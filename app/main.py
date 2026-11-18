"""FastAPI app: /classify, /messages, /stats, /health."""
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query

from app import config, db
from app.classifier import LLMUnavailable, classify_message
from app.schemas import Category, ClassifyRequest, ClassifyResponse, Intent, Urgency

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("quickfix.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="QuickFix Customer Message Classifier", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "model": config.LLM_MODEL}


# Plain `def` (not async): FastAPI runs it in a worker thread, so the slow
# blocking model call does not freeze the server.
@app.post("/classify", response_model=ClassifyResponse)
def classify(request: ClassifyRequest):
    try:
        result = classify_message(request.message)
    except LLMUnavailable as exc:
        log.error("LLM unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=f"Language model unavailable: {exc}")

    new_id = db.save_message(request.message, result, config.LLM_MODEL)
    return ClassifyResponse(
        id=new_id,
        message=request.message,
        intent=result.intent,
        category=result.category,
        urgency=result.urgency,
        safety_risk=result.safety_risk,
        summary=result.summary,
        needs_review=result.needs_review,
        model=config.LLM_MODEL,
        response_ms=result.response_ms,
        invalid_attempts=result.invalid_attempts,
    )


@app.get("/messages")
def get_messages(
    intent: Optional[Intent] = None,
    category: Optional[Category] = None,
    urgency: Optional[Urgency] = None,
    needs_review: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> List[dict]:
    return db.list_messages(intent, category, urgency, needs_review, limit, offset)


@app.get("/stats")
def get_stats():
    return db.get_stats()
