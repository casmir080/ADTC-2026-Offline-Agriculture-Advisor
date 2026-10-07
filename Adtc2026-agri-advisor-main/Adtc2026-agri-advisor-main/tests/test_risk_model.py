"""
Confirms risk_model works across ALL topics, not just the one we
happened to test manually through the LLM. Run with: pytest -v
"""

import pytest

from app import risk_model
from app.rag import LocalRetriever


SAMPLE_CHUNKS = {
    "fall armyworm": "Fall armyworm is one of the most damaging maize pests",
    "maize streak virus": "Maize streak virus, transmitted by leafhoppers, causes narrow yellow streaks",
    "nitrogen deficiency": "Nitrogen deficiency in maize shows first as yellowing",
    "cassava mosaic": "Cassava mosaic disease (CMD) is the most widespread viral disease",
    "cassava brown streak": "Cassava brown streak disease is a separate but equally serious viral disease",
    "anthracnose": "Anthracnose, caused by Colletotrichum lindemuthianum, shows as dark sunken lesions",
    "angular leaf spot": "Angular leaf spot, caused by the fungus Pseudocercospora griseola",
    "bean rust": "Bean rust, caused by Uromyces appendiculatus, produces small reddish-brown pustules",
}


@pytest.mark.parametrize("expected_topic,sample_text", SAMPLE_CHUNKS.items())
def test_identify_topic(expected_topic, sample_text):
    detected = risk_model.identify_topic(sample_text)
    assert detected == expected_topic, (
        f"Expected '{expected_topic}' but got '{detected}' for text: {sample_text!r}"
    )


@pytest.mark.parametrize("topic", SAMPLE_CHUNKS.keys())
@pytest.mark.parametrize("season", ["dry", "rainy"])
def test_assess_risk_returns_valid_result(topic, season):
    result = risk_model.assess_risk(topic, season)
    assert result is not None, f"No rule found for topic={topic} season={season}"
    level, rationale = result
    assert level in ("low", "medium", "high")
    assert len(rationale) > 10


def test_unknown_topic_returns_none():
    assert risk_model.identify_topic("something about weather forecasts") is None


def test_real_corpus_chunks_all_resolve_to_a_topic_or_none_gracefully():
    retriever = LocalRetriever()
    for chunk in retriever.chunks:
        risk_model.identify_topic(chunk)
