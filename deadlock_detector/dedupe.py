"""Dedupe: escalate a node only once; re-draft only if severity rises.

Without this, an hourly scan re-calls the LLM every hour on the same stale node
— wasted tokens *and* it spams the owner. Mandatory for cost + trust.
"""
from __future__ import annotations

import json
from pathlib import Path


class EscalationLedger:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self._state: dict[str, float] = {}
        if self.path and self.path.exists():
            try:
                self._state = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self._state = {}

    def should_escalate(self, key: str, severity_score: float) -> bool:
        prev = self._state.get(key)
        return prev is None or severity_score > prev

    def record(self, key: str, severity_score: float) -> None:
        self._state[key] = severity_score
        if self.path:
            self.path.write_text(json.dumps(self._state, indent=2), encoding="utf-8")
