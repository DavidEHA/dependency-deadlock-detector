from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..models import Ticket
from ..severity import SeverityResult


@dataclass
class EscalationContext:
    """Everything the drafter needs — all computed deterministically upstream.

    The LLM never counts tickets or traverses the graph; it only turns these
    facts into prose.
    """

    stale_ticket: Ticket
    business_days_stale: float
    severity: SeverityResult
    blocked_keys: list[str]
    affected_teams: list[str]
    chain_preview: list[str]       # e.g. ["CLIENT-204", "TEAMB-88", "TEAMA-42"]
    days_to_milestone: float | None


class Drafter(Protocol):
    name: str

    def draft(self, ctx: EscalationContext) -> str: ...
