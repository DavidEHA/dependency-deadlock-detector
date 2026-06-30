"""Domain models for the dependency graph."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DependencyType(str, Enum):
    """Kind of dependency — drives the staleness threshold.

    Clients are slower than internal teams, so a tighter threshold on a client
    sign-off would just generate noise. Thresholds are in *working days*.
    """

    INTERNAL_BLOCKER = "internal_blocker"
    CLIENT_SIGN_OFF = "client_sign_off"
    TECHNICAL = "technical"

    @property
    def threshold_business_days(self) -> float:
        return {
            DependencyType.INTERNAL_BLOCKER: 1.0,
            DependencyType.CLIENT_SIGN_OFF: 2.0,
            DependencyType.TECHNICAL: 1.5,
        }[self]


@dataclass(frozen=True)
class Owner:
    """The person responsible for the *next action* on a dependency.

    Staleness is measured against this person's working calendar — that's the
    whole point: escalating someone during their night/weekend/holiday is the
    false positive we're trying to avoid.
    """

    name: str
    handle: str          # for @mention, e.g. "priya.nair"
    timezone: str        # IANA tz, e.g. "Asia/Kolkata" (never a fixed offset)
    region: str          # ISO country for the holiday calendar, e.g. "IN", "MX"


@dataclass
class Ticket:
    key: str
    summary: str
    status: str
    dep_type: DependencyType
    owner: Owner
    last_activity: datetime                 # tz-aware (stored in UTC)
    blocked_by: list[str] = field(default_factory=list)  # keys this ticket waits on
    milestone: str | None = None
    milestone_due: datetime | None = None   # tz-aware (UTC)
