"""SQLite database layer (plain sqlite3, so it runs anywhere with zero setup)."""
import json
import sqlite3
from contextlib import contextmanager

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT NOT NULL,
    skills_json TEXT NOT NULL DEFAULT '[]',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS candidates (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id        INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    filename      TEXT NOT NULL,
    name          TEXT,
    email         TEXT,
    phone         TEXT,
    years_exp     REAL,
    score         REAL NOT NULL,
    skill_score   REAL NOT NULL,
    text_score    REAL NOT NULL,
    quality_score REAL NOT NULL,
    verdict       TEXT NOT NULL,
    matched_json  TEXT NOT NULL DEFAULT '[]',
    missing_json  TEXT NOT NULL DEFAULT '[]',
    extra_json    TEXT NOT NULL DEFAULT '[]',
    sections_json TEXT NOT NULL DEFAULT '[]',
    keywords_json TEXT NOT NULL DEFAULT '[]',
    resume_text   TEXT NOT NULL,
    insights      TEXT,
    insights_src  TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_candidates_job ON candidates(job_id, score DESC);
"""


def connect():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.executescript(SCHEMA)


def _loads(value, default):
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def job_row(row, candidate_count=0, top_score=None, avg_score=None):
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "skills": _loads(row["skills_json"], []),
        "created_at": row["created_at"],
        "candidate_count": candidate_count,
        "top_score": top_score,
        "avg_score": avg_score,
    }


def candidate_row(row, full=False):
    data = {
        "id": row["id"],
        "job_id": row["job_id"],
        "filename": row["filename"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"],
        "years_exp": row["years_exp"],
        "score": row["score"],
        "skill_score": row["skill_score"],
        "text_score": row["text_score"],
        "quality_score": row["quality_score"],
        "verdict": row["verdict"],
        "matched": _loads(row["matched_json"], []),
        "missing": _loads(row["missing_json"], []),
        "extra": _loads(row["extra_json"], []),
        "sections": _loads(row["sections_json"], []),
        "keywords": _loads(row["keywords_json"], []),
        "insights": row["insights"],
        "insights_src": row["insights_src"],
        "created_at": row["created_at"],
    }
    if full:
        data["resume_text"] = row["resume_text"]
    return data
