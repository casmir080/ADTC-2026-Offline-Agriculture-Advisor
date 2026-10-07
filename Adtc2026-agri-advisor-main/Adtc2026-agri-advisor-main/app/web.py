"""Web UI for the ADTC 2026 agriculture advisor. Run: python -m app.web"""

from flask import Flask, request, render_template_string
import requests

from app import config, risk_model, llm, yoruba_menu
from app.rag import LocalRetriever

app = Flask(__name__)
_retriever = LocalRetriever()

RISK_COLORS = {"high": "#c0392b", "medium": "#d68910", "low": "#1e8449"}

BASE_STYLE = """
<style>
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif;
         background:#f4f6f2; color:#222; max-width:720px; margin:32px auto; padding:0 16px; }
  h1 { font-size:1.4rem; color:#234d20; }
  .tag { display:inline-block; background:#e3eedd; color:#234d20; font-size:0.75rem;
         padding:2px 8px; border-radius:10px; margin-bottom:14px; }
  textarea, select { width:100%; padding:10px; font-size:1rem;
         border:1px solid #ccc; border-radius:6px; box-sizing:border-box; margin-bottom:10px; }
  button { background:#234d20; color:white; border:none; padding:10px 18px;
           border-radius:6px; font-size:1rem; cursor:pointer; }
  button:hover { background:#163814; }
  .card { background:white; border:1px solid #e0e0e0; border-radius:10px; padding:18px; margin-top:18px; }
  .badge { display:inline-block; padding:4px 10px; border-radius:6px; color:white; font-weight:600; font-size:0.85rem; }
  .warn { background:#fdf3d8; border:1px solid #e8c468; border-radius:8px; padding:10px 14px; margin-top:14px; font-size:0.92rem; }
  .src { font-size:0.8rem; color:#777; margin-top:10px; }
  .perf { font-size:0.78rem; color:#999; margin-top:8px; }
  a { color:#234d20; }
  .yo-list a { display:block; padding:8px 0; border-bottom:1px solid #eee; }
</style>
"""

INDEX_PAGE = """
<!doctype html>
<html><head><title>ADTC Agriculture Advisor</title>""" + BASE_STYLE + """</head>
<body>
  <span class="tag">Offline &middot; runs on-device &middot; no cloud</span>
  <h1>&#127806; Agriculture Advisor</h1>
  <p style="color:#555; font-size:0.92rem;">Describe a symptom in maize, cassava, or beans. <em>Responses can take 30-90s on this dev machine; the target ADTC hardware is faster.</em></p>
  <form method="POST" action="/ask" onsubmit="document.getElementById('btn').innerText='Thinking... please wait, do NOT refresh or close this tab (up to 90s on this hardware)'; document.getElementById('btn').disabled=true;">
    <textarea name="question" rows="3" placeholder="e.g. there are window pane marks and frass on my young maize leaves" required>{{ question or '' }}</textarea>
    <select name="season">
      <option value="" {% if season=='' %}selected{% endif %}>Season unknown / skip risk check</option>
      <option value="dry" {% if season=='dry' %}selected{% endif %}>Dry season</option>
      <option value="rainy" {% if season=='rainy' %}selected{% endif %}>Rainy season</option>
    </select>
    <button id="btn" type="submit">Ask</button>
  </form>
  <p style="margin-top:18px;"><a href="/yoruba">&#127472;&#127466; Yoruba mode &rarr;</a></p>
  {% if result %}
  <div class="card">
    <strong>Q:</strong> {{ result.question }}
    {% if result.low_confidence %}
    <div class="warn">&#9888; Low-confidence match against the local knowledge base. Consider consulting a local agricultural extension officer.</div>
    {% endif %}
    {% if result.risk %}
    <p style="margin-top:14px;">
      <span class="badge" style="background:{{ result.risk_color }}">{{ result.risk.level|upper }} RISK</span>
      &nbsp;<span style="color:#555; font-size:0.88rem;">{{ result.risk.rationale }}</span>
    </p>
    {% endif %}
    <p style="margin-top:14px; white-space:pre-wrap;">{{ result.answer }}</p>
    <div class="src">Top sources: {% for c in result.chunks %}{{ c.source }} (score {{ "%.3f"|format(c.score) }}){% if not loop.last %}, {% endif %}{% endfor %}</div>
    <div class="perf">{{ result.perf.eval_count }} tokens in {{ "%.1f"|format(result.perf.eval_duration_s) }}s &rarr; {{ "%.1f"|format(result.perf.tps) }} tok/s</div>
  </div>
  {% endif %}
</body></html>
"""

YORUBA_PAGE = """
<!doctype html>
<html><head><title>Yoruba Mode</title>""" + BASE_STYLE + """</head>
<body>
  <span class="tag">&#127472;&#127466; Local language mode</span>
  <h1>Yor&ugrave;b&aacute;</h1>
  <p style="color:#555; font-size:0.85rem;">Fixed, pre-written answers &mdash; avoids open-ended Yoruba generation entirely.</p>
  <div class="card yo-list">
    {% for item in menu %}
    <a href="/yoruba/{{ loop.index0 }}">{{ item.label_yo }} <span style="color:#999;">({{ item.label_en }})</span></a>
    {% endfor %}
  </div>
  <p style="margin-top:14px;"><a href="/">&larr; Back to English mode</a></p>
  {% if answer %}<div class="card">{{ answer }}</div>{% endif %}
</body></html>
"""


@app.route("/", methods=["GET"])
def index():
    return render_template_string(INDEX_PAGE, result=None, question="", season="")


@app.route("/ask", methods=["POST"])
def ask():
    question = request.form.get("question", "").strip()
    season = request.form.get("season", "").strip()
    context = _retriever.retrieve(question)
    low_confidence = _retriever.is_low_confidence(context)

    risk_info = None
    risk_color = None
    if context:
        topic = risk_model.identify_topic(context[0]["text"])
        if topic and season:
            result = risk_model.assess_risk(topic, season)
            if result:
                level, rationale = result
                risk_info = {"topic": topic, "level": level, "rationale": rationale}
                risk_color = RISK_COLORS.get(level, "#777")

    risk_line = f"{risk_info['level'].upper()} risk - {risk_info['rationale']}" if risk_info else None
    prompt = llm.build_prompt(question, context, risk_line)
    try:
        gen = llm.generate(prompt)
    except requests.exceptions.ConnectionError:
        gen = {"text": "[Error] Can't reach the local model server. Check Ollama is running and OLLAMA_HOST in app/config.py.",
               "eval_count": 0, "eval_duration_s": 0, "tps": 0, "roundtrip_s": 0}

    result = {"question": question, "chunks": context, "low_confidence": low_confidence,
              "risk": risk_info, "risk_color": risk_color, "answer": gen["text"], "perf": gen}
    return render_template_string(INDEX_PAGE, result=result, question=question, season=season)


@app.route("/yoruba", methods=["GET"])
def yoruba():
    return render_template_string(YORUBA_PAGE, menu=yoruba_menu.MENU, answer=None)


@app.route("/yoruba/<int:idx>", methods=["GET"])
def yoruba_answer(idx):
    answer = yoruba_menu.MENU[idx]["answer_yo"] if 0 <= idx < len(yoruba_menu.MENU) else None
    return render_template_string(YORUBA_PAGE, menu=yoruba_menu.MENU, answer=answer)


if __name__ == "__main__":
    print(f"[boot] domain={config.DOMAIN} model={config.MODEL_NAME}")
    print("[boot] open http://localhost:5000 in a browser")
    app.run(host="0.0.0.0", port=5000, debug=False)
