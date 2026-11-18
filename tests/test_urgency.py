import pytest

from app.urgency import compute_urgency


@pytest.mark.parametrize(
    "message",
    [
        "Sparks coming from the board",
        "BURNING smell from AC",
        "water is flooding the floor",
        "There is a Gas   Leak in the kitchen",
        "Switch board lo current kottindi",
        "స్విచ్ బోర్డ్ నుండి పొగ వస్తోంది",
        "Short circuit happened",
    ],
)
def test_safety_keywords_force_high_even_if_model_says_false(message):
    assert compute_urgency(message, "other", safety_risk=False) == "high"


def test_model_safety_flag_forces_high():
    assert compute_urgency("my fan is noisy", "book_service", safety_risk=True) == "high"


@pytest.mark.parametrize("intent", ["price_enquiry", "cancel", "other"])
def test_low_intents(intent):
    assert compute_urgency("hello there", intent, safety_risk=False) == "low"


@pytest.mark.parametrize("intent", ["book_service", "reschedule", "complaint", "status_check"])
def test_normal_intents(intent):
    assert compute_urgency("hello there", intent, safety_risk=False) == "normal"


def test_safety_beats_low_intent():
    assert compute_urgency("cancel it, there is smoke", "cancel", safety_risk=False) == "high"
