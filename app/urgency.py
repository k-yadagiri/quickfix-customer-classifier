"""Urgency is decided here, in plain Python. The model never sets it."""
from app.labels import LOW_URGENCY_INTENTS, SAFETY_KEYWORDS


def has_safety_keyword(message: str) -> bool:
    # Collapse whitespace so "gas   leak" still matches "gas leak".
    text = " ".join(message.lower().split())
    return any(word in text for word in SAFETY_KEYWORDS)


def compute_urgency(message: str, intent: str, safety_risk: bool) -> str:
    # 1. Safety: model flag OR keyword in the message.
    if safety_risk or has_safety_keyword(message):
        return "high"
    # 2. Low-priority intents.
    if intent in LOW_URGENCY_INTENTS:
        return "low"
    # 3. Everything else.
    return "normal"
