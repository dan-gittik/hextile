from __future__ import annotations
from typing import Any, Callable, Generic, Type, TypeVar

import threading


T = TypeVar('T')
GetterType = Callable[..., T]
SetterType = Callable[..., None]
DeleterType = Callable[..., None]
OnSetType = Callable[[object, T], T]
OnDeleteType = Callable[[object], None]
undefined = object()


class attribute(Generic[T]):

    cached_attributes_list = '_cached_attributes'
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
        return f'attribute {self.name!r}'
    
    def __repr__(self):
        return f'<{self}>'
    
    def __call__(self, getter: GetterType) -> attribute:
        self._getter = getter
        if self.name is None:
            self.name = getter.__name__
        return self

    def __set_name__(self, owner: Type, name: str):
        self.name = name
        if self.cached:
            cached_attributes = getattr(owner, self.cached_attributes_list, None)
            if cached_attributes is None:
                cached_attributes = []
                setattr(owner, self.cached_attributes_list, cached_attributes)
                setattr(owner, self.clear_cache_method, clear_cache)
            cached_attributes.append(name)
    
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
            raise TypeError(f'{self.name} is a read-only attribute, and cannot be set')
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
            raise TypeError(f'{self.name} is a read-only attribute, and cannot be deleted')
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
    
    def setter(self, setter: SetterType) -> attribute:
        if self.cached:
            raise TypeError(f'{self.name} is a cached attribute, and cannot have a custom setter')
        self._setter = setter
        return self
    
    def on_set(self, on_set: OnSetType) -> attribute:
        self._on_set = on_set
        return self
    
    def deleter(self, deleter: DeleterType) -> attribute:
        if self.cached:
            raise TypeError(f'{self.name} is a cached attribute, and cannot have a custom deleter')
        self._deleter = deleter
        return self
    
    def on_delete(self, on_delete: OnDeleteType) -> attribute:
        self._on_delete = on_delete
        return self


def clear_cache(self) -> None:
    for name in getattr(self.__class__, attribute.cached_attributes_list, []):
        self.__dict__.pop(name, None)