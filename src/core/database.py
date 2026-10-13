import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DB_DIR / "memory.db"


class Database:
    """
    SQLite-backed database for persistent conversation history and session memory.
    Zero external server dependencies, uses standard Python sqlite3.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        os.makedirs(self.db_path.parent, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    emotion TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    def create_or_get_session(self, session_id: str = "default", title: str = "Percakapan Utama") -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if not row:
                cursor.execute(
                    "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (session_id, title, datetime.now().isoformat(), datetime.now().isoformat())
                )
                conn.commit()
            return session_id

    def add_message(self, session_id: str, role: str, content: str, emotion: Optional[str] = None):
        self.create_or_get_session(session_id)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (session_id, role, content, emotion, timestamp) VALUES (?, ?, ?, ?, ?)",
                (session_id, role, content, emotion, datetime.now().isoformat())
            )
            cursor.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), session_id)
            )
            conn.commit()

    def get_messages(self, session_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, role, content, emotion, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC LIMIT ?",
                (session_id, limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_recent_messages(self, session_id: str = "default", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Returns the last `limit` messages for the session in chronological order (oldest to newest).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, role, content, emotion, timestamp FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in reversed(rows)]

    def get_sessions(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id, s.title, s.created_at, s.updated_at, COUNT(m.id) as message_count
                FROM sessions s
                LEFT JOIN messages m ON s.id = m.session_id
                GROUP BY s.id
                ORDER BY s.updated_at DESC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def clear_session_messages(self, session_id: str = "default"):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.commit()

    def delete_session(self, session_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()

    def delete_all(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages")
            cursor.execute("DELETE FROM sessions")
            conn.commit()


# Global Singleton instance
db = Database()
