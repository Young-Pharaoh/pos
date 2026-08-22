"""Date-range handling for reports.

The shop operates in a single location, so timestamps are stored and
compared as naive local time -- there is no multi-timezone concern to
model. All ranges are half-open: ``start <= ts < end_exclusive``. This
keeps day/month/year boundaries unambiguous and avoids double-counting a
row that lands exactly on a boundary timestamp.

Note: because timestamps are naive local time, a report window that spans
a daylight-saving transition will be off by an hour relative to wall-clock
time. This is an accepted limitation for a small single-location shop.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta


@dataclass(frozen=True)
class DateRange:
    """A half-open datetime range ``[start, end_exclusive)`` with a label."""

    start: datetime
    end_exclusive: datetime
    label: str

    def contains(self, ts: datetime) -> bool:
        return self.start <= ts < self.end_exclusive

    @property
    def start_date(self) -> date:
        return self.start.date()

    @property
    def end_date_inclusive(self) -> date:
        """Last calendar date included in the range."""
        return (self.end_exclusive - timedelta(seconds=1)).date()


def _start_of_day(d: date) -> datetime:
    return datetime(d.year, d.month, d.day)


def day(on: date) -> DateRange:
    start = _start_of_day(on)
    return DateRange(start, start + timedelta(days=1), label=on.isoformat())


def month(year: int, month_number: int) -> DateRange:
    start = datetime(year, month_number, 1)
    days_in_month = calendar.monthrange(year, month_number)[1]
    end_exclusive = start + timedelta(days=days_in_month)
    return DateRange(start, end_exclusive, label=f"{year:04d}-{month_number:02d}")


def year(year_number: int) -> DateRange:
    start = datetime(year_number, 1, 1)
    end_exclusive = datetime(year_number + 1, 1, 1)
    return DateRange(start, end_exclusive, label=f"{year_number:04d}")


def custom(start_date: date, end_date: date) -> DateRange:
    """Inclusive of both ``start_date`` and ``end_date`` as calendar days."""
    if end_date < start_date:
        raise ValueError("end_date cannot be before start_date")
    start = _start_of_day(start_date)
    end_exclusive = _start_of_day(end_date) + timedelta(days=1)
    label = f"{start_date.isoformat()} to {end_date.isoformat()}"
    return DateRange(start, end_exclusive, label=label)


def today() -> DateRange:
    return day(datetime.now().date())


def this_month() -> DateRange:
    now = datetime.now()
    return month(now.year, now.month)


def this_year() -> DateRange:
    return year(datetime.now().year)
