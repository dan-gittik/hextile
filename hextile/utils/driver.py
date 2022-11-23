from __future__ import annotations
from typing import Type

from .url import URL, URLType


class Driver:

    label: str = None
    scheme: str = None
    drivers: dict[str, Type[Driver]] = {}

    def __init_subclass__(cls):
        if 'label' in cls.__dict__:
            cls.drivers = {}
            return
        if 'scheme' not in cls.__dict__:
            if cls.label is None:
                raise TypeError(f'invalid driver base class {cls.__name__}: label is not defined')
            raise TypeError(f'invalid driver class {cls.__name__}: scheme is not defined')
        if cls.scheme in cls.drivers:
            raise TypeError(f'invalid driver class {cls.__name__}: scheme {cls.scheme!r} is already defined (in class {cls.drivers[cls.scheme].__name__})')
        cls.drivers[cls.scheme] = cls
    
    def __init__(self, url: URLType):
        self.url = URL.parse(url)
        self.on_init()
    
    def __str__(self):
        return f'{self.scheme} {self.label} driver at {self.url}'
    
    def __repr__(self):
        return f'{self.__class__.__name__}({str(self.url)!r})'
    
    @classmethod
    def from_url(cls, url: URLType) -> Driver:
        url = URL.parse(url)
        for scheme, driver in cls.drivers.items():
            if url.scheme == scheme:
                return driver(url)
        raise ValueError(f'unsupported URL scheme {url.scheme!r} (expected one of: {", ".join(cls.drivers)})')
    
    def on_init(self) -> None:
        pass