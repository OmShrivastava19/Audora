"""Simple JSON-backed storage for generation results.

This keeps the project runnable without introducing a database dependency.
"""
from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any


class ResultStore:
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self._lock = Lock()
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_path.exists():
            self.data_path.write_text("{}", encoding="utf-8")

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        raw = self.data_path.read_text(encoding="utf-8").strip()
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def _write(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        self.data_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def save_result(self, user_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            data = self._read()
            bucket = data.setdefault(user_id, [])
            bucket.insert(0, result)
            self._write(data)

    def list_history(self, user_id: str, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        with self._lock:
            data = self._read()
            bucket = data.get(user_id, [])
            return bucket[offset : offset + limit]

    def get_result(self, user_id: str, result_id: str) -> dict[str, Any] | None:
        with self._lock:
            data = self._read()
            bucket = data.get(user_id, [])
            for item in bucket:
                if item.get("id") == result_id:
                    return item
            return None
