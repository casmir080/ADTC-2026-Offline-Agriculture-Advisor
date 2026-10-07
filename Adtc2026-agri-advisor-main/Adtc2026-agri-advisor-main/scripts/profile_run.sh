#!/usr/bin/env bash
# Runs the app under `time -v` to capture peak RSS, plus your own
# memory_watchdog log, so you get an early read on the Speed (Sperf)
# and Efficiency (Seff) scores before the official ADTC audit.
set -e

mkdir -p logs
TS=$(date +%Y%m%d_%H%M%S)
OUT="logs/profile_${TS}.log"

echo "==> Profiling run started. Output: $OUT"
echo "==> Also drop the ADTC profiler tool output in here once you have it."

if command -v /usr/bin/time >/dev/null 2>&1; then
    /usr/bin/time -v python -m app.main 2>&1 | tee "$OUT"
else
    echo "(GNU time not found, running without peak-RSS capture)"
    python -m app.main 2>&1 | tee "$OUT"
fi

echo ""
echo "==> Look for 'Maximum resident set size' in $OUT for peak RAM (KB)."
echo "==> Compare token throughput against your logged [perf] lines."
