from hextile.utils import cached_property


def test_cached_property():
    class A:
        def __init__(self):
            self.x = 0
        @cached_property
        def p(self):
            self.x += 1
            return self.x
    a = A()
    assert a.p == 1
    assert a.p == 1


def test_cached_property_from_class():
    class A:
        @cached_property
        def p(self):
            pass
    assert isinstance(A.p, cached_property)
    assert A.p.name == 'p'
    assert A.p.name in A._cached_properties
    assert A.refresh
    assert str(A.p) == "cached property 'p'"
    assert repr(A.p) == "<cached property 'p'>"


def test_cached_property_set():
    class A:
        @cached_property
        def p(self):
            return 1
    a = A()
    assert a.p == 1
    a.p = 2
    assert a.p == 2


def test_cached_property_on_set():
    class A:
        @cached_property
        def p(self):
            return 1
        @p.on_set
        def p(self, x):
            return x + 1
    a = A()
    a.p = 2
    assert a.p == 3
    a.p = 4
    assert a.p == 5


def test_cached_property_delete():
    class A:
        def __init__(self):
            self.x = 0
        @cached_property
        def p(self):
            self.x += 1
            return self.x
    a = A()
    assert a.p == 1
    assert a.p == 1
    del a.p
    assert a.p == 2
    assert a.p == 2


def test_cached_property_unset():
    class A:
        @cached_property
        def p(self):
            return 1
    a = A()
    a.p = 2
    assert a.p == 2
    del a.p
    assert a.p == 1


def test_cached_property_multiple_delete():
    class A:
        @cached_property
        def p(self):
            return 1
    a = A()
    del a.p
    assert a.p == 1
    del a.p
    assert a.p == 1


def test_cached_property_refresh():
    class A:
        def __init__(self):
            self.x = 0
            self.y = 0
        @cached_property
        def p(self):
            self.x += 1
            return self.x
        @cached_property
        def q(self):
            self.y += 1
            return self.y
    a = A()
    assert a.p == 1
    assert a.p == 1
    assert a.q == 1
    assert a.q == 1
    a.refresh()
    assert a.p == 2
    assert a.p == 2
    assert a.q == 2
    assert a.q == 2