from .colors import (
    RGBType,
    HSVType,
    rgb_distance,
    hsv_distance,
    rgb_to_hex,
    hex_to_rgb,
)
from .xtermmap import xterm_rgb, xterm_hsv


def xterm_to_rgb(xterm: int) -> RGBType:
    _validate_xterm(xterm)
    return xterm_rgb[xterm]


def rgb_to_xterm(rgb: RGBType) -> int:
    closest_xterm, _ = min(xterm_rgb.items(), key=lambda item: rgb_distance(rgb, item[1]))
    return closest_xterm


def xterm_to_hsv(xterm: int) -> HSVType:
    _validate_xterm(xterm)
    return xterm_hsv[xterm]


def hsv_to_xterm(hsv: HSVType) -> int:
    closest_xterm, _ = min(xterm_hsv.items(), key=lambda item: hsv_distance(hsv, item[1]))
    return closest_xterm


def xterm_to_hex(xterm: int) -> str:
    rgb = xterm_to_rgb(xterm)
    return rgb_to_hex(rgb)


def hex_to_xterm(hex: str) -> int:
    rgb = hex_to_rgb(hex)
    return rgb_to_xterm(rgb)


def resolve_xterm(target: int|str|RGBType) -> int:
    if isinstance(target, int):
        _validate_xterm(target)
        return target
    if isinstance(target, str):
        return hex_to_xterm(target)
    if isinstance(target, tuple) and len(target) == 3:
        return rgb_to_xterm(target)
    raise ValueError(f'invalid color {target!r} (expected an xterm ID integer, a hexdecimal color string, or an RGB color tuple of 3 integers between 0 and 256)')


def _validate_xterm(xterm: int) -> None:
    if not 0 <= xterm < 256 or int(xterm) != xterm:
        raise ValueError(f'invalid xterm {xterm!r} (expected an integer between 0 and 256)')