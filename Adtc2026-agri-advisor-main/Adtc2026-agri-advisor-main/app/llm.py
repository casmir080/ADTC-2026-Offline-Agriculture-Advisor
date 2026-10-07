"""Shared prompt-building and generation logic for CLI and web UI."""

import time
import requests
from app import config

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
        context_block = "\n\n".join(f"[Source: {c['source']}]\n{c['text']}" for c in context_chunks)
    risk_block = f"\n\nRisk assessment: {risk_line}" if risk_line else ""
    return f"Context:\n{context_block}{risk_block}\n\nQuestion: {question}\n\nAnswer using the context where relevant:"


def generate(prompt: str) -> dict:
    url = f"{config.OLLAMA_HOST}/api/generate"
    payload = {
        "model": config.MODEL_NAME,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {"temperature": config.TEMPERATURE, "num_predict": config.MAX_RESPONSE_TOKENS, "num_ctx": 2048},
    }
    start = time.time()
    resp = requests.post(url, json=payload, timeout=600)
    resp.raise_for_status()
    data = resp.json()
    elapsed = max(time.time() - start, 1e-6)
    eval_count = data.get("eval_count", 0)
    eval_duration_s = data.get("eval_duration", 0) / 1e9
    tps = eval_count / eval_duration_s if eval_duration_s > 0 else 0
    return {"text": data.get("response", ""), "eval_count": eval_count, "eval_duration_s": eval_duration_s, "tps": tps, "roundtrip_s": elapsed}
