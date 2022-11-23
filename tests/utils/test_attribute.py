import threading
import time

import pytest

from hextile.utils import attribute


def test_attribute():
    class A:
        @attribute
        def p(self):
            pass
    assert isinstance(A.p, attribute)
    assert A.p.name == 'p'
    assert str(A.p) == "attribute 'p'"
    assert repr(A.p) == "<attribute 'p'>"


def test_get():
    class A:
        @attribute
        def p(self):
            return 1
    a = A()
    assert a.p == 1


def test_set():
    class A:
        @attribute
        def p(self):
            return 1
    a = A()
    a.p = 2
    assert a.p == 2


def test_setter():
    set = []
    class A:
        @attribute
        def p(self):
            return 1
        @p.setter
        def p(self, value):
            set.append(value)
    a = A()
    a.p = 2
    assert a.p == 1
    assert set == [2]


def test_on_set():
    class A:
        @attribute
        def p(self):
            return 1
        @p.on_set
        def p(self, value):
            return value + 1
    a = A()
    a.p = 2
    assert a.p == 3


def test_deleter():
    deleted = []
    class A:
        @attribute
        def p(self):
            return 1
        @p.deleter
        def p(self):
            deleted.append(self.p)
    a = A()
    del a.p
    assert a.p == 1
    a.p = 2
    del a.p
    assert a.p == 2
    assert deleted == [1, 2]


def test_on_delete():
    deleted = []
    class A:
        @attribute
        def p(self):
            return 1
        @p.on_delete
        def p(self):
            deleted.append(self.p)
    a = A()
    del a.p
    assert a.p == 1
    a.p = 2
    del a.p
    assert a.p == 1
    assert deleted == [1, 2]


def test_readonly():
    class A:
        @attribute(readonly=True)
        def p(self):
            return 1
    a = A()
    assert a.p == 1
    with pytest.raises(TypeError, match=r"p is a read-only attribute, and cannot be set"):
        a.p = 2
    with pytest.raises(TypeError, match=r"p is a read-only attribute, and cannot be deleted"):
        del a.p


def test_cached():
    class A:
        def __init__(self):
            self.x = 0
        @attribute(cached=True)
        def p(self):
            self.x += 1
            return self.x
    a = A()
    assert a.p == 1
    assert a.p == 1


def test_cached_attribute():
    class A:
        @attribute(cached=True)
        def p(self):
            return 1
    assert A.p.name in A._cached_attributes
    assert A.clear_cache


def test_cached_set():
    class A:
        @attribute(cached=True)
        def p(self):
            return 1
    a = A()
    a.p = 2
    assert a.p == 2


def test_cached_setter():
    with pytest.raises(TypeError, match=r'p is a cached attribute, and cannot have a custom setter'):
        class A:
            @attribute(cached=True)
            def p(self):
                return 1
            @p.setter
            def p(self, value):
                pass


def test_cached_on_set():
    class A:
        def __init__(self):
            self.x = 0
        @attribute(cached=True)
        def p(self):
            self.x += 1
            return self.x
        @p.on_set
        def p(self, x):
            return x + 1
    a = A()
    a.p = 2
    assert a.p == 3
    assert a.p == 3


def test_cached_deleter():
    with pytest.raises(TypeError, match=r'p is a cached attribute, and cannot have a custom deleter'):
        class A:
            @attribute(cached=True)
            def p(self):
                return 1
            @p.deleter
            def p(self):
                pass


def test_cached_on_delete():
    deleted = []
    class A:
        @attribute(cached=True)
        def p(self):
            return 1
        @p.on_delete
        def p(self):
            deleted.append(self.p)
    a = A()
    del a.p
    a.p = 2
    del a.p
    assert a.p == 1
    assert deleted == [1, 2]


def test_clear_cache():
    class A:
        def __init__(self):
            self.x = 0
            self.y = 0
        @attribute(cached=True)
        def p(self):
            self.x += 1
            return self.x
        @attribute(cached=True)
        def q(self):
            self.y += 1
            return self.y
    a = A()
    assert a.p == 1
    assert a.p == 1
    assert a.q == 1
    assert a.q == 1
    a.clear_cache()
    assert a.p == 2
    assert a.p == 2
    assert a.q == 2
    assert a.q == 2


def test_threadsafe_get():
    class A:
        def __init__(self):
            self.x = 0
        @attribute
        def p(self):
            x = self.x
            time.sleep(0.1)
            self.x = x + 1
            return x
    a = A()
    t1 = threading.Thread(target=lambda: a.p)
    t2 = threading.Thread(target=lambda: a.p)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert a.p == 1
    class A:
        def __init__(self):
            self.x = 0
        @attribute(threadsafe=True)
        def p(self):
            x = self.x
            time.sleep(0.1)
            self.x = x + 1
            return x
    a = A()
    t1 = threading.Thread(target=lambda: a.p)
    t2 = threading.Thread(target=lambda: a.p)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert a.p == 2


def test_threadsafe_set():
    class A:
        def __init__(self):
            self.x = 0
        @attribute
        def p(self):
            return self.x
        @p.setter
        def p(self, x):
            time.sleep(0.1)
            self.x = x
    def inc():
        a.p = a.p + 1
    a = A()
    t1 = threading.Thread(target=inc)
    t2 = threading.Thread(target=inc)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert a.p == 1
    class A:
        def __init__(self):
            self.x = 0
        @attribute(threadsafe=True)
        def p(self):
            return self.x
        @p.setter
        def p(self, x):
            time.sleep(0.1)
            self.x = x
    a = A()
    t1 = threading.Thread(target=inc)
    t2 = threading.Thread(target=inc)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert a.p == 2


def test_threadsafe_delete():
    class A:
        def __init__(self):
            self.x = 2
        @attribute
        def p(self):
            return self.x
        @p.deleter
        def p(self):
            x = self.x
            time.sleep(0.1)
            self.x = x - 1
    def delete():
        del a.p
    a = A()
    t1 = threading.Thread(target=delete)
    t2 = threading.Thread(target=delete)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert a.p == 1
    class A:
        def __init__(self):
            self.x = 2
        @attribute(threadsafe=True)
        def p(self):
            return self.x
        @p.deleter
        def p(self):
            x = self.x
            time.sleep(0.1)
            self.x = x - 1
    a = A()
    t1 = threading.Thread(target=delete)
    t2 = threading.Thread(target=delete)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert a.p == 0