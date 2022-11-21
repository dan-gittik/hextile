from __future__ import annotations
from typing import ContextManager, Iterable, Iterator, Type

from dataclasses import dataclass
import pathlib

from ...utils import URL


class FileSystemDriver:
    
    scheme: str = None
    drivers: dict[str, Type[FileSystemDriver]] = {}
    end = -1

    @dataclass
    class Status:
        size: int
        mode: int
        owner_id: int = None
        group_id: int = None
        owner_name: str = None
        group_name: str = None
        access_time: float = None
        modification_time: float = None

    def __init_subclass__(cls):
        if not cls.scheme:
            raise RuntimeError(f'invalid filesystem driver class {cls.__name__}: scheme is not defined')
        if cls.scheme in cls.drivers:
            raise RuntimeError(f'invalid filesystem driver class {cls.__name__}: scheme {cls.scheme!r} is already defined (in class {cls.drivers[cls.scheme].__name__})')
        cls.drivers[cls.scheme] = cls
    
    def __init__(self, url: URL):
        self.url = url
        self.on_init()
    
    def __str__(self):
        return f'{self.scheme} filesystem driver at {self.url}'
    
    def __repr__(self):
        return f'<{self}>'
    
    @classmethod
    def from_url(cls, url: URL) -> FileSystemDriver:
        for scheme, driver in cls.drivers.items():
            if url.scheme == scheme:
                return driver(url)
        raise ValueError(f'unsupported URL scheme {url.scheme} (expected one of: {", ".join(cls.drivers)})')
    
    def on_init(self) -> None:
        pass
    
    def current_directory(self) -> pathlib.Path:
        raise NotImplementedError()
    
    def home_directory(self) -> pathlib.Path:
        raise NotImplementedError()
    
    def temporary_directory(self) -> pathlib.Path:
        raise NotImplementedError()
    
    def exists(self, path: pathlib.Path) -> bool:
        raise NotImplementedError()
    
    def is_directory(self, path: pathlib.Path) -> bool:
        raise NotImplementedError()

    def status(self, path: pathlib.Path) -> Status:
        raise NotImplementedError()
    
    def owner_name(self, path: pathlib.Path) -> str:
        raise NotImplementedError()
    
    def group_name(self, path: pathlib.Path) -> str:
        raise NotImplementedError()
    
    def rename(self, path: pathlib.Path, target: pathlib.Path) -> None:
        raise NotImplementedError()

    def change_mode(self, path: pathlib.Path, mode: int) -> None:
        raise NotImplementedError()
    
    def create_directory(self, path: pathlib.Path) -> None:
        raise NotImplementedError()
    
    def delete_directory(self, path: pathlib.Path) -> None:
        raise NotImplementedError()
    
    def copy_directory(self, path: pathlib.Path) -> None:
        raise NotImplementedError()
    
    def list_directory(self, path: pathlib.Path) -> Iterator[str]:
        raise NotImplementedError()
    
    def inside_directory(self, path: pathlib.Path) -> ContextManager[None]:
        raise NotImplementedError()
    
    def read(self, path: pathlib.Path, size: int, offset: int) -> bytes:
        raise NotImplementedError()
    
    def read_chunks(self, path: pathlib.Path, size: int, offset: int) -> Iterator[bytes]:
        raise NotImplementedError()
    
    def write(self, path: pathlib.Path, data: bytes, offset: int, truncate: bool) -> None:
        raise NotImplementedError()
    
    def write_chunks(self, path: pathlib.Path, chunks: Iterable[bytes], offset: int, truncate: bool) -> None:
        raise NotImplementedError()
    
    def execute(self, path: pathlib.Path, arguments: Iterable[str], stdin: bytes, timeout: float) -> tuple[int, bytes, bytes]:
        raise NotImplementedError()
    
    def delete_file(self, path: pathlib.Path) -> None:
        raise NotImplementedError()
    
    def copy_file(self, path: pathlib.Path, target: pathlib.Path) -> None:
        raise NotImplementedError()
    
    def archive(self, path: pathlib.Path, target: pathlib.Path, format: str) -> None:
        raise NotImplementedError()
    
    def extract(self, path: pathlib.Path, target: pathlib.Path, format: str) -> None:
        raise NotImplementedError()