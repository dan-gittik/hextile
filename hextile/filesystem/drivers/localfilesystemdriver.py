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

    def owner_name(self, path: pathlib.Path) -> str:
        try:
            return path.owner()
        except NotImplementedError:
            return None
    
    def group_name(self, path: pathlib.Path) -> str:
        try:
            return path.group()
        except NotImplementedError:
            return None
    
    def status(self, path: pathlib.Path) -> FileSystemDriver.Status:
        stat = path.stat()
        return self.Status(
            size = stat.st_size,
            mode = stat.st_mode & 0o777,
            time = stat.st_mtime,
            owner_id = stat.st_uid,
            group_id = stat.st_gid,
        )
    
    def change_mode(self, path: pathlib.Path, mode: int) -> None:
        path.chmod(mode)
    
    def create_directory(self, path: pathlib.Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
    
    def delete_directory(self, path: pathlib.Path) -> None:
        shutil.rmtree(path)
    
    def copy_directory(self, source: pathlib.Path, target: pathlib.Path) -> None:
        shutil.copytree(source, target)
    
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
    ) -> Execution:
        return Execution.run(path, *arguments, stdin=stdin, timeout=timeout, sigterm_timeout=0)

    def delete_file(self, path: pathlib.Path) -> None:
        path.unlink()
    
    def copy_file(self, source: pathlib.Path, target: pathlib.Path) -> None:
        shutil.copy2(source, target)
    
    def move(self, source: pathlib.Path, target: pathlib.Path) -> None:
        source.rename(target)
    
    def archive_zip(self, source: pathlib.Path, target: pathlib.Path) -> None:
        self._archive(source, target, 'zip')
    
    def archive_tar(self, source: pathlib.Path, target: pathlib.Path) -> None:
        self._archive(source, target, 'tar')
    
    def archive_gzip(self, source: pathlib.Path, target: pathlib.Path) -> None:
        self._archive(source, target, 'gztar')

    def archive_bzip2(self, source: pathlib.Path, target: pathlib.Path) -> None:
        self._archive(source, target, 'bztar')

    def archive_xz(self, source: pathlib.Path, target: pathlib.Path) -> None:
        self._archive(source, target, 'xztar')

    def extract_zip(self, source: pathlib.Path, target: pathlib.Path) -> None:
        shutil.unpack_archive(source, target, 'zip')

    def extract_tar(self, source: pathlib.Path, target: pathlib.Path) -> None:
        shutil.unpack_archive(source, target, 'tar')
    
    def extract_gzip(self, source: pathlib.Path, target: pathlib.Path) -> None:
        shutil.unpack_archive(source, target, 'gztar')
    
    def extract_bzip2(self, source: pathlib.Path, target: pathlib.Path) -> None:
        shutil.unpack_archive(source, target, 'bztar')
    
    def extract_xz(self, source: pathlib.Path, target: pathlib.Path) -> None:
        shutil.unpack_archive(source, target, 'xztar')

    def _resolve_mode(self, offset: int, truncate: bool) -> str:
        if offset == self.end:
            return 'ab'
        if truncate:
            return 'wb'
        return 'rb+'
    
    def _archive(self, source: pathlib.Path, target: pathlib.Path, format: str) -> pathlib.Path:
        prefix = target.with_name(target.name.split('.', 1)[0])
        path = shutil.make_archive(prefix, format, source)
        pathlib.Path(path).rename(target)