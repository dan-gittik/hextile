import pytest

from hextile.utils import Dictionary


@pytest.fixture
def d():
    return Dictionary(x=1, y=2)


def test_getattr(d):
    assert d.x == 1
    assert d.y == 2
    with pytest.raises(AttributeError):
        d.z


def test_setattr(d):
    d.z = 3
    assert d.z == 3
    d.x = 0
    assert d.x == 0


def test_delattr(d):
    assert 'x' in d
    del d.x
    assert 'x' not in d
    with pytest.raises(AttributeError):
        del d.z
    with pytest.raises(AttributeError):
        del d.x