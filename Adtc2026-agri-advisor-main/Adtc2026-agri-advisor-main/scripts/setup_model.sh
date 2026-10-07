#!/usr/bin/env bash
# Pulls the model defined in app/config.py (or override with ADTC_MODEL).
set -e

MODEL="${ADTC_MODEL:-gemma3:4b}"

echo "==> Pulling $MODEL via Ollama (this happens once, then it's cached locally)"
ollama pull "$MODEL"

echo "==> Done. Quick sanity check:"
ollama run "$MODEL" "Reply with one short sentence confirming you're running locally." --verbose=false || true
