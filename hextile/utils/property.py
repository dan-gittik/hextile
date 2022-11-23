from __future__ import annotations
from typing import Any, Callable, Generic, Type, TypeVar

import threading


T = TypeVar('T')
GetterType = Callable[[object], T]
SetterType = Callable[[object, T], None]
DeleterType = Callable[[object], None]
OnSetType = Callable[[object, T], T]
OnDeleteType = Callable[[object], None]
undefined = object()


class property(Generic[T]):

    cached_properties_list = '_cached_properties'
    clear_cache_method = 'clear_cache'

    default_readonly = False
    default_cached = False
    default_threadsafe = False

    def __init__(
            self,
            getter: GetterType = None,
            setter: SetterType = None,
            deleter: DeleterType = None,
            /,
            *,
            readonly: bool = None,
            cached: bool = None,
            threadsafe: bool = None,
    ):
        if readonly is None:
            readonly = self.default_readonly
        if cached is None:
            cached = self.default_cached
        if threadsafe is None:
            threadsafe = self.default_threadsafe
        self.name = getter and getter.__name__
        self.readonly = readonly
        self.cached = cached
        self.threadsafe = threadsafe
        self._getter = getter
        self._setter = setter
        self._deleter = deleter
        self._on_set: OnSetType = None
        self._on_delete: OnDeleteType = None
        self._lock = threading.Lock()
    
    def __str__(self):
        return f'property {self.name!r}'
    
    def __repr__(self):
        return f'<{self}>'
    
    def __call__(self, getter: GetterType) -> property:
        self._getter = getter
        if self.name is None:
            self.name = getter.__name__
        return self

    def __set_name__(self, owner: Type, name: str):
        self.name = name
        if self.cached:
            cached_properties = getattr(owner, self.cached_properties_list, None)
            if cached_properties is None:
                cached_properties = []
                setattr(owner, self.cached_properties_list, cached_properties)
                setattr(owner, self.clear_cache_method, clear_cache)
            cached_properties.append(name)
    
    def __get__(self, instance: object, owner: Type = None) -> T:
        if instance is None:
            return self
        try:
            if self.threadsafe:
                self._lock.acquire()
            value = instance.__dict__.get(self.name, undefined)
            if value is undefined:
                value = self._getter(instance)
                if self.cached:
                    instance.__dict__[self.name] = value
            return value
        finally:
            if self.threadsafe:
                self._lock.release()
    
    def __set__(self, instance: object, value: Any) -> None:
        if self.readonly:
            raise TypeError(f'{self.name} is a read-only property, and cannot be set')
        try:
            if self.threadsafe:
                self._lock.acquire()
            if self._on_set:
                value = self._on_set(instance, value)
            if self._setter:
                self._setter(instance, value)
            else:
                instance.__dict__[self.name] = value
        finally:
            if self.threadsafe:
                self._lock.release()
    
    def __delete__(self, instance: object) -> None:
        if self.readonly:
            raise TypeError(f'{self.name} is a read-only property, and cannot be deleted')
        try:
            if self.threadsafe:
                self._lock.acquire()
            if self._on_delete:
                self._on_delete(instance)
            if self._deleter:
                self._deleter(instance)
            else:
                instance.__dict__.pop(self.name, None)
        finally:
            if self.threadsafe:
                self._lock.release()
    
    def setter(self, setter: SetterType) -> property:
        if self.cached:
            raise TypeError(f'{self.name} is a cached property, and cannot have a custom setter')
        self._setter = setter
        return self
    
    def on_set(self, on_set: OnSetType) -> property:
        self._on_set = on_set
        return self
    
    def deleter(self, deleter: DeleterType) -> property:
        if self.cached:
            raise TypeError(f'{self.name} is a cached property, and cannot have a custom deleter')
        self._deleter = deleter
        return self
    
    def on_delete(self, on_delete: OnDeleteType) -> property:
        self._on_delete = on_delete
        return self


def clear_cache(self) -> None:
    for name in getattr(self.__class__, property.cached_properties_list, []):
        self.__dict__.pop(name, None)