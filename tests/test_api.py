import json

import pytest
from fastapi.testclient import TestClient

from app import classifier, config, db
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as c:  # runs startup -> creates the table
        yield c


def fake_llm(intent="book_service", category="electrical", safety=False):
    raw = json.dumps({"intent": intent, "category": category, "safety_risk": safety, "summary": "s"})
    return lambda message, retry_hint=None: raw


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "model": config.LLM_MODEL}


def test_classify_saves_and_returns(client, monkeypatch):
    monkeypatch.setattr(classifier, "call_llm", fake_llm(safety=True))
    r = client.post("/classify", json={"message": "Switch board lo current kottindi"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 1 and body["urgency"] == "high" and body["safety_risk"] is True
    assert body["model"] == config.LLM_MODEL and body["needs_review"] is False
    assert len(client.get("/messages").json()) == 1


@pytest.mark.parametrize("payload", [{"message": ""}, {"message": "   "}, {"message": "a" * 1001}, {}])
def test_classify_validation_422(client, payload):
    assert client.post("/classify", json=payload).status_code == 422


def test_message_of_exactly_1000_chars_ok(client, monkeypatch):
    monkeypatch.setattr(classifier, "call_llm", fake_llm())
    assert client.post("/classify", json={"message": "a" * 1000}).status_code == 200


def test_bad_model_output_is_saved_with_needs_review(client, monkeypatch):
    monkeypatch.setattr(classifier, "call_llm", lambda m, retry_hint=None: "garbage")
    r = client.post("/classify", json={"message": "hello"})
    assert r.status_code == 200
    body = r.json()
    assert (body["intent"], body["category"], body["needs_review"]) == ("other", "none", True)


def test_model_down_returns_503_and_saves_nothing(client, monkeypatch):
    def boom(message, retry_hint=None):
        raise classifier.LLMUnavailable("Ollama is not running")

    monkeypatch.setattr(classifier, "call_llm", boom)
    r = client.post("/classify", json={"message": "hello"})
    assert r.status_code == 503 and "Ollama" in r.json()["detail"]
    assert client.get("/messages").json() == []


def test_messages_newest_first_and_filters(client, monkeypatch):
    monkeypatch.setattr(classifier, "call_llm", fake_llm("book_service", "plumbing"))
    client.post("/classify", json={"message": "first"})
    monkeypatch.setattr(classifier, "call_llm", fake_llm("cancel", "painting"))
    client.post("/classify", json={"message": "second"})
    monkeypatch.setattr(classifier, "call_llm", lambda m, retry_hint=None: "bad")
    client.post("/classify", json={"message": "third"})

    assert [m["message"] for m in client.get("/messages").json()] == ["third", "second", "first"]
    assert [m["message"] for m in client.get("/messages?intent=cancel").json()] == ["second"]
    assert [m["message"] for m in client.get("/messages?category=plumbing").json()] == ["first"]
    assert [m["message"] for m in client.get("/messages?urgency=low").json()] == ["third", "second"]
    assert [m["message"] for m in client.get("/messages?needs_review=true").json()] == ["third"]
    assert client.get("/messages?intent=refund").status_code == 422


def test_stats(client, monkeypatch):
    monkeypatch.setattr(classifier, "call_llm", fake_llm("cancel", "painting"))
    client.post("/classify", json={"message": "cancel it"})
    stats = client.get("/stats").json()
    assert stats["total"] == 1 and stats["needs_review"] == 0
    assert stats["by_intent"]["cancel"] == 1 and stats["by_intent"]["other"] == 0
    assert stats["by_category"]["painting"] == 1
    assert stats["by_urgency"]["low"] == 1
