import pytest

from hextile.utils import (
    validate_xterm,
    xterm_to_rgb,
    rgb_to_xterm,
    xterm_to_hsv,
    hsv_to_xterm,
    xterm_to_hex,
    hex_to_xterm,
    resolve_xterm,
)


black_xterm = 0
white_xterm = 15
gray_xterm = 1
red_xterm = 9
green_xterm = 10
yellow_xterm = 11

black_rgb = 0, 0, 0
white_rgb = 255, 255, 255
gray_rgb = 128, 128, 128
red_rgb = 255, 0, 0
green_rgb = 0, 255, 0
yellow_rgb = 255, 255, 0

black_hsv = 0, 0, 0
white_hsv = 0, 0, 100
gray_hsv = 0, 0, 50
red_hsv = 0, 100, 100
green_hsv = 120, 100, 100
yellow_hsv = 60, 100, 100

black_hex = '#000000'
white_hex = '#ffffff'
gray_hex = '#888888'
red_hex = '#ff0000'
green_hex = '#00ff00'
yellow_hex = '#ffff00'


def test_validate_xterm():
    validate_xterm(black_xterm)
    validate_xterm(white_xterm)
    with pytest.raises(ValueError, match=r'invalid xterm -1 \(expected an integer between 0 and 256\)'):
        validate_xterm(-1)
    with pytest.raises(ValueError, match=r'invalid xterm 256 \(expected an integer between 0 and 256\)'):
        validate_xterm(256)
    with pytest.raises(ValueError, match=r'invalid xterm 127.5 \(expected an integer between 0 and 256\)'):
        validate_xterm(127.5)


def test_xterm_to_rgb():
    assert xterm_to_rgb(black_xterm) == black_rgb
    assert xterm_to_rgb(white_xterm) == white_rgb
    assert xterm_to_rgb(red_xterm) == red_rgb
    assert xterm_to_rgb(green_xterm) == green_rgb
    assert xterm_to_rgb(yellow_xterm) == yellow_rgb


def test_rgb_to_xterm():
    assert rgb_to_xterm(black_rgb) == black_xterm
    assert rgb_to_xterm(white_rgb) == white_xterm
    assert rgb_to_xterm(red_rgb) == red_xterm
    assert rgb_to_xterm(green_rgb) == green_xterm
    assert rgb_to_xterm(yellow_rgb) == yellow_xterm


def test_rgb_to_xterm_close():
    r, g, b = red_rgb
    assert rgb_to_xterm((r - 1, g, b)) == red_xterm
    assert rgb_to_xterm((r, g + 1, b)) == red_xterm
    assert rgb_to_xterm((r, g, b + 1)) == red_xterm


def test_xterm_to_hsv():
    assert xterm_to_hsv(black_xterm) == black_hsv
    assert xterm_to_hsv(white_xterm) == white_hsv
    assert xterm_to_hsv(red_xterm) == red_hsv
    assert xterm_to_hsv(green_xterm) == green_hsv
    assert xterm_to_hsv(yellow_xterm) == yellow_hsv


def test_hsv_to_xterm():
    assert hsv_to_xterm(black_hsv) == black_xterm
    assert hsv_to_xterm(white_hsv) == white_xterm
    assert hsv_to_xterm(red_hsv) == red_xterm
    assert hsv_to_xterm(green_hsv) == green_xterm
    assert hsv_to_xterm(yellow_hsv) == yellow_xterm


def test_hsv_to_xterm_close():
    h, s, v = red_hsv
    assert hsv_to_xterm((h + 1, s, v)) == red_xterm
    assert hsv_to_xterm((h, s - 1, v)) == red_xterm
    assert hsv_to_xterm((h, s, v - 1)) == red_xterm


def test_xterm_to_hex():
    assert xterm_to_hex(black_xterm) == black_hex
    assert xterm_to_hex(white_xterm) == white_hex
    assert xterm_to_hex(red_xterm) == red_hex
    assert xterm_to_hex(green_xterm) == green_hex
    assert xterm_to_hex(yellow_xterm) == yellow_hex


def test_hex_to_xterm():
    assert hex_to_xterm(black_hex) == black_xterm
    assert hex_to_xterm(white_hex) == white_xterm
    assert hex_to_xterm(red_hex) == red_xterm
    assert hex_to_xterm(green_hex) == green_xterm
    assert hex_to_xterm(yellow_hex) == yellow_xterm


def test_hex_to_xterm_close():
    assert hex_to_xterm(f'#fe0000') == red_xterm
    assert hex_to_xterm(f'#ff0100') == red_xterm
    assert hex_to_xterm(f'#ff0001') == red_xterm


def test_resolve_xterm():
    assert resolve_xterm(red_xterm) == red_xterm
    assert resolve_xterm(red_hex) == red_xterm
    assert resolve_xterm(red_rgb) == red_xterm
    with pytest.raises(ValueError, match=r'invalid color 1.0 \(expected an xterm ID integer, a hexdecimal color string, or an RGB color tuple of 3 integers between 0 and 256\)'):
        resolve_xterm(1.0)
    with pytest.raises(ValueError, match=r'invalid color (1, 2) \(expected an xterm ID integer, a hexdecimal color string, or an RGB color tuple of 3 integers between 0 and 256\)'):
        resolve_xterm((1, 2))