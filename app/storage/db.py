"""SQLite storage — ephemeral dictation history + permanent stats."""

import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path


class MurmurDB:
    """Manages dictation history (24h retention) and lifetime stats."""

    DB_PATH = Path.home() / ".murmur" / "murmur.db"
    RETENTION_HOURS = 24

    def __init__(self, db_path: Path | None = None):
        self._db_path = db_path or self.DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")

        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS dictations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                raw_text TEXT NOT NULL,
                cleaned_text TEXT NOT NULL,
                language TEXT DEFAULT 'unknown',
                mode TEXT DEFAULT 'normal',
                duration_seconds REAL DEFAULT 0,
                word_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                first_use_date TEXT NOT NULL,
                total_words INTEGER DEFAULT 0,
                total_sessions INTEGER DEFAULT 0,
                total_seconds REAL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)

        # Initialize stats row if not exists
        self._conn.execute("""
            INSERT OR IGNORE INTO stats (id, first_use_date, total_words, total_sessions, total_seconds)
            VALUES (1, datetime('now'), 0, 0, 0)
        """)

        self._conn.commit()

    # ── Dictation history (ephemeral) ──────────────────────────────

    def save_dictation(
        self,
        raw_text: str,
        cleaned_text: str,
        language: str = "unknown",
        mode: str = "normal",
        duration_seconds: float = 0,
    ) -> int:
        """Save a dictation entry and update stats."""
        word_count = len(cleaned_text.split())

        cursor = self._conn.execute(
            """INSERT INTO dictations
               (raw_text, cleaned_text, language, mode, duration_seconds, word_count)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (raw_text, cleaned_text, language, mode, duration_seconds, word_count),
        )

        # Update lifetime stats
        self._conn.execute(
            """UPDATE stats SET
               total_words = total_words + ?,
               total_sessions = total_sessions + 1,
               total_seconds = total_seconds + ?
               WHERE id = 1""",
            (word_count, duration_seconds),
        )

        self._conn.commit()
        return cursor.lastrowid

    def get_recent_dictations(self, limit: int = 50) -> list[dict]:
        """Get recent dictations (within retention period)."""
        self._purge_old()
        cursor = self._conn.execute(
            """SELECT * FROM dictations
               ORDER BY timestamp DESC LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def _purge_old(self) -> None:
        """Delete dictations older than retention period."""
        cutoff = datetime.utcnow() - timedelta(hours=self.RETENTION_HOURS)
        self._conn.execute(
            "DELETE FROM dictations WHERE timestamp < ?",
            (cutoff.isoformat(),),
        )
        self._conn.commit()

    # ── Stats (permanent) ──────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get lifetime usage statistics."""
        row = self._conn.execute("SELECT * FROM stats WHERE id = 1").fetchone()
        if not row:
            return {}

        stats = dict(row)

        # Calculate weeks active
        first_use = datetime.fromisoformat(stats["first_use_date"])
        weeks = max(1, (datetime.utcnow() - first_use).days // 7)
        stats["weeks_active"] = weeks

        # Calculate average WPM
        total_minutes = stats["total_seconds"] / 60
        if total_minutes > 0:
            stats["avg_wpm"] = round(stats["total_words"] / total_minutes)
        else:
            stats["avg_wpm"] = 0

        return stats

    # ── Settings ───────────────────────────────────────────────────

    def get_setting(self, key: str, default: str = "") -> str:
        """Get a setting value."""
        row = self._conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Set a setting value."""
        self._conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        self._conn.commit()

    def get_all_settings(self) -> dict[str, str]:
        """Get all settings as a dict."""
        cursor = self._conn.execute("SELECT key, value FROM settings")
        return {row["key"]: row["value"] for row in cursor.fetchall()}

    # ── Lifecycle ──────────────────────────────────────────────────

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
