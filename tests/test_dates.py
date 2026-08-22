from datetime import date, datetime

import pytest

from app.utils.dates import custom, day, month, year


def test_day_range_is_midnight_to_midnight():
    r = day(date(2026, 3, 15))
    assert r.start == datetime(2026, 3, 15, 0, 0, 0)
    assert r.end_exclusive == datetime(2026, 3, 16, 0, 0, 0)


def test_day_range_boundaries_inclusive_exclusive():
    r = day(date(2026, 3, 15))
    assert r.contains(datetime(2026, 3, 15, 0, 0, 0))
    assert r.contains(datetime(2026, 3, 15, 23, 59, 59))
    assert not r.contains(datetime(2026, 3, 16, 0, 0, 0))
    assert not r.contains(datetime(2026, 3, 14, 23, 59, 59))


def test_month_range_handles_variable_month_lengths():
    feb = month(2026, 2)
    assert feb.start == datetime(2026, 2, 1)
    assert feb.end_exclusive == datetime(2026, 3, 1)

    # 2026 is not a leap year: Feb has 28 days.
    assert feb.contains(datetime(2026, 2, 28, 23, 59, 59))
    assert not feb.contains(datetime(2026, 3, 1, 0, 0, 0))


def test_month_range_leap_year_february():
    feb = month(2028, 2)
    assert feb.end_exclusive == datetime(2028, 3, 1)
    assert feb.contains(datetime(2028, 2, 29, 12, 0, 0))


def test_year_range():
    r = year(2026)
    assert r.start == datetime(2026, 1, 1)
    assert r.end_exclusive == datetime(2027, 1, 1)
    assert r.contains(datetime(2026, 12, 31, 23, 59, 59))
    assert not r.contains(datetime(2027, 1, 1, 0, 0, 0))


def test_custom_range_is_inclusive_of_both_endpoints():
    r = custom(date(2026, 1, 10), date(2026, 1, 12))
    assert r.contains(datetime(2026, 1, 10, 0, 0, 0))
    assert r.contains(datetime(2026, 1, 12, 23, 59, 59))
    assert not r.contains(datetime(2026, 1, 13, 0, 0, 0))
    assert not r.contains(datetime(2026, 1, 9, 23, 59, 59))


def test_custom_range_single_day_matches_day_range():
    r = custom(date(2026, 1, 10), date(2026, 1, 10))
    d = day(date(2026, 1, 10))
    assert r.start == d.start
    assert r.end_exclusive == d.end_exclusive


def test_custom_range_rejects_end_before_start():
    with pytest.raises(ValueError):
        custom(date(2026, 1, 12), date(2026, 1, 10))
