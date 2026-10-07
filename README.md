# ADTC-2026-Offline-Agriculture-Advisor
An offline, on-device AI advisor for smallholder farmers across Sub-Saharan Africa, built for the Africa Deep Tech Challenge 2026 ("Laptop LLM Challenge"). Runs entirely on a standard 8GB laptop with no cloud dependency, no GPU, and no internet connection at inference time.

Covers three staple crops — maize, cassava, and common bean — diagnosing common pest, disease, and nutrient issues from a plain description of symptoms.

What makes this more than an LLM wrapper
Local RAG over a hand-built agricultural knowledge base (no cloud vector DB, no external API calls)
A rule-based agronomic risk engine (app/risk_model.py) that computes pest/disease risk from real epidemiological patterns (e.g. fungal disease favored by humidity, whitefly/leafhopper vectors favored by dry heat) — independent of the LLM, which is then instructed to incorporate that computed risk rather than inventing its own urgency framing. This is the project's cross-disciplinary integration.
A Yoruba-language menu mode (app/yoruba_menu.py) for farmers who prefer a local language — built as a fixed-answer menu rather than free-form generation, after testing showed the base model cannot reliably understand or generate Yoruba.
Requirements
Python 3.11+
Ollama installed and running
~3GB free disk space for the model
Setup
git clone <this-repo-url>
cd adtc2026-agri-advisor

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

ollama pull llama3.2:3b
ollama serve   # if not already running as a background service
By default, app/config.py points to http://172.19.192.1:11434 — a holdover from this project's own development setup, where Ollama ran on Windows while the app ran in WSL. On a normal single-OS Ubuntu 22.04 machine (the actual ADTC target environment), change this back to:

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

[Running](https://github.com/casmir080/Adtc2026-agri-advisor#running)
python -m app.main
Ask a question naturally, e.g.: you> there are window pane marks and frass on my young maize leaves

When prompted, enter the current season (dry or rainy) to trigger the risk engine.

Type /yo at any time for the Yoruba menu mode, or exit to quit.

[Running the web UI](https://github.com/casmir080/Adtc2026-agri-advisor#running-the-web-ui)
python -m app.web
```

Open http://localhost:5000 (or the WSL host IP printed in the terminal
if localhost does not resolve in your setup) in a browser. Includes a
color-coded risk badge, a low-confidence warning, and the same Yoruba
menu mode as the CLI.

## Testing

```bash
pytest -v
```
28 tests covering RAG retrieval accuracy and full risk-engine coverage
across all 8 corpus topics × 2 seasons.

## Profiling / benchmarking

```bash
python scripts/memory_watchdog.py &     # background RAM logger
/usr/bin/time -v python -m app.main     # peak RSS on exit
bash scripts/profile_run.sh             # wraps both together
```

See `REPORT.md` for actual measured benchmarks, design decisions, and
known limitations.

## Project layout
app/

config.py         model/host/domain settings

main.py            entry point: RAG + risk engine + generation loop

rag.py             local TF-IDF retrieval over data/corpus/

risk_model.py      rule-based agronomic risk engine

yoruba_menu.py     fixed-answer Yoruba localization mode

data/corpus/         agricultural knowledge base (maize/cassava/bean)

scripts/             model setup, memory watchdog, profiling helpers

tests/               pytest suite (RAG + risk engine coverage)

REPORT.md            full design rationale, benchmarks, limitations

## Known limitations

See `REPORT.md` § Known Limitations — most notably, Yoruba content is
a first draft pending native-speaker review, and retrieval is
TF-IDF/keyword-based rather than semantic.
