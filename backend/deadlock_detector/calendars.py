"""Business-hours / working-calendar logic — timezone- and holiday-aware.

Core design decision (the biggest product risk addressed): staleness must be
measured in the *owner's* working time, not naive wall-clock. A fixed "48h"
fires on weekends and ignores timezones (India team vs Mexico team), which
produces false positives -> alert fatigue -> the tool gets ignored, which is
the exact failure it's meant to fix.

By counting only working hours in the owner's IANA timezone and skipping
weekends + regional holidays, weekend handling falls out for free:
Fri 18:00 -> Mon 09:00 = 0 business hours.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

from .models import Owner


@dataclass(frozen=True)
class WorkingCalendar:
    timezone: str
    work_start_hour: int = 9
    work_end_hour: int = 18
    work_days: frozenset[int] = frozenset({0, 1, 2, 3, 4})  # Mon=0 .. Sun=6
    holidays: frozenset[date] = field(default_factory=frozenset)

    @property
    def _tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    def _is_working_day(self, d: date) -> bool:
        return d.weekday() in self.work_days and d not in self.holidays

    def business_hours_between(self, start: datetime, end: datetime) -> float:
        """Working hours between two tz-aware instants, in this calendar."""
        if end <= start:
            return 0.0
        tz = self._tz
        local_start = start.astimezone(tz)
        local_end = end.astimezone(tz)
        total = 0.0
        day = local_start.date()
        while day <= local_end.date():
            if self._is_working_day(day):
                window_open = datetime.combine(day, time(self.work_start_hour), tz)
                window_close = datetime.combine(day, time(self.work_end_hour), tz)
                lo = max(window_open, local_start)
                hi = min(window_close, local_end)
                if hi > lo:
                    total += (hi - lo).total_seconds() / 3600.0
            day += timedelta(days=1)
        return total

    def business_days_between(self, start: datetime, end: datetime) -> float:
        hours_per_day = max(1, self.work_end_hour - self.work_start_hour)
        return self.business_hours_between(start, end) / hours_per_day


@lru_cache(maxsize=64)
def _holidays_for(region: str) -> frozenset[date]:
    """Per-region holidays via the optional `holidays` package; empty if absent."""
    try:
        import holidays as _h  # optional dependency
    except Exception:
        return frozenset()
    try:
        this_year = date.today().year
        cal = _h.country_holidays(region, years=[this_year, this_year + 1])
        return frozenset(cal.keys())
    except Exception:
        return frozenset()


def calendar_for(owner: Owner) -> WorkingCalendar:
    return WorkingCalendar(timezone=owner.timezone, holidays=_holidays_for(owner.region))
