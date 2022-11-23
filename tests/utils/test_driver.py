import pytest

from hextile.utils import Driver


class test_driver():
    class MyDriver(Driver):
        label = 'my'
        def f(self):
            raise NotImplementedError()
    class DriverA(MyDriver):
        scheme = 'a'
        def f(self):
            return 1
    class DriverB(MyDriver):
        scheme = 'b'
        def f(self):
            return 2
    d = MyDriver.from_url('a://')
    assert d.url == 'a://'
    assert str(d) == 'a my driver at a://'
    assert repr(d) == "DriverA('a://')"
    assert d.f() == 1
    d = MyDriver.from_url('b://')
    assert d.url == 'b://'
    assert str(d) == 'b my driver at b://'
    assert repr(d) == "DriverB('b://')"
    assert d.f() == 2


def test_on_init():
    init = []
    class MyDriver(Driver):
        label = 'my'
    class DriverA(MyDriver):
        scheme = 'a'
        def on_init(self):
            init.append(1)
    d = MyDriver.from_url('a://')
    assert init == [1]


def test_no_label():
    with pytest.raises(TypeError, match=r'invalid driver base class MyDriver: label is not defined'):
        class MyDriver(Driver):
            pass


def test_no_scheme():
    class MyDriver(Driver):
        label = 'my'
    with pytest.raises(TypeError, match=r'invalid driver class DriverA: scheme is not defined'):
        class DriverA(MyDriver):
            pass


def test_duplicate_scheme():
    class MyDriver(Driver):
        label = 'my'
    class DriverA(MyDriver):
        scheme = 'a'
    with pytest.raises(TypeError, match=r"invalid driver class DriverB: scheme 'a' is already defined \(in class DriverA\)"):
        class DriverB(MyDriver):
            scheme = 'a'