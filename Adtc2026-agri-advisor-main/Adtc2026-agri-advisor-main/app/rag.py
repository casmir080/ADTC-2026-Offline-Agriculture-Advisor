"""
Minimal local RAG over a folder of text/markdown files.
"""

import glob
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app import config


def _chunk_text(text: str, size: int, overlap: int):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


class LocalRetriever:
    def __init__(self, corpus_dir: str = None):
        self.corpus_dir = corpus_dir or config.CORPUS_DIR
        self.chunks: list[str] = []
        self.sources: list[str] = []
        self.vectorizer = None
        self.matrix = None
        self._build_index()

    def _build_index(self):
        paths = sorted(
            glob.glob(os.path.join(self.corpus_dir, "**", "*.md"), recursive=True)
            + glob.glob(os.path.join(self.corpus_dir, "**", "*.txt"), recursive=True)
        )
        for path in paths:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            for chunk in _chunk_text(text, config.CHUNK_SIZE_CHARS, config.CHUNK_OVERLAP_CHARS):
                if chunk.strip():
                    self.chunks.append(chunk)
                    self.sources.append(os.path.basename(path))

        if not self.chunks:
            print(f"[rag] WARNING: no documents found in '{self.corpus_dir}'.")
            return

        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.chunks)
        print(f"[rag] Indexed {len(self.chunks)} chunks from {len(paths)} file(s).")

    def retrieve(self, query: str, top_k: int = None):
        top_k = top_k or config.TOP_K
        if not self.chunks or self.vectorizer is None:
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix)[0]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked[:top_k]:
            if scores[i] > 0:
                results.append({"text": self.chunks[i], "source": self.sources[i], "score": float(scores[i])})
        return results

    def is_low_confidence(self, results, threshold: float = None) -> bool:
        threshold = threshold if threshold is not None else config.CONFIDENCE_THRESHOLD
        if not results:
            return True
        return results[0]["score"] < threshold
