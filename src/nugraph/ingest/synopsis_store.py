"""Persistent store for scraped synopses (SQLite).

This doubles as the scraper's **resume log**: every novel we attempt is recorded with a
status, so a re-run skips everything already done. M4 reads `ok` rows to build embeddings.

statuses: 'ok' (got text) | 'empty' (page had no description) | 'notfound' (no series page)
          | 'error' (request failed after retries)
"""

from __future__ import annotations

import datetime as _dt
import sqlite3
from pathlib import Path

from ..config import settings

DB_PATH: Path = settings.processed_dir / "synopses.sqlite"


def _conn() -> sqlite3.Connection:
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS synopsis (
               id          INTEGER PRIMARY KEY,
               description TEXT,
               status      TEXT NOT NULL,
               fetched_at  TEXT NOT NULL
           )"""
    )
    return conn


def done_ids() -> set[int]:
    """Ids already attempted (any status) — used to resume."""
    with _conn() as c:
        return {row[0] for row in c.execute("SELECT id FROM synopsis")}


def upsert(novel_id: int, description: str | None, status: str) -> None:
    now = _dt.datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO synopsis (id, description, status, fetched_at) VALUES (?, ?, ?, ?)",
            (novel_id, description, status, now),
        )


def get_descriptions() -> dict[int, str]:
    """All successfully-scraped descriptions ({id: text}). Used by M4 embedding."""
    with _conn() as c:
        return {
            row[0]: row[1]
            for row in c.execute("SELECT id, description FROM synopsis WHERE status = 'ok'")
        }


def get_one(novel_id: int) -> str | None:
    """Single successfully-scraped description, or None."""
    with _conn() as c:
        row = c.execute(
            "SELECT description FROM synopsis WHERE id = ? AND status = 'ok'", (novel_id,)
        ).fetchone()
    return row[0] if row else None


def stats() -> dict[str, int]:
    with _conn() as c:
        return dict(c.execute("SELECT status, COUNT(*) FROM synopsis GROUP BY status").fetchall())
