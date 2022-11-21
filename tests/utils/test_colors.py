import pytest

from hextile.utils import (
    validate_rgb,
    rgb_distance,
    rgb_to_hsv,
    rgb_to_hex,
    validate_hsv,
    hsv_distance,
    hsv_to_rgb,
    hsv_to_hex,
    validate_hex,
    hex_distance,
    hex_to_rgb,
    hex_to_hsv,
)


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
gray_hex = '#808080'
red_hex = '#ff0000'
green_hex = '#00ff00'
yellow_hex = '#ffff00'


def test_validate_rgb():
    validate_rgb(black_rgb)
    validate_rgb(white_rgb)
    with pytest.raises(ValueError, match=r'invalid RGB color \(-1, 0, 0\): invalid red value -1 \(expected an integer between 0 and 256\)'):
        validate_rgb((-1, 0, 0))
    with pytest.raises(ValueError, match=r'invalid RGB color \(256, 0, 0\): invalid red value 256 \(expected an integer between 0 and 256\)'):
        validate_rgb((256, 0, 0))
    with pytest.raises(ValueError, match=r'invalid RGB color \(127.5, 0, 0\): invalid red value 127.5 \(expected an integer between 0 and 256\)'):
        validate_rgb((127.5, 0, 0))


def test_rgb_distance():
    assert rgb_distance(black_rgb, white_rgb) == rgb_distance(white_rgb, black_rgb)
    assert rgb_distance(black_rgb, gray_rgb) < rgb_distance(black_rgb, white_rgb)
    assert rgb_distance(red_rgb, yellow_rgb) < rgb_distance(red_rgb, green_rgb)


def test_rgb_to_hsv():
    assert rgb_to_hsv(black_rgb) == black_hsv
    assert rgb_to_hsv(white_rgb) == white_hsv
    assert rgb_to_hsv(gray_rgb) == gray_hsv
    assert rgb_to_hsv(red_rgb) == red_hsv
    assert rgb_to_hsv(green_rgb) == green_hsv
    assert rgb_to_hsv(yellow_rgb) == yellow_hsv


def test_rgb_to_hex():
    assert rgb_to_hex(black_rgb) == black_hex
    assert rgb_to_hex(white_rgb) == white_hex
    assert rgb_to_hex(gray_rgb) == gray_hex
    assert rgb_to_hex(red_rgb) == red_hex
    assert rgb_to_hex(green_rgb) == green_hex
    assert rgb_to_hex(yellow_rgb) == yellow_hex


def test_validate_hsv():
    validate_hsv(black_hsv)
    validate_hsv(white_hsv)
    with pytest.raises(ValueError, match=r'invalid HSV color \(-1, 0, 0\): invalid hue -1 \(expected an integer between 0 and 360\)'):
        validate_hsv((-1, 0, 0))
    with pytest.raises(ValueError, match=r'invalid HSV color \(360, 0, 0\): invalid hue 360 \(expected an integer between 0 and 360\)'):
        validate_hsv((360, 0, 0))
    with pytest.raises(ValueError, match=r'invalid HSV color \(0.5, 0, 0\): invalid hue 0.5 \(expected an integer between 0 and 360\)'):
        validate_hsv((0.5, 0, 0))
    with pytest.raises(ValueError, match=r'invalid HSV color \(0, -1, 0\): invalid saturation -1 \(expected an integer between 0 and 100\)'):
        validate_hsv((0, -1, 0))
    with pytest.raises(ValueError, match=r'invalid HSV color \(0, 101, 0\): invalid saturation 101 \(expected an integer between 0 and 100\)'):
        validate_hsv((0, 101, 0))
    with pytest.raises(ValueError, match=r'invalid HSV color \(0, 0.5, 0\): invalid saturation 0.5 \(expected an integer between 0 and 100\)'):
        validate_hsv((0, 0.5, 0))
    with pytest.raises(ValueError, match=r'invalid HSV color \(0, 0, -1\): invalid value -1 \(expected an integer between 0 and 100\)'):
        validate_hsv((0, 0, -1))
    with pytest.raises(ValueError, match=r'invalid HSV color \(0, 0, 101\): invalid value 101 \(expected an integer between 0 and 100\)'):
        validate_hsv((0, 0, 101))
    with pytest.raises(ValueError, match=r'invalid HSV color \(0, 0, 0.5\): invalid value 0.5 \(expected an integer between 0 and 100\)'):
        validate_hsv((0, 0, 0.5))


