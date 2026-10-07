#!/usr/bin/env python3
"""
Run this alongside your app during development:

    python scripts/memory_watchdog.py &
    python -m app.main

It polls total system + per-process memory every second, logs to
logs/memory_log.csv, and prints a warning if usage crosses
config.MEMORY_WARN_THRESHOLD_GB. This is your early-warning system —
catch creeping memory growth here, days before the official audit does.
"""

import csv
import os
import sys
import time

import psutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import config  # noqa: E402

LOG_PATH = "logs/memory_log.csv"
POLL_SECONDS = 1.0


def get_relevant_process_rss_gb():
    """Sums RSS across python and ollama processes (the actual app footprint)."""
    total_bytes = 0
    for proc in psutil.process_iter(["name", "memory_info"]):
        try:
            name = (proc.info["name"] or "").lower()
            if "python" in name or "ollama" in name:
                total_bytes += proc.info["memory_info"].rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return total_bytes / (1024 ** 3)


def main():
    os.makedirs("logs", exist_ok=True)
    new_file = not os.path.exists(LOG_PATH)

    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["timestamp", "rss_gb", "pct_of_7gb_budget"])

        print(f"[watchdog] logging to {LOG_PATH}. Ctrl+C to stop.")
        try:
            while True:
                rss_gb = get_relevant_process_rss_gb()
                pct = (rss_gb / config.MAX_RAM_GB) * 100
                writer.writerow([time.time(), round(rss_gb, 3), round(pct, 1)])
                f.flush()

                if rss_gb > config.MEMORY_WARN_THRESHOLD_GB:
                    print(
                        f"[watchdog] \u26a0\ufe0f  {rss_gb:.2f} GB used "
                        f"({pct:.0f}% of {config.MAX_RAM_GB} GB budget)"
                    )
                time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            print("\n[watchdog] stopped.")


if __name__ == "__main__":
    main()
