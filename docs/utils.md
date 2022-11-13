# Hextile Utilities

A collection of utility function and classes.

## Dictionary

The `Dictionary` class extends the native dictionary type to support attribute access, modification and deletion.

```pythono
>>> d = Dictionary(x=1)
>>> d.x
1
>>> d.y = 2
>>> del d.y
```

## Datetime

A collection of functions that work with datetimes and properly handle timezones. In the following descriptions, a normalized datetime is one with a UTC (Coordinated Universal Time) timezone, while naive datetimes (with no associated timezone) are assumed to reflect the local time.

- `now()` returns the current normalized datetime.

    ```python
    >>> now()
    datetime.datetime(2000, 1, 1, 12, 0, 0, 0, tzinfo=datetime.timezone.utc)
    ```

- `datetime(year, month, day[, hour[, minute[, second[, microsecond]]]])` returns an arbitrary normalized datetime.

    ```python
    >>> datetime(2000, 1, 1, 12)
    datetime.datetime(2000, 1, 1, 12, 0, 0, 0, tzinfo=datetime.timezone.utc)
    ```

- `datetime_to_timestamp(datetime)` returns the unix timestamp (microseconds since Epoch time) corresponding to the datetime;

    ```python
    >>> d = datetime(2000, 1, 1, 12)
    >>> datetime_to_timestamp(d)
    946728000.00 
    ```

- `datetime_from_timestamp(timestamp)` returns a normalized datetime corresponding to the unix timestamp (microseconds since Epoch time).

    ```python
    >>> timestamp_to_datetime(946728000.00)
    datetime.datetime(2000, 1, 1, 12, 0, 0, 0, tzinfo=datetime.timezone.utc)
    ```

- `datetime_to_string(datetime, format=None, local=True)` returns a string representing the datetime, either in the specified format or in ISO-8601. If `local` is `True`, the result reflects the local timezone; otherwise it reflects UTC.

    ```python
    # Assuming the local timezone is 1 hour ahead of UTC:
    >>> d = datetime(2000, 1, 1, 11)
    >>> datetime_to_string(d)
    '2000-01-01T11:00:00+01:00'
    >>> datetime_to_string(d, local=False)
    '2000-01-01T12:00:00+00:00'
    >>> datetime_to_string(d, format='%d/%m/%Y %H:%M:%S')
    '01/01/2000 11:00:00'
    ```

- `datetime_from_string(string, format=None, local=True)` returns a normalized datetime represented by the string, either in the specified format or in ISO-8601. If `local` is `True` and no timezone is specified in the string, it is understood to reflect the local time; otherwise it is understood to reflect UTC.

    ```python
    # Assuming the local timezone is 1 hour ahead of UTC:
    >>> string_to_datetime('2000-01-01T11:00:00')
    datetime.datetime(2000, 1, 1, 12, 0, 0, 0, tzinfo=datetime.timezone.utc)
    >>> string_to_datetime('2000-01-01T12:00:00', local=False)
    datetime.datetime(2000, 1, 1, 12, 0, 0, 0, tzinfo=datetime.timezone.utc)
    >>> string_to_datetime('31/12/1999 23:00:00', format='%d/%m/%Y %H:%M:%S')
    datetime.datetime(2000, 1, 1, 12, 0, 0, 0, tzinfo=datetime.timezone.utc)
    ```