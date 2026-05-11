"""Lightweight SQLite mirror for user-scoped JSON datasets."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class SQLiteDataStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        conn = self.connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_records (
                    username TEXT NOT NULL,
                    dataset TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (username, dataset, record_id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_records_dataset
                ON user_records (username, dataset, updated_at DESC)
                """
            )
            conn.commit()
        finally:
            conn.close()

    def replace_dataset(self, username: str, dataset: str, rows: list[dict[str, Any]]) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        conn = self.connect()
        try:
            conn.execute(
                "DELETE FROM user_records WHERE username = ? AND dataset = ?",
                (username, dataset),
            )
            for index, row in enumerate(rows):
                record_id = str(row.get("id") or row.get("symbol") or row.get("time") or index)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO user_records
                    (username, dataset, record_id, payload, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (username, dataset, record_id, json.dumps(row, ensure_ascii=False), now),
                )
            conn.commit()
        finally:
            conn.close()

    def read_dataset(self, username: str, dataset: str) -> list[dict[str, Any]]:
        conn = self.connect()
        try:
            rows = conn.execute(
                """
                SELECT payload
                FROM user_records
                WHERE username = ? AND dataset = ?
                ORDER BY updated_at DESC, record_id ASC
                """,
                (username, dataset),
            ).fetchall()
        finally:
            conn.close()
        return [json.loads(row["payload"]) for row in rows]

    def migrate_userspace(self, userspace_dir: str | Path) -> int:
        userspace = Path(userspace_dir)
        if not userspace.exists():
            return 0
        migrated = 0
        file_map = {
            "holdings": "holdings.json",
            "history": "analysis_history.json",
            "alerts": "alerts.json",
            "automations": "automations.json",
            "automation_log": "automation_log.json",
        }
        for user_dir in userspace.iterdir():
            if not user_dir.is_dir():
                continue
            username = user_dir.name
            for dataset, filename in file_map.items():
                path = user_dir / filename
                if not path.exists():
                    continue
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if dataset == "holdings" and isinstance(data, dict):
                    rows = data.get(username, [])
                else:
                    rows = data if isinstance(data, list) else []
                if rows:
                    self.replace_dataset(username, dataset, rows)
                    migrated += len(rows)
        return migrated