def test_hsv_distance():
    assert hsv_distance(black_hsv, white_hsv) == hsv_distance(white_hsv, black_hsv)
    assert hsv_distance(black_hsv, gray_hsv) < hsv_distance(black_hsv, white_hsv)
    assert hsv_distance(red_hsv, yellow_hsv) < hsv_distance(red_hsv, green_hsv)


def test_hsv_to_rgb():
    assert hsv_to_rgb(black_hsv) == black_rgb
    assert hsv_to_rgb(white_hsv) == white_rgb
    assert hsv_to_rgb(gray_hsv) == gray_rgb
    assert hsv_to_rgb(red_hsv) == red_rgb
    assert hsv_to_rgb(green_hsv) == green_rgb
    assert hsv_to_rgb(yellow_hsv) == yellow_rgb


def test_hsv_to_hex():
    assert hsv_to_hex(black_hsv) == black_hex
    assert hsv_to_hex(white_hsv) == white_hex
    assert hsv_to_hex(gray_hsv) == gray_hex
    assert hsv_to_hex(red_hsv) == red_hex
    assert hsv_to_hex(green_hsv) == green_hex
    assert hsv_to_hex(yellow_hsv) == yellow_hex


def test_validate_hex():
    validate_hex(black_hex)
    validate_hex(white_hex)
    validate_hex(black_hex[1:])
    validate_hex(white_hex[1:])
    with pytest.raises(ValueError, match=r"invalid hexadecimal color '#fffff' \(expected 6 hexdecimal characters, possibly starting with #\)"):
        validate_hex('#fffff')
    with pytest.raises(ValueError, match=r"invalid hexadecimal color '#fffffff' \(expected 6 hexdecimal characters, possibly starting with #\)"):
        validate_hex('#fffffff')
    with pytest.raises(ValueError, match=r"invalid hexadecimal color '#fffffg' \(expected 6 hexdecimal characters, possibly starting with #\)"):
        validate_hex('#fffffg')
    with pytest.raises(ValueError, match=r"invalid hexadecimal color '\$ffffff' \(expected 6 hexdecimal characters, possibly starting with #\)"):
        validate_hex('$ffffff')


def test_hex_distance():
    assert hex_distance(black_hex, white_hex) == hex_distance(white_hex, black_hex)
    assert hex_distance(black_hex, gray_hex) < hex_distance(black_hex, white_hex)
    assert hex_distance(red_hex, yellow_hex) < hex_distance(red_hex, green_hex)


def test_hex_to_rgb():
    assert hex_to_rgb(black_hex) == black_rgb
    assert hex_to_rgb(white_hex) == white_rgb
    assert hex_to_rgb(gray_hex) == gray_rgb
    assert hex_to_rgb(red_hex) == red_rgb
    assert hex_to_rgb(green_hex) == green_rgb
    assert hex_to_rgb(yellow_hex) == yellow_rgb


def test_hex_to_hsv():
    assert hex_to_hsv(black_hex) == black_hsv
    assert hex_to_hsv(white_hex) == white_hsv
    assert hex_to_hsv(gray_hex) == gray_hsv
    assert hex_to_hsv(red_hex) == red_hsv
    assert hex_to_hsv(green_hex) == green_hsv
    assert hex_to_hsv(yellow_hex) == yellow_hsv