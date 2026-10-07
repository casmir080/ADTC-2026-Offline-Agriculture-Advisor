"""
ADTC 2026 submission entry point.
Combines: local RAG (retrieval) + rule-based risk engine (classical) +
local LLM (generation/explanation) + Yoruba menu mode (localization).
"""

import time

import requests

from app import config, yoruba_menu, risk_model
from app.rag import LocalRetriever

SYSTEM_PROMPT = (
    "You are a helpful, concise on-device assistant. "
    "Use the provided context if it's relevant. If the context doesn't "
    "answer the question, say so plainly instead of guessing. "
    "If a risk assessment is provided, incorporate its urgency level "
    "naturally into your answer."
)


def build_prompt(question: str, context_chunks: list[dict], risk_line: str = None) -> str:
    if not context_chunks:
        context_block = "(no relevant local context found)"
    else:
        context_block = "\n\n".join(
            f"[Source: {c['source']}]\n{c['text']}" for c in context_chunks
        )
    risk_block = f"\n\nRisk assessment: {risk_line}" if risk_line else ""
    return (
        f"Context:\n{context_block}{risk_block}\n\n"
        f"Question: {question}\n\n"
        f"Answer using the context where relevant:"
    )


def generate(prompt: str):
    url = f"{config.OLLAMA_HOST}/api/generate"
    payload = {
        "model": config.MODEL_NAME,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": config.TEMPERATURE,
            "num_predict": config.MAX_RESPONSE_TOKENS,
            "num_ctx": 2048,
        },
    }
    start = time.time()
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    elapsed = max(time.time() - start, 1e-6)

    text = data.get("response", "")
    eval_count = data.get("eval_count", 0)
    eval_duration_s = data.get("eval_duration", 0) / 1e9
    tps = eval_count / eval_duration_s if eval_duration_s > 0 else 0

    print(text)
    print(f"\n[perf] {eval_count} tokens, {eval_duration_s:.1f}s -> {tps:.1f} tok/s "
          f"(roundtrip {elapsed:.1f}s)")
    return text


def yoruba_mode():
    while True:
        yoruba_menu.print_menu()
        choice = input("\nyàn nọ́mbà (choose number)> ").strip()
        answer = yoruba_menu.get_answer(choice)
        if answer == "BACK":
            return
        if answer is None:
            print("Yàn nọ́mbà tí ó tọ́ (pick a valid number).")
            continue
        print(f"\n{answer}\n")


def main():
    print(f"[boot] domain={config.DOMAIN}  model={config.MODEL_NAME}")
    retriever = LocalRetriever()
    print("\nADTC local assistant ready.")
    print("Type 'exit' to quit, or '/yo' for Yoruba menu mode.\n")

    while True:
        question = input("you> ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if question.lower() == "/yo":
            yoruba_mode()
            continue
        if not question:
            continue

        context = retriever.retrieve(question)

        print(f"[debug] retrieved {len(context)} chunk(s)")
        for c in context:
            print(f"[debug]   score={c['score']:.3f}  source={c['source']}")

        # --- hybrid risk engine ---
        risk_line = None
        if context:
            topic = risk_model.identify_topic(context[0]["text"])
            if topic:
                season = input(
                    f"[risk-engine] detected topic: '{topic}'. "
                    f"Is it currently rainy or dry season? (rainy/dry)> "
                ).strip()
                result = risk_model.assess_risk(topic, season)
                if result:
                    level, rationale = result
                    risk_line = f"{level.upper()} risk - {rationale}"
                    print(f"[risk-engine] {risk_line}")
        # --- end hybrid risk engine ---

        prompt = build_prompt(question, context, risk_line)
        print("assistant> ", end="", flush=True)
        try:
            generate(prompt)
        except requests.exceptions.ConnectionError:
            print("\n[error] Can't reach Ollama. Check OLLAMA_HOST in app/config.py")


if __name__ == "__main__":
    main()
