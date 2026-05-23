import datetime as dt

import pytest

from gca.utils import git_date_string, parse_date


def test_utc_naive_is_treated_as_utc():
    when = dt.datetime(2024, 1, 15, 12, 0, 0)
    s = git_date_string(when)
    epoch, offset = s.split()
    assert int(epoch) == int(when.replace(tzinfo=dt.timezone.utc).timestamp())
    assert offset == "+0000"


def test_aware_offset_is_preserved():
    tz = dt.timezone(dt.timedelta(hours=-5, minutes=-30))
    when = dt.datetime(2024, 6, 1, 8, 30, 0, tzinfo=tz)
    s = git_date_string(when)
    epoch, offset = s.split()
    assert int(epoch) == int(when.timestamp())
    assert offset == "-0530"


def test_far_past():
    when = dt.datetime(1999, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc)
    s = git_date_string(when)
    epoch = int(s.split()[0])
    assert epoch == 946684799


def test_leap_day():
    when = dt.datetime(2024, 2, 29, 0, 0, 0, tzinfo=dt.timezone.utc)
    s = git_date_string(when)
    assert s.endswith("+0000")
    # round-trip
    epoch = int(s.split()[0])
    back = dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc)
    assert back == when


def test_parse_date_strict():
    assert parse_date("2024-05-23") == dt.date(2024, 5, 23)
    with pytest.raises(ValueError):
        parse_date("05/23/2024")
    with pytest.raises(ValueError):
        parse_date("2024-5-23")
