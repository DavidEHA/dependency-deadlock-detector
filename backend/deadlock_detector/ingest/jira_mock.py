"""Mock Jira ingestor — reads a JSON fixture shaped like the Jira REST output.

MVP scope: only Jira issue links (`blocks` / `is blocked by`) + status +
last-updated. Structured and reliable. Emails / meeting transcripts (noisy LLM
extraction) are deferred to phase 2. Swapping this for a real Jira client is a
single class behind the Ingestor interface.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..models import DependencyType, Owner, Ticket


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class MockJiraIngestor:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def fetch(self) -> list[Ticket]:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        owners = {o["handle"]: Owner(**o) for o in raw["owners"]}
        tickets: list[Ticket] = []
        for t in raw["tickets"]:
            tickets.append(
                Ticket(
                    key=t["key"],
                    summary=t["summary"],
                    status=t["status"],
                    dep_type=DependencyType(t["dep_type"]),
                    owner=owners[t["owner"]],
                    last_activity=_parse_dt(t["last_activity"]),
                    blocked_by=t.get("blocked_by", []),
                    milestone=t.get("milestone"),
                    milestone_due=_parse_dt(t["milestone_due"]) if t.get("milestone_due") else None,
                )
            )
        return tickets
