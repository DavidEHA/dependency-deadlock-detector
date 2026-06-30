"""Stage 4: severity = f(downstream blast radius x proximity to milestone).

Not just age. A node that's a little stale but blocks 7 tickets the day before
a milestone outranks one that's very stale but blocks nothing.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SeverityResult:
    score: float
    level: Severity
    blast_count: int
    days_to_milestone: float | None


def _milestone_multiplier(days_to_milestone: float | None) -> float:
    if days_to_milestone is None:
        return 1.0
    if days_to_milestone <= 3:
        return 2.0
    if days_to_milestone <= 7:
        return 1.5
    return 1.0


def score(
    blast_count: int,
    business_days_stale: float,
    threshold_business_days: float,
    days_to_milestone: float | None,
) -> SeverityResult:
    overdue = max(0.0, business_days_stale - threshold_business_days)
    raw = (blast_count + overdue * 2.0) * _milestone_multiplier(days_to_milestone)
    if raw >= 12:
        level = Severity.CRITICAL
    elif raw >= 7:
        level = Severity.HIGH
    elif raw >= 3:
        level = Severity.MEDIUM
    else:
        level = Severity.LOW
    return SeverityResult(round(raw, 1), level, blast_count, days_to_milestone)
