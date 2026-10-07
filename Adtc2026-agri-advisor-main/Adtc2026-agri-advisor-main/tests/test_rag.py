"""
Minimal tests for the RAG retriever. Run with: pytest

These don't touch the model at all — they're here so you can verify
your retrieval logic in isolation, fast, without spinning up Ollama.
"""

import os
import tempfile

from app.rag import LocalRetriever


def test_retrieve_finds_relevant_chunk():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "doc.md")
        with open(path, "w") as f:
            f.write(
                "Tomato blight causes dark spots on leaves and stems. "
                "Remove affected leaves promptly.\n\n"
                "Irrigation scheduling depends on local rainfall patterns."
            )

        retriever = LocalRetriever(corpus_dir=tmp)
        results = retriever.retrieve("how do I treat tomato blight", top_k=1)

        assert len(results) == 1
        assert "blight" in results[0]["text"].lower()


def test_retrieve_empty_corpus_returns_empty():
    with tempfile.TemporaryDirectory() as tmp:
        retriever = LocalRetriever(corpus_dir=tmp)
        results = retriever.retrieve("anything")
        assert results == []
