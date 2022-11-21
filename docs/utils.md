# Hextile Utilities

A collection of utility function and classes.

- [Dictionary](#Dictionary)
- [Datetime](#Datetime)
- [URL](#URL)
- [Cached Property](#Cached-Property)
- [Execution](#Execution)
- [Colors](#Colors)

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

## URL

The `URL` class provides an easy way to parse a URL (according to RFC 1808).

```python
>>> url = URL.from_string('http://www.example.com/path')
>>> url.scheme
'http'
>>> url.host
'www.example.com'
>>> url.path
'/path'

>>> url = URL.from_string('scheme://user:1234@host:8000/path?x=1&y=2#fragment')
>>> url.scheme
'scheme'
>>> url.username
'user'
>>> url.password
'1234'
>>> url.host
'host'
>>> url.port
8000
>>> url.path
'/path'
>>> url.query
{'x': '1', 'y': '2'}
>>> url.fragment
'fragment'

# Note that the password is censored by default, and has to revealed explicitly:
>>> print(url)
scheme://user:********@host:8000/path?x=1&y=2#fragment
>>> print(url.reveal())
scheme://user:1234@host:8000/path?x=1&y=2#fragment
```

## Cached Property

The `cached_property` decorator turns a method into a property whose value is only computed once, and cached thereafter.

```python
>>> class A:
...     def __init__(self):
...         self.x = 0
...     @cached_property
...     def p(self):
...         self.x += 1
...         return self.x
>>> a = A()
>>> a.p
1
>>> a.p
1
```

A cached property can be refreshed, so as to remove its cached value and prompt a recomputation on the next access, by deleting it (if no value is cached, deleting it has no effect).

```python
>>> del a.p
>>> a.p
2
>>> del a.p
>>> del a.p # Also OK.
```

A cached property can be set, in which case its new value is cached.

```python
>>> a.p = 0
>>> a.p
0
>>> # Deletion has the same effect of uncaching the value and prompting recomputation:
>>> del a.p
>>> a.p
3
```

This class differs from `functools.cached_property` in two main ways: first, it supports augmenting the cached property setter, so if a value is assigned it has a chance to undergo some transformation before replacing the cached value.

```python
>>> class A:
...     @cached_property
...     def p(self):
...         return 1
...     @p.on_set
...     def p(self, x):
...         return x + 1
>>> a = A()
>>> a.p
1
>>> a.p = 2
>>> a.p
3
```

Second, it keeps track of all the class's cached properties, so it's possible to quickly and easily refresh entire objects, using an auto-added `refresh()` method (its name can be changed by setting `cached_property.refresh_method`; the name of the class attribute which stores all the class's cached properties, which defaults to `_cached_properties`, can be changed as well, by setting `cached_property.cached_properties_attribute`).

```python
>>> class A:
...     def __init__(self):
...         self.x = 0
...         self.y = 0
...     @cached_property
...     def p(self):
...         self.x += 1
...         return self.x
...     @cached_property
...     def q(self):
...         self.y += 1
...         return self.y
>>> a = A()
>>> a.p
1
>>> a.q
1
>>> a.refresh()
>>> a.p
2
>>> a.q
2
```

## Execution

The `Execution` class encapsulates the result of a command execution (similar to `subprocess.Popen` or `subprocess.run`), but provides a nicer interface to execute commands and manage their timeouts.

```python
>>> e = Execution.run('echo', 'Hello, world!')
>>> e.exit_code
0
>>> e.success
True
>>> e.stdout
b'Hello, world!\n'
>>> e.output
'Hello, world!'
>>> e.stderr
b''
>>> e.error
''
```

The `run(*command, stdin=None, timeout=None, sigterm_timeout=None)` also accepts:

- The standard input (as a string or bytes) to be passed to the executed command.

    ```python
    >>> e = Execution.run('cat', '-', stdin='Hello, world!')
    >>> e.stdout
    b'Hello, world!'
    ```

- A timeout in seconds, after which the process is terminated (defaults to `None`, which can be changed by setting `Execution.default_timeout`).

    ```python
    >>> e = Execution.run('sleep', 3, timeout=1)
    >>> e.exit_code
    -15 # Ends after ~1 second with SIGTERM.
    ```

- A SIGTERM timeout in seconds, after which the process is forcefully killed (in case it doesn't terminate properly; defaults to `3.0`, which can be changed by setting `Execution.default_sigterm_timeout`).

    ```python
    >>> e = Execution.run('bash', '-c', 'trap : SIGTERM; sleep 3', timeout=1)
    >>> e.exit_code
    0 # Takes the full 3 seconds.
    >>> e = Execution.run('bash', '-c', 'trap : SIGTERM; sleep 3', timeout=1, sigterm_timeout=1)
    >>> e.exit_code
    -9 # Ends after ~2 seconds with SIGKILL.
    ```

    Note that this means that when passing in a timeone, the process might actually run for up to `timeout + 3` seconds (or, more generally, `timeout + sigterm_timeout`) seconds. To get exact timeouts, either pass in `sigterm_timeout=0`, or set `Execution.default_sigterm_timeout` to `0`.

## Colors

A collection of functions to work with RGB, HSV, hexadecimal and XTERM colors.

RGB colors are represented as triplets of red, blue and green values, each of them an integer between 0 and 256; HSV colors are represented as triplets of hue, saturation and value, the hue an integer between 0 and 360 and the saturation and value integers between 0 and 100; hexadecimal colors are represented as a string of 6 hexadecimal colors, possibly starting with `#`; and XTERM colors are represented by a color ID, an integer between 0 and 256.

- `rgb_distance((r1, g1, b1), (r2, g2, b2))` receives two RGB colors and returns the distance between them; the value is not useful in itself, except that more similar colors have lower distances.

- `rgb_to_hsv((r, g, b))` receives an RGB color and returns an equivalent HSV color.

- `rgb_to_hex((r, g, b))` receives an RGB color and returns an equivalent hexadecimal color.

- `hsv_distance((h1, s1, v1), (h2, s2, v2))` receives two HSV colors and returns the distance between them; the value is not useful in itself, except that more similar colors have lower distances.

- `hsv_to_rgb((h, s, v))` receives an HSV color and returns an equivalent RGB color.

- `hsv_to_hex((h, s, v))` receives an HSV color and returns an equivalent hexadecimal color.

- `hex_distance(hex1, hex2)` receives two hexadecimal colors and returns the distance between them; the value is not useful in itself, except that more similar colors have lower distances.

- `hex_to_rgb(hex)` receives a hexadecimal color and returns an equivalent RGB color.

- `hex_to_hsv(hex)` receives a hexadecimal color and returns an equivalent HSV color.

- `xterm_to_rgb(xterm)` receives an XTERM color and returns an equivalent RGB color.

- `rgb_to_xterm((r, g, b))` receives an RGB color, and returns the closest equivalent XTERM color.

- `xterm_to_hsv(xterm)` receives an XTERM color and returns an equivalent HSV color.

- `hsv_to_xterm((h, s, v))` receives an HSV color, and returns the closest equivalent XTERM color.

- `xterm_to_hex(xterm)` receives an XTERM color and returns an equivalent hexadecimal color.

- `hex_to_xterm(hex)` receives a hexadecimal color and returns the closest equivalent XTERM color.

- `resolve_xterm(target)` receives a color as an XTERM ID, hexadecimal string, or RGB tuple and returns the closest equivalent XTERM color.