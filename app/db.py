"""SQLite storage (standard library only). One short-lived connection per call."""
import sqlite3
from contextlib import closing
from typing import Optional

from app import config
from app.labels import CATEGORIES, INTENTS, URGENCIES

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    message          TEXT    NOT NULL,
    intent           TEXT    NOT NULL,
    category         TEXT    NOT NULL,
    urgency          TEXT    NOT NULL,
    safety_risk      INTEGER NOT NULL,
    summary          TEXT    NOT NULL,
    needs_review     INTEGER NOT NULL,
    model            TEXT    NOT NULL,
    response_ms      INTEGER NOT NULL,
    invalid_attempts INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(_connect()) as conn:
        conn.execute(SCHEMA)
        conn.commit()


def _to_dict(row: sqlite3.Row) -> dict:
    item = dict(row)
    item["safety_risk"] = bool(item["safety_risk"])
    item["needs_review"] = bool(item["needs_review"])
    return item


def save_message(message: str, c, model: str) -> int:
    """Insert one classification (c is a classifier.Classification) and return its id."""
    with closing(_connect()) as conn:
        cur = conn.execute(
            """INSERT INTO messages
               (message, intent, category, urgency, safety_risk, summary,
                needs_review, model, response_ms, invalid_attempts)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                message, c.intent, c.category, c.urgency, int(c.safety_risk), c.summary,
                int(c.needs_review), model, c.response_ms, c.invalid_attempts,
            ),
        )
        conn.commit()
        return cur.lastrowid


def list_messages(
    intent: Optional[str] = None,
    category: Optional[str] = None,
    urgency: Optional[str] = None,
    needs_review: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> list:
    """Newest first. Filters are optional; values are passed as SQL parameters."""
    where, params = [], []
    if intent is not None:
        where.append("intent = ?")
        params.append(intent)
    if category is not None:
        where.append("category = ?")
        params.append(category)
    if urgency is not None:
        where.append("urgency = ?")
        params.append(urgency)
    if needs_review is not None:
        where.append("needs_review = ?")
        params.append(int(needs_review))

    sql = "SELECT * FROM messages"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params += [limit, offset]

    with closing(_connect()) as conn:
        return [_to_dict(r) for r in conn.execute(sql, params).fetchall()]


def get_stats() -> dict:
    """Counts by intent / category / urgency (every label shown, even with 0) + review count."""
    with closing(_connect()) as conn:
        def counts(column: str, labels: tuple) -> dict:
            result = {label: 0 for label in labels}
            for row in conn.execute(f"SELECT {column} AS k, COUNT(*) AS n FROM messages GROUP BY {column}"):
                result[row["k"]] = row["n"]
            return result

        total = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        review = conn.execute("SELECT COUNT(*) FROM messages WHERE needs_review = 1").fetchone()[0]
        return {
            "total": total,
            "by_intent": counts("intent", INTENTS),
            "by_category": counts("category", CATEGORIES),
            "by_urgency": counts("urgency", URGENCIES),
            "needs_review": review,
        }
