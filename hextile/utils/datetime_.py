import datetime as dt


default_local = True


def now() -> dt.datetime:
    return dt.datetime.now().astimezone(dt.timezone.utc)


def datetime(
        year: int,
        month: int,
        day: int,
        hour: int = None,
        minute: int = None,
        second: int = None,
        microsecond: int = None,
) -> dt.datetime:
    args = filter(None, (year, month, day, hour, minute, second, microsecond))
    return dt.datetime(*args, tzinfo=dt.timezone.utc)


def datetime_to_timestamp(datetime: dt.datetime) -> float:
    if datetime.tzinfo is None:
        datetime = datetime.astimezone()
    return datetime.timestamp()


def datetime_from_timestamp(timestamp: float) -> dt.datetime:
    return dt.datetime.fromtimestamp(timestamp, dt.timezone.utc)


def datetime_to_string(datetime: dt.datetime, format: str = None, local: bool = None) -> str:
    if local is None:
        local = default_local
    if datetime.tzinfo is None:
        datetime = datetime.astimezone(dt.timezone.utc)
    if local:
        datetime = datetime.astimezone()
    if format:
        return datetime.strftime(format)
    else:
        return datetime.isoformat()


def datetime_from_string(string: str, format: str = None, local: bool = None) -> dt.datetime:
    if local is None:
        local = default_local
    if format:
        datetime = dt.datetime.strptime(string, format)
    else:
        datetime = dt.datetime.fromisoformat(string)
    if datetime.tzinfo is None:
        if local:
            datetime = datetime.astimezone()
        else:
            datetime = datetime.replace(tzinfo=dt.timezone.utc)
    return datetime.astimezone(dt.timezone.utc)