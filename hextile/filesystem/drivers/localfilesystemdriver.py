from __future__ import annotations
from typing import ContextManager, Iterable, Iterator

import contextlib
import os
import pathlib
import shutil
import tempfile

from .filesystemdriver import FileSystemDriver
from ...utils import Execution


class LocalFileSystemDriver(FileSystemDriver):
    
    scheme = 'local'

    def current_directory(self) -> pathlib.Path:
        return pathlib.Path.cwd()

    def home_directory(self) -> pathlib.Path:
        return pathlib.Path.home()

    def temporary_directory(self) -> pathlib.Path:
        return pathlib.Path(tempfile.mkdtemp())

    def exists(self, path: pathlib.Path) -> bool:
        return path.exists()
    
    def is_directory(self, path: pathlib.Path) -> bool:
        return path.is_dir()

    def status(self, path: pathlib.Path) -> FileSystemDriver.Status:
        stat = path.stat()
        return self.Status(
            size = stat.st_size,
            mode = stat.st_mode,
            time = stat.st_mtime,
            owner_id = stat.st_uid,
            group_id = stat.st_gid,
        )
    
    def owner_name(self, path: pathlib.Path) -> str:
        return path.owner()
    
    def group_name(self, path: pathlib.Path) -> str:
        return path.group()
    
    def rename(self, path: pathlib.Path, target: pathlib.Path) -> None:
        path.rename(target)
    
    def change_mode(self, path: pathlib.Path, mode: int) -> None:
        path.chmod(mode)
    
    def create_directory(self, path: pathlib.Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
    
    def delete_directory(self, path: pathlib.Path) -> None:
        shutil.rmtree(path)
    
    def copy_directory(self, path: pathlib.Path, target: pathlib.Path) -> None:
        shutil.copytree(path, target)
    
    def list_directory(self, path: pathlib.Path) -> Iterator[str]:
        for entry in path.iterdir():
            yield entry.name
    
    @contextlib.contextmanager
    def inside_directory(self, path: pathlib.Path) -> ContextManager[None]:
        try:
            source = os.getcwd()
            os.chdir(path)
            yield
        finally:
            os.chdir(source)
    
    def read(self, path: pathlib.Path, size: int, offset: int) -> bytes:
        with path.open('rb') as reader:
            if offset > 0:
                reader.seek(offset)
            return reader.read(size)
    
    def read_chunks(self, path: pathlib.Path, size: int, offset: int) -> Iterator[bytes]:
        with path.open('rb') as reader:
            if offset > 0:
                reader.seek(offset)
            while True:
                chunk = reader.read(size)
                if not chunk:
                    break
                yield chunk
        
    def write(self, path: pathlib.Path, data: bytes, offset: int, truncate: bool) -> None:
        mode = self._resolve_mode(offset, truncate)
        with path.open(mode) as writer:
            if offset > 0:
                writer.seek(offset)
            writer.write(data)
    
    def write_chunks(
            self,
            path: pathlib.Path,
            chunks: Iterable[bytes],
            offset: int,
            truncate: bool,
    ) -> None:
        mode = self._resolve_mode(offset, truncate)
        with path.open(mode) as writer:
            if offset > 0:
                writer.seek(offset)
            for chunk in chunks:
                writer.write(chunk)
        
    def execute(
            self,
            path: pathlib.Path,
            arguments: Iterable[str],
            stdin: bytes,
            timeout: float,
    ) -> tuple[int, bytes, bytes]:
        execution = Execution.run(path, *arguments, stdin=stdin, timeout=timeout)
        return execution.exit_code, execution.stdout, execution.stderr

    def delete_file(self, path: pathlib.Path) -> None:
        path.unlink()
    
    def copy_file(self, path: pathlib.Path, target: pathlib.Path) -> None:
        shutil.copy2(path, target)
    
    def archive(self, path: pathlib.Path, target: pathlib.Path, format: str) -> None:
        shutil.make_archive(target, format, path)
    
    def extract(self, path: pathlib.Path, target: pathlib.Path, format: str) -> None:
        shutil.unpack_archive(path, path, format)
    
    def _resolve_mode(self, offset: int, truncate: bool) -> str:
        if offset == self.end:
            return 'ab'
        if truncate:
            return 'wb'
        return 'rb+'