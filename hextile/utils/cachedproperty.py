from __future__ import annotations
from typing import Any, Callable, Type, TypeVar


class CachedProperty:

    cached_properties_attribute = '_cached_properties'
    refresh_method = 'refresh'

    def __init__(self, getter: GetterType):
        self.getter = getter
        self.name = self.getter.__name__
        self.setter: SetterType = None
    
    def __str__(self):
        return f'cached property {self.name!r}'
    
    def __repr__(self):
        return f'<{self}>'

    def __set_name__(self, owner: Type, name: str):
        self.name = name
        cached_properties = getattr(owner, self.cached_properties_attribute, None)
        if cached_properties is None:
            cached_properties = []
            setattr(owner, self.cached_properties_attribute, cached_properties)
            setattr(owner, self.refresh_method, refresh)
        cached_properties.append(name)
    
    def __get__(self, instance: object, owner: Type):
        if instance is None:
            return self
        if self.name not in instance.__dict__:
            instance.__dict__[self.name] = self.getter(instance)
        return instance.__dict__[self.name]
    
    def __set__(self, instance: object, value: Any) -> None:
        if self.setter is not None:
            value = self.setter(instance, value)
        instance.__dict__[self.name] = value
    
    def __delete__(self, instance: object) -> None:
        instance.__dict__.pop(self.name, None)
    
    def on_set(self, setter: SetterType) -> CachedProperty:
        self.setter = setter
        return self


def refresh(self: object) -> None:
    for name in getattr(self.__class__, CachedProperty.cached_properties_attribute, []):
        self.__dict__.pop(name, None)


T = TypeVar('T')
GetterType = Callable[[object], T]
SetterType = Callable[[object, Any], T]


cached_property = CachedProperty