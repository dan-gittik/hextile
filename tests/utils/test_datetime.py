import datetime as dt

from hextile.utils import (
    now,
    datetime,
    datetime_to_timestamp,
    datetime_from_timestamp,
    datetime_to_string,
    datetime_from_string,
)


def test_now():
    d1 = now()
    assert d1.tzinfo is dt.timezone.utc
    d2 = dt.datetime.now().astimezone()
    assert (d2 - d1).total_seconds() < 1


def test_datetime():
    d1 = datetime(2000, 1, 1, 12)
    assert d1.tzinfo is dt.timezone.utc
    d2 = dt.datetime(2000, 1, 1, 12, tzinfo=dt.timezone.utc)
    assert (d2 - d1).total_seconds() < 1


def test_datetime_to_timestamp():
    d = datetime(2000, 1, 1, 12)
    t = datetime_to_timestamp(d)
    assert t == 946728000.0


def test_datetime_to_timestamp_naive():
    d = dt.datetime(2000, 1, 1, 12)
    t = datetime_to_timestamp(d)
    assert t == 946728000.0 - d.astimezone().tzinfo.utcoffset(None).total_seconds()


def test_datetime_to_timestamp_with_timezone():
    d = dt.datetime(2000, 1, 1, 12).astimezone()
    t = datetime_to_timestamp(d)
    assert t == 946728000.0 - d.tzinfo.utcoffset(None).total_seconds()


def test_datetime_from_timestamp():
    d = datetime_from_timestamp(946728000.0)
    assert d.year == 2000
    assert d.month == 1
    assert d.day == 1
    assert d.hour == 12
    assert d.minute == 0
    assert d.second == 0
    assert d.microsecond == 0
    assert d.tzinfo is dt.timezone.utc


def test_datetime_to_string():
    d = datetime(2000, 1, 1, 12)
    s = datetime_to_string(d, local=False)
    assert s == '2000-01-01T12:00:00+00:00'


def test_datetime_to_string_naive():
    d = dt.datetime.now()
    u = d.astimezone(dt.timezone.utc)
    assert datetime_to_string(d, local=False) == u.isoformat()


def test_datetime_to_string_with_timezone():
    d = dt.datetime.now().astimezone()
    assert datetime_to_string(d, local=False) == d.isoformat()


def test_datetime_to_string_with_format():
    d = datetime(2000, 1, 1, 12)
    s = datetime_to_string(d, format='%d/%m/%Y %H:%M:%S', local=False)
    assert s == '01/01/2000 12:00:00'


def test_datetime_to_string_local():
    d1 = now()
    d2 = dt.datetime.now()
    f = '%Y-%m-%d %H:%M'
    assert datetime_to_string(d1, f, local=True) == d2.strftime(f)


def test_datetime_from_string():
    d = datetime_from_string('2000-01-01T12:00:00', local=False)
    assert d.year == 2000
    assert d.month == 1
    assert d.day == 1
    assert d.hour == 12
    assert d.minute == 0
    assert d.second == 0
    assert d.microsecond == 0
    assert d.tzinfo is dt.timezone.utc


def test_datetime_from_string_with_format():
    d = datetime_from_string('01/01/2000 12:00:00', format='%d/%m/%Y %H:%M:%S', local=False)
    assert d.year == 2000
    assert d.month == 1
    assert d.day == 1
    assert d.hour == 12
    assert d.minute == 0
    assert d.second == 0
    assert d.microsecond == 0
    assert d.tzinfo is dt.timezone.utc


def test_datetime_from_string_local():
    d1 = now()
    d2 = datetime_from_string(dt.datetime.now().isoformat(), local=True)
    assert abs((d1 - d2).total_seconds()) < 1


def test_datetime_from_string_timezones():
    d1 = datetime_from_string('2000-01-01T12:00:00+00:00')
    d2 = datetime_from_string('2000-01-01T13:00:00+01:00')
    assert d1 == d2
    d3 = datetime_from_string('2000-01-01T11:00:00-01:00')
    assert d1 == d3