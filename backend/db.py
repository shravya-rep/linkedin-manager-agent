import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "linklens.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT,
                text TEXT NOT NULL,
                topic TEXT,
                signal_score REAL,
                relevance_score REAL,
                anxiety_score REAL,
                action TEXT,
                reason TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_action ON posts (action)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON posts (created_at)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                post_id TEXT PRIMARY KEY,
                feedback TEXT NOT NULL,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS block_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


def save_block_pattern(pattern: str, description: str):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO block_patterns (pattern, description)
            VALUES (?, ?)
        """, (pattern, description))
        conn.commit()


def get_block_patterns() -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT pattern, description FROM block_patterns").fetchall()
    return [dict(r) for r in rows]


def save_post(post_id, text, topic, signal_score, relevance_score, anxiety_score, action, reason):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO posts (post_id, text, topic, signal_score, relevance_score, anxiety_score, action, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (post_id, text, topic, signal_score, relevance_score, anxiety_score, action, reason))
        conn.commit()


def get_highlights_today():
    """Return all HIGHLIGHT posts from the last 24 hours."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT text, topic, signal_score, reason
            FROM posts
            WHERE action = 'HIGHLIGHT'
              AND created_at >= datetime('now', '-24 hours')
            ORDER BY signal_score DESC
        """).fetchall()
    return [dict(r) for r in rows]


def save_feedback(post_id: str, feedback: str):
    """feedback: 'like' or 'dislike'"""
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO feedback (post_id, feedback, created_at)
            VALUES (?, ?, datetime('now'))
        """, (post_id, feedback))
        conn.commit()


def get_topic_weights() -> dict:
    """Return topic preference weights derived from feedback history."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT p.topic,
                   SUM(CASE WHEN f.feedback = 'like' THEN 1 ELSE 0 END) AS likes,
                   SUM(CASE WHEN f.feedback = 'dislike' THEN 1 ELSE 0 END) AS dislikes
            FROM feedback f
            JOIN posts p ON p.post_id = f.post_id
            GROUP BY p.topic
        """).fetchall()
    weights = {}
    for r in rows:
        net = r["likes"] - r["dislikes"]
        weights[r["topic"]] = net
    return weights


def get_recent_posts(limit=50):
    """Return the most recent scored posts regardless of action."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT post_id, text, topic, signal_score, relevance_score, anxiety_score, action, reason, created_at
            FROM posts
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]
