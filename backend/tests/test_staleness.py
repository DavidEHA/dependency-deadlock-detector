from datetime import datetime, timezone

from deadlock_detector.calendars import WorkingCalendar

# Mexico City is UTC-6 year-round (DST abolished in 2022).
MX = WorkingCalendar(timezone="America/Mexico_City")


def test_weekend_is_skipped():
    # Fri 18:00 local -> Mon 09:00 local = 0 working hours.
    start = datetime(2026, 6, 20, 0, 0, tzinfo=timezone.utc)   # Fri 18:00 MX
    end = datetime(2026, 6, 22, 15, 0, tzinfo=timezone.utc)    # Mon 09:00 MX
    assert MX.business_hours_between(start, end) == 0.0


def test_single_working_day():
    # Mon 09:00 -> Mon 18:00 MX = 9 working hours = 1.0 working day.
    start = datetime(2026, 6, 22, 15, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 23, 0, 0, tzinfo=timezone.utc)
    assert MX.business_hours_between(start, end) == 9.0
    assert MX.business_days_between(start, end) == 1.0


def test_india_timezone_half_hour_offset():
    # Asia/Kolkata is UTC+5:30 — a fixed-offset assumption would be wrong.
    india = WorkingCalendar(timezone="Asia/Kolkata")
    # Thu 18:00 IST (end of workday) -> Fri 18:00 IST = exactly one work day.
    start = datetime(2026, 6, 18, 12, 30, tzinfo=timezone.utc)  # Thu 18:00 IST
    end = datetime(2026, 6, 19, 12, 30, tzinfo=timezone.utc)    # Fri 18:00 IST
    assert india.business_hours_between(start, end) == 9.0
