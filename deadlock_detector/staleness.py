"""Stage 2: flag dependencies that have gone silent too long.

Deterministic (zero LLM tokens). Staleness only *detects candidates*; severity
(stage 4) *ranks* them. Keeping the two separate is deliberate.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .calendars import calendar_for
from .models import Ticket


@dataclass
class StalenessResult:
    ticket: Ticket
    business_days_stale: float
    threshold_business_days: float
    is_stale: bool


def assess(ticket: Ticket, now: datetime) -> StalenessResult:
    cal = calendar_for(ticket.owner)
    stale = cal.business_days_between(ticket.last_activity, now)
    threshold = ticket.dep_type.threshold_business_days
    return StalenessResult(
        ticket=ticket,
        business_days_stale=stale,
        threshold_business_days=threshold,
        is_stale=stale > threshold,
    )
