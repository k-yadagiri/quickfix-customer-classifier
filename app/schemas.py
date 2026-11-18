"""Request / response shapes for the API."""
from typing import Literal
from typing_extensions import Annotated

from pydantic import BaseModel, StringConstraints

Intent = Literal["book_service", "reschedule", "cancel", "complaint", "price_enquiry", "status_check", "other"]
Category = Literal[
    "plumbing", "electrical", "ac_repair", "appliance_repair",
    "cleaning", "pest_control", "carpentry", "painting", "none",
]
Urgency = Literal["high", "normal", "low"]


class ClassifyRequest(BaseModel):
    # Whitespace is stripped first, so "   " is rejected as empty (422). Max 1000 chars.
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class ClassifyResponse(BaseModel):
    id: int
    message: str
    intent: Intent
    category: Category
    urgency: Urgency
    safety_risk: bool
    summary: str
    needs_review: bool
    model: str
    response_ms: int
    invalid_attempts: int  # extra field: invalid model answers before the final result (used by eval.py)
