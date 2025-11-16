"""Simple JSON-based storage for tracking seen jobs and applications."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class JsonStateStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.data: Dict[str, Any] = {"seen_jobs": {}, "applications": {}}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            self.data = json.loads(self.path.read_text())

    def _persist(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2))

    def has_seen(self, job_id: str) -> bool:
        return job_id in self.data["seen_jobs"]

    def record_seen(self, job_id: str, meta: Dict[str, Any]) -> None:
        self.data["seen_jobs"][job_id] = meta
        self._persist()

    def record_application(self, job_id: str, status: str, message: str) -> None:
        self.data["applications"][job_id] = {"status": status, "message": message}
        self._persist()
