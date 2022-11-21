import math
import re


RGBType = tuple[int, int, int]
HSVType = tuple[int, int, int]


_rgb_fields = 'red', 'green', 'blue'
_hsv_fields = 'saturation', 'value'
_hex_regex = re.compile(r'''
    ^
    \#?
    ([0-9a-f]{2})
    ([0-9a-f]{2})
    ([0-9a-f]{2})
    $
''', flags=re.VERBOSE | re.IGNORECASE)
 

def rgb_distance(rgb1: RGBType, rgb2: RGBType) -> float:
    _validate_rgb(rgb1)
    _validate_rgb(rgb2)
    r1, g1, b1 = rgb1
    r2, g2, b2 = rgb2
    return (
        ((r2 - r1) * 0.3) ** 2
      + ((g2 - g1) * 0.59) ** 2
      + ((b2 - b1) * 0.11) ** 2
    ) ** 0.5


def rgb_to_hsv(rgb: RGBType) -> HSVType:
    _validate_rgb(rgb)
    r, g, b = rgb
    r /= 255
    g /= 255
    b /= 255
    m = min(r, g, b)
    M = max(r, g, b)
    if M == 0:
        return 0, 0, 0
    d = M - m
    if d == 0:
        return 0, 0, round(M * 100)
    v = M
    s = d / M
    if r == M:
        h = (g - b) / d
    elif g == M:
        h = 2 + (b - r) / d
    else:
        h = 4 + (r - g) / d
    h *= 60
    if h < 0:
        h += 360
    return round(h), round(s * 100), round(v * 100)


def rgb_to_hex(rgb: RGBType) -> str:
    _validate_rgb(rgb)
    r, g, b = rgb
    return f'#{r:02x}{g:02x}{b:02x}'


def hsv_distance(hsv1: HSVType, hsv2: HSVType) -> float:
    _validate_hsv(hsv1)
    _validate_hsv(hsv2)
    h1, s1, v1 = hsv1
    h2, s2, v2 = hsv2
    h1 = h1 / 360 * 2 * math.pi
    h2 = h2 / 360 * 2 * math.pi
    s1 /= 100
    s2 /= 100
    v1 /= 100
    v2 /= 100
    return (
        (math.sin(h1) * s1 * v1 - math.sin(h2) * s2 * v2) ** 2
      + (math.cos(h1) * s1 * v1 - math.cos(h2) * s2 * v2) ** 2
      + (v1 - v2) ** 2
    ) ** 0.5


def hsv_to_rgb(hsv: HSVType) -> RGBType:
    _validate_hsv(hsv)
    h, s, v = hsv
    s /= 100
    v /= 100
    if s == 0:
        v = round(255 * v)
        return v, v, v
    h /= 60
    i = math.floor(h)
    f = h - i
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return round(r * 255), round(g * 255), round(b * 255)


def hsv_to_hex(hsv: HSVType) -> str:
    rgb = hsv_to_rgb(hsv)
    return rgb_to_hex(rgb)


def hex_distance(hex1: str, hex2: str) -> float:
    rgb1 = hex_to_rgb(hex1)
    rgb2 = hex_to_rgb(hex2)
    return rgb_distance(rgb1, rgb2)


def hex_to_rgb(hex: str) -> RGBType:
    match = _hex_regex.match(hex)
    if not match:
        raise ValueError(f'invalid hexadecimal color {hex!r} (expected 6 hexdecimal characters, possibly starting with #)')
    return tuple(int(group, 16) for group in match.groups())


def hex_to_hsv(hex: str) -> HSVType:
    rgb = hex_to_rgb(hex)
    return rgb_to_hsv(rgb)


def _validate_rgb(rgb: RGBType) -> None:
    for color, name in zip(rgb, _rgb_fields):
        if not 0 <= color < 256 or int(color) != color:
            raise ValueError(f'invalid RGB color {rgb!r}: invalid {name} value {color!r} (expected an integer between 0 and 256)')


def _validate_hsv(hsv: HSVType) -> None:
    h, s, v = hsv
    if not 0 <= h < 360 or int(h) != h:
        raise ValueError(f'invalid HSV color {hsv!r}: invalid hue {h!r} (expected an integer between 0 and 360)')
    for value, name in zip((s, v), _hsv_fields):
        if not 0 <= value <= 100 or int(value) != value:
            raise ValueError(f'invalid HSV color {hsv!r}: invalid {name} {value!r} (expected an integer between 0 and 100)')