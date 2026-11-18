
"""LLM classification, output validation, retry, and safe fallback."""

import json
import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional

import httpx

from app import config
from app.labels import CATEGORIES, INTENTS
from app.prompt import SYSTEM_PROMPT, build_user_prompt
from app.urgency import compute_urgency

log = logging.getLogger("quickfix.classifier")

MAX_ATTEMPTS = 2
MAX_SUMMARY_CHARS = 300

FALLBACK_SUMMARY = (
    "Could not be classified automatically; needs manual review."
)


class LLMUnavailable(Exception):
    """Raised when the model server cannot be reached or times out."""


class InvalidModelOutput(Exception):
    """Raised when the model returns invalid JSON or unsupported labels."""


@dataclass
class Classification:
    intent: str
    category: str
    urgency: str
    safety_risk: bool
    summary: str
    needs_review: bool
    invalid_attempts: int
    response_ms: int


def call_llm(message: str, retry_hint: Optional[str] = None) -> str:
    """Call the OpenAI-compatible Ollama endpoint."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(message)},
    ]

    if retry_hint:
        messages.append({
            "role": "user",
            "content": (
                f"Your previous response was invalid: {retry_hint}. "
                "Return only one valid JSON object using the required labels."
            ),
        })

    payload = {
        "model": config.LLM_MODEL,
        "messages": messages,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}"
    }

    url = f"{config.LLM_BASE_URL.rstrip('/')}/chat/completions"

    try:
        response = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=config.LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

    except httpx.TimeoutException as exc:
        raise LLMUnavailable(
            f"Model request timed out after "
            f"{config.LLM_TIMEOUT_SECONDS} seconds."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise LLMUnavailable(
            f"Model server returned HTTP {exc.response.status_code}: "
            f"{exc.response.text[:200]}"
        ) from exc

    except httpx.HTTPError as exc:
        raise LLMUnavailable(
            f"Cannot connect to Ollama at {config.LLM_BASE_URL}. "
            "Check whether Ollama is running."
        ) from exc

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"] or ""

    except (ValueError, KeyError, IndexError, TypeError):
        return ""


def parse_and_validate(raw: str) -> dict:
    """Parse model JSON and validate the required fields and labels."""

    text = (raw or "").strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end <= start:
        raise InvalidModelOutput("Response does not contain JSON.")

    try:
        data = json.loads(text[start:end + 1])
    except ValueError as exc:
        raise InvalidModelOutput("Response is not valid JSON.") from exc

    if not isinstance(data, dict):
        raise InvalidModelOutput("JSON response must be an object.")

    intent = str(data.get("intent", "")).strip().lower()
    category = str(data.get("category", "")).strip().lower()

    if intent not in INTENTS:
        raise InvalidModelOutput(
            f"Unsupported intent: {intent}"
        )

    if category not in CATEGORIES:
        raise InvalidModelOutput(
            f"Unsupported category: {category}"
        )

    safety = data.get("safety_risk")

    if isinstance(safety, str):
        value = safety.strip().lower()

        if value == "true":
            safety = True
        elif value == "false":
            safety = False

    if not isinstance(safety, bool):
        raise InvalidModelOutput(
            "safety_risk must be a JSON boolean."
        )

    # Enforce the assignment rule in Python.
    if intent == "other":
        category = "none"

    summary = data.get("summary")

    if isinstance(summary, str):
        summary = summary.strip()[:MAX_SUMMARY_CHARS]
    else:
        summary = ""

    if not summary:
        summary = "No summary provided by the model."

    return {
        "intent": intent,
        "category": category,
        "safety_risk": safety,
        "summary": summary,
    }


def classify_message(
    message: str,
    llm: Optional[Callable[..., str]] = None,
) -> Classification:
    """Classify a message, retry once on invalid output, then fall back."""

    llm = llm or call_llm

    started = time.perf_counter()
    invalid_attempts = 0
    retry_hint = None
    result = None
    needs_review = False

    for attempt in range(1, MAX_ATTEMPTS + 1):
        raw = llm(message, retry_hint=retry_hint)

        try:
            result = parse_and_validate(raw)
            break

        except InvalidModelOutput as exc:
            invalid_attempts += 1
            retry_hint = str(exc)

            log.warning(
                "Invalid model output (%d/%d): %s",
                attempt,
                MAX_ATTEMPTS,
                exc,
            )

    if result is None:
        result = {
            "intent": "other",
            "category": "none",
            "safety_risk": False,
            "summary": FALLBACK_SUMMARY,
        }
        needs_review = True

    # Urgency is calculated by Python, not by the LLM.
    urgency = compute_urgency(
        message,
        result["intent"],
        result["safety_risk"],
    )

    response_ms = int(
        (time.perf_counter() - started) * 1000
    )

    return Classification(
        intent=result["intent"],
        category=result["category"],
        urgency=urgency,
        safety_risk=result["safety_risk"],
        summary=result["summary"],
        needs_review=needs_review,
        invalid_attempts=invalid_attempts,
        response_ms=response_ms,
    )
