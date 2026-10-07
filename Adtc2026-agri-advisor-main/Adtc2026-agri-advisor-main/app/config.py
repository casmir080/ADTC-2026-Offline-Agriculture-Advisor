"""
Central configuration for the ADTC 2026 submission.
"""

import os

# --- Domain ---
DOMAIN = "agriculture"

# --- Model ---
MODEL_NAME = os.environ.get("ADTC_MODEL", "llama3.2:3b")

# Ollama runs on Windows; WSL reaches it via the Windows host IP.
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://172.19.192.1:11434")

# --- Hardware budget (mirrors the ADTC Standard Laptop) ---
MAX_RAM_GB = 7.0
MEMORY_WARN_THRESHOLD_GB = 6.0

# --- RAG ---
CORPUS_DIR = "data/corpus"
TOP_K = 2
CHUNK_SIZE_CHARS = 800
CHUNK_OVERLAP_CHARS = 100

# --- Generation ---
# Lowered for faster dev-loop testing on older hardware.
# The real ADTC audit hardware (10th-12th gen CPU) won't need this crutch,
# but raise it back toward 256 before final benchmarking/submission.
MAX_RESPONSE_TOKENS = 256
TEMPERATURE = 0.3
STREAM = True

# --- Retrieval confidence ---
# Below this TF-IDF score, the top match is too weak to trust -
# surface a warning instead of letting the LLM answer unhedged.
CONFIDENCE_THRESHOLD = 0.15

# --- Retrieval confidence ---
# Below this TF-IDF score, the top match is too weak to trust -
# surface a warning instead of letting the LLM answer unhedged.
CONFIDENCE_THRESHOLD = 0.15

# --- Retrieval confidence ---
# Below this TF-IDF score, the top match is too weak to trust -
# surface a warning instead of letting the LLM answer unhedged.
CONFIDENCE_THRESHOLD = 0.15
