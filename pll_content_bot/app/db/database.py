from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.get_conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS content_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rubric_type TEXT NOT NULL,
                    source_item_id TEXT NOT NULL,
                    formatted_text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    published_at TEXT,
                    tags TEXT
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_content_unique
                    ON content_items(rubric_type, source_item_id, status)
                    WHERE status IN ('published', 'scheduled', 'ready', 'draft');

                CREATE TABLE IF NOT EXISTS dataset_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rubric_type TEXT NOT NULL,
                    source_item_id TEXT NOT NULL,
                    used_at TEXT NOT NULL,
                    status TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_dataset_usage_lookup
                    ON dataset_usage(rubric_type, source_item_id);

                CREATE TABLE IF NOT EXISTS runtime_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
