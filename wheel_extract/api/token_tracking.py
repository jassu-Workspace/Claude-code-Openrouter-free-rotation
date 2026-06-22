"""Token usage tracking with SQLite persistence."""

from __future__ import annotations

import sqlite3
import threading
from datetime import UTC, date, datetime
from typing import Any

from config.paths import config_dir_path

_DB_DIR = config_dir_path() / ".fcc"
_DB_PATH = _DB_DIR / "token_tracking.db"

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    last_activity TEXT NOT NULL,
    date TEXT NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    request_count INTEGER DEFAULT 0,
    model TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS token_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    date TEXT NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    model TEXT DEFAULT '',
    request_id TEXT DEFAULT '',
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(date);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_events_date ON token_events(date);
CREATE INDEX IF NOT EXISTS idx_events_session ON token_events(session_id);
"""


def _conn() -> sqlite3.Connection:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(_DB_PATH), timeout=10)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=3000")
    db.executescript(_CREATE_SQL)
    db.commit()
    return db


def _today() -> str:
    return date.today().isoformat()


def _now() -> str:
    return datetime.now(UTC).isoformat()


_local = threading.local()


def _get_db() -> sqlite3.Connection:
    if not hasattr(_local, "db") or _local.db is None:
        _local.db = _conn()
    return _local.db


def close() -> None:
    if hasattr(_local, "db") and _local.db is not None:
        _local.db.close()
        _local.db = None


def track_event(
    session_id: str,
    input_tokens: int,
    output_tokens: int,
    model: str = "",
    request_id: str = "",
) -> None:
    """Record a token usage event and update session totals."""
    db = _get_db()
    now = _now()
    today = _today()
    try:
        db.execute(
            "INSERT OR IGNORE INTO sessions (session_id, started_at, last_activity, date, model) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, now, now, today, model),
        )
        db.execute(
            "UPDATE sessions SET input_tokens = input_tokens + ?, "
            "output_tokens = output_tokens + ?, "
            "request_count = request_count + 1, "
            "last_activity = ?, "
            "model = CASE WHEN ? != '' THEN ? ELSE model END, "
            "is_active = 1 "
            "WHERE session_id = ?",
            (input_tokens, output_tokens, now, model, model, session_id),
        )
        db.execute(
            "INSERT INTO token_events (session_id, timestamp, date, input_tokens, output_tokens, model, request_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, now, today, input_tokens, output_tokens, model, request_id),
        )
        db.commit()
    except Exception:
        db.rollback()


def deactivate_session(session_id: str) -> None:
    """Mark a session as no longer active."""
    db = _get_db()
    try:
        db.execute(
            "UPDATE sessions SET is_active = 0 WHERE session_id = ?", (session_id,)
        )
        db.commit()
    except Exception:
        db.rollback()


def prune_old_sessions(days: int = 30) -> int:
    """Remove inactive sessions older than `days` days. Returns rows deleted."""
    db = _get_db()
    try:
        cur = db.execute(
            "DELETE FROM sessions WHERE is_active = 0 AND date < date('now', ?)",
            (f"-{days} days",),
        )
        db.commit()
        return cur.rowcount or 0
    except Exception:
        db.rollback()
        return 0


def get_active_sessions() -> list[dict[str, Any]]:
    """Return all active sessions ordered by last_activity desc."""
    db = _get_db()
    db.row_factory = sqlite3.Row
    rows = db.execute(
        "SELECT * FROM sessions WHERE is_active = 1 ORDER BY last_activity DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_all_sessions(limit: int = 100) -> list[dict[str, Any]]:
    """Return recent sessions ordered by last_activity desc."""
    db = _get_db()
    db.row_factory = sqlite3.Row
    rows = db.execute(
        "SELECT * FROM sessions ORDER BY last_activity DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_daily_usage(days: int = 30) -> list[dict[str, Any]]:
    """Return aggregated token usage per day."""
    db = _get_db()
    db.row_factory = sqlite3.Row
    rows = db.execute(
        "SELECT date, SUM(input_tokens) as input_tokens, "
        "SUM(output_tokens) as output_tokens, "
        "SUM(request_count) as request_count, "
        "COUNT(DISTINCT session_id) as session_count "
        "FROM sessions "
        "GROUP BY date "
        "ORDER BY date DESC "
        "LIMIT ?",
        (days,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_summary() -> dict[str, Any]:
    """Return overall token usage summary."""
    db = _get_db()
    row = db.execute(
        "SELECT "
        "COALESCE(SUM(input_tokens), 0) as total_input, "
        "COALESCE(SUM(output_tokens), 0) as total_output, "
        "COALESCE(SUM(request_count), 0) as total_requests, "
        "COUNT(DISTINCT session_id) as total_sessions "
        "FROM sessions"
    ).fetchone()
    today_row = db.execute(
        "SELECT "
        "COALESCE(SUM(input_tokens), 0) as today_input, "
        "COALESCE(SUM(output_tokens), 0) as today_output, "
        "COALESCE(SUM(request_count), 0) as today_requests "
        "FROM sessions WHERE date = ?",
        (_today(),),
    ).fetchone()
    active_count = db.execute(
        "SELECT COUNT(*) FROM sessions WHERE is_active = 1"
    ).fetchone()[0]
    input_total = row[0] or 0
    output_total = row[1] or 0
    return {
        "total_input_tokens": input_total,
        "total_output_tokens": output_total,
        "total_tokens": input_total + output_total,
        "total_requests": row[2] or 0,
        "total_sessions": row[3] or 0,
        "active_sessions": active_count,
        "today_input_tokens": today_row[0] or 0,
        "today_output_tokens": today_row[1] or 0,
        "today_tokens": (today_row[0] or 0) + (today_row[1] or 0),
        "today_requests": today_row[2] or 0,
    }


def get_session_detail(session_id: str) -> dict[str, Any] | None:
    """Return detail for a single session including recent events."""
    db = _get_db()
    db.row_factory = sqlite3.Row
    session = db.execute(
        "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    if not session:
        return None
    events = db.execute(
        "SELECT * FROM token_events WHERE session_id = ? ORDER BY timestamp DESC LIMIT 50",
        (session_id,),
    ).fetchall()
    result = dict(session)
    result["events"] = [dict(e) for e in events]
    return result
