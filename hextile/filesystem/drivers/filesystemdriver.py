from __future__ import annotations
from typing import ContextManager, Iterable, Iterator

from dataclasses import dataclass
import pathlib

from ...utils import Driver, Execution


class FileSystemDriver(Driver):
    
    label = 'filesystem'
    start = 0
    end = -1

    @dataclass
    class Status:
        size: int
        mode: int
        time: float = None
        owner_id: int = None
        group_id: int = None

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

    def owner_name(self, path: pathlib.Path) -> str:
        raise NotImplementedError()
    
    def group_name(self, path: pathlib.Path) -> str:
        raise NotImplementedError()
    
    def status(self, path: pathlib.Path) -> Status:
        raise NotImplementedError()
    
    def change_mode(self, path: pathlib.Path, mode: int) -> None:
        raise NotImplementedError()
    
    def create_directory(self, path: pathlib.Path) -> None:
        raise NotImplementedError()
    
    def delete_directory(self, path: pathlib.Path) -> None:
        raise NotImplementedError()
    
    def copy_directory(self, source: pathlib.Path, target: pathlib.Path) -> None:
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
    
    def write_chunks(
            self,
            path: pathlib.Path,
            chunks: Iterable[bytes],
            offset: int,
            truncate: bool,
    ) -> None:
        raise NotImplementedError()
    
    def execute(
            self,
            path: pathlib.Path,
            arguments: Iterable[str],
            stdin: bytes,
            timeout: float,
    ) -> Execution:
        raise NotImplementedError()
    
    def delete_file(self, path: pathlib.Path) -> None:
        raise NotImplementedError()
    
    def copy_file(self, source: pathlib.Path, target: pathlib.Path) -> None:
        raise NotImplementedError()
    
    def move(self, source: pathlib.Path, target: pathlib.Path) -> None:
        raise NotImplementedError()

    def archive_zip(self, source: pathlib.Path, target: pathlib.Path) -> None:
        raise NotImplementedError()
    
    def archive_tar(self, source: pathlib.Path, target: pathlib.Path) -> None:
        raise NotImplementedError()

    def archive_gzip(self, source: pathlib.Path, target: pathlib.Path) -> None:
        raise NotImplementedError()

    def archive_bzip2(self, source: pathlib.Path, target: pathlib.Path) -> None:
        raise NotImplementedError()

    def archive_xz(self, source: pathlib.Path, target: pathlib.Path) -> None:
        raise NotImplementedError()

    def extract_zip(self, source: pathlib.Path, target: pathlib.Path) -> None:
        raise NotImplementedError()

    def extract_tar(self, source: pathlib.Path, target: pathlib.Path) -> None:
        raise NotImplementedError()

    def extract_gzip(self, source: pathlib.Path, target: pathlib.Path) -> None:
        raise NotImplementedError()

    def extract_bzip2(self, source: pathlib.Path, target: pathlib.Path) -> None:
        raise NotImplementedError()

    def extract_xz(self, source: pathlib.Path, target: pathlib.Path) -> None:
        raise NotImplementedError()