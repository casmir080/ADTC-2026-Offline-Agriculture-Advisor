"""
Rule-based agronomic risk engine.

This is the "classical model" half of the cross-disciplinary integration
required by the contest brief: a deterministic, explainable rule system
grounded in real pest/disease epidemiology, sitting alongside the LLM
rather than replacing it. The LLM explains and contextualizes; this
engine supplies the actual risk judgment, which is something an LLM
should not be trusted to invent on the fly.

Rules are grounded in well-documented vector/pathogen behavior:
  - Fungal diseases spread faster in humid/rainy conditions (moisture
    is required for spore germination and splash dispersal).
  - Whitefly- and leafhopper-transmitted viruses spread faster when
    vector insect populations are high, which tends to happen in
    warm, dry conditions.
  - Nutrient issues aren't "spreading" risks, but season still matters:
    heavy rain increases nitrogen leaching risk.
"""

TOPIC_KEYWORDS = {
    "fall armyworm": ["fall armyworm", "frass", "window-pane"],
    "maize streak virus": ["maize streak virus", "leafhoppers"],
    "nitrogen deficiency": ["nitrogen deficiency"],
    "cassava mosaic": ["cassava mosaic", "cmd"],
    "cassava brown streak": ["brown streak"],
    "anthracnose": ["anthracnose"],
    "angular leaf spot": ["angular leaf spot"],
    "bean rust": ["bean rust", "uromyces"],
}

RISK_RULES = {
    "fall armyworm": {
        "type": "pest",
        "dry": ("high", "Warm, dry conditions favor fall armyworm moth activity and egg-laying; check plants every 2-3 days."),
        "rainy": ("medium", "Rain can wash some young larvae off leaves, but established infestations still need monitoring."),
    },
    "maize streak virus": {
        "type": "viral_leafhopper",
        "dry": ("high", "Leafhopper populations build up faster in warm, dry conditions, increasing transmission risk."),
        "rainy": ("medium", "Vector activity is somewhat reduced, but infected volunteer plants can still carry the virus between seasons."),
    },
    "nitrogen deficiency": {
        "type": "nutrient",
        "dry": ("medium", "Drought stress can compound visible deficiency symptoms even if some nitrogen is present in soil."),
        "rainy": ("high", "Heavy rainfall increases nitrogen leaching from soil; symptoms often worsen after sustained heavy rain."),
    },
    "cassava mosaic": {
        "type": "viral_whitefly",
        "dry": ("high", "Whitefly populations typically increase in hot, dry conditions, raising spread risk between plants."),
        "rainy": ("medium", "Whitefly numbers are usually somewhat reduced, but infected cuttings remain a transmission risk regardless of season."),
    },
    "cassava brown streak": {
        "type": "viral_whitefly",
        "dry": ("high", "Same whitefly-driven spread pattern as cassava mosaic disease; root damage may not be visible until harvest."),
        "rainy": ("medium", "Lower vector activity than dry season, but cutting-borne spread is unaffected by season."),
    },
    "anthracnose": {
        "type": "fungal",
        "dry": ("low", "Fungal spread requires moisture; dry conditions slow new infection significantly."),
        "rainy": ("high", "Rain splash spreads spores between plants rapidly; risk rises sharply in sustained wet weather."),
    },
    "angular leaf spot": {
        "type": "fungal",
        "dry": ("low", "Low humidity slows spore germination and spread."),
        "rainy": ("high", "High humidity and leaf wetness strongly favor this fungus; risk increases with consecutive rainy days."),
    },
    "bean rust": {
        "type": "fungal",
        "dry": ("low", "Spores need moisture on the leaf surface to germinate; dry weather limits new infections."),
        "rainy": ("high", "Moderate temperatures with high humidity are ideal for rust spread."),
    },
}


def identify_topic(chunk_text: str):
    text_lower = chunk_text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return topic
    return None


def assess_risk(topic: str, season: str):
    """season should be 'dry' or 'rainy'. Returns (risk_level, rationale) or None."""
    season = season.strip().lower()
    if season not in ("dry", "rainy"):
        return None
    rule = RISK_RULES.get(topic)
    if not rule:
        return None
    return rule[season]
