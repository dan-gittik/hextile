from __future__ import annotations
from typing import ContextManager, Iterable, Iterator, Type
from types import TracebackType

import collections
import contextlib
import datetime as dt
import stat
import pathlib
import weakref

from .drivers import FileSystemDriver
from ..utils import cached_property,datetime_from_timestamp, Execution


class Path(str):

    readable = 'r'
    writable = 'w'
    executable = 'x'

    default_depth_first = False
    default_encoding = 'utf8'
    default_on_encoding_error = 'strict'
    default_chunk_size = 4096
    default_linebreak = '\n'
    default_archive_format = 'zip'
    default_into_directory = False
    default_overwrite = False
    default_truncate = True
    default_append = False
    
    _values: weakref.WeakValueDictionary[str, Path] = weakref.WeakValueDictionary()
    _driver: FileSystemDriver
    _path: pathlib.Path
    _temporary: bool = None
    _skip: bool = None

    def __new__(
            cls,
            driver: FileSystemDriver,
            path: PathType,
            temporary: bool = False,
            skippable: bool = False,
    ):
        path = resolve_path(path)
        value = str(path)
        if value in cls._values:
            return cls._values[value]
        instance = super().__new__(value)
        instance._driver = driver
        instance._path = path
        if temporary:
            instance._temporary = True
        if skippable:
            instance._skip = False
        cls._values[value] = instance
        return instance
    
    def __enter__(self) -> Path:
        if self._temporary is None:
            raise TypeError(f'path {self!r} is not temporary and cannot be used in a with statement')
        return self

    def __exit__(self, exception: Type[Exception], error: Exception, traceback: TracebackType) -> None:
        self.delete()
    
    def __truediv__(self, other: PathType) -> Path:
        return self._clone(resolve_path(other, relative_to=self))
    
    @cached_property
    def is_root(self) -> bool:
        return self._path.parent == self._path

    @cached_property
    def directory(self) -> Path:
        return self._clone(self._path.parent)
    
    @cached_property
    def basename(self) -> str:
        return self._path.name
    
    @cached_property
    def name(self) -> str:
        if self._dot_index == -1:
            return self._path.name
        return self._path.name[:self._dot_index]
    
    @cached_property
    def extension(self) -> str:
        if self._dot_index == -1:
            return ''
        return self._path.name[self._dot_index:]
    
    @cached_property
    def exists(self) -> bool:
        return self._driver.exists(self._path)
    
    @cached_property
    def is_directory(self) -> bool:
        return self._driver.is_directory(self._path)
    
    @property
    def is_file(self) -> bool:
        return not self.is_directory
    
    @cached_property
    def status(self) -> FileSystemDriver.Status:
        return self._driver.status(self._path)
    
    @property
    def size(self) -> int:
        if self.is_directory:
            return None
        return self.status.size
    
    @property
    def access_time(self) -> float:
        return self.status.access_time
    
    @property
    def access_datetime(self) -> dt.datetime:
        return self.access_time and datetime_from_timestamp(self.access_time)

    @property
    def modification_time(self) -> float:
        return self.status.modification_time
    
    @property
    def modification_datetime(self) -> dt.datetime:
        return self.modification_time and datetime_from_timestamp(self.modification_time)

    @property
    def owner_id(self) -> int:
        return self.status.owner_id
    
    @property
    def group_id(self) -> int:
        return self.status.group_id
    
    @property
    def owner_name(self) -> str:
        return self.status.owner_name
    
    @property
    def group_name(self) -> str:
        return self.status.group_name
    
    @property
    def owner_readable(self) -> bool:
        return self._get_permission(stat.S_IRUSR)

    @owner_readable.setter
    def owner_readable(self, readable: bool) -> None:
        self._set_permission(stat.S_IRUSR, readable)
    
    @property
    def owner_writable(self) -> bool:
        return self._get_permission(stat.S_IWUSR)

    @owner_writable.setter
    def owner_writable(self, writable: bool) -> None:
        self._set_permission(stat.S_IWUSR, writable)

    @property
    def owner_executable(self) -> bool:
        return self._get_permission(stat.S_IXUSR)

    @owner_executable.setter
    def owner_executable(self, executable: bool) -> None:
        self._set_permission(stat.S_IXUSR, executable)
    
    @property
    def owner_permissions(self) -> str:
        return self._get_permissions(stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR)
    
    @owner_permissions.setter
    def owner_permissions(self, permissions: str) -> None:
        self._set_permissions(permissions, stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR)

    @property
    def group_readable(self) -> bool:
        return self._get_permission(stat.S_IRGRP)

    @group_readable.setter
    def group_readable(self, readable: bool) -> None:
        self._set_permission(stat.S_IRGRP, readable)
    
    @property
    def group_writable(self) -> bool:
        return self._get_permission(stat.S_IWGRP)

    @group_writable.setter
    def group_writable(self, writable: bool) -> None:
        self._set_permission(stat.S_IWGRP, writable)

    @property
    def group_executable(self) -> bool:
        return self._get_permission(stat.S_IXGRP)

    @group_executable.setter
    def group_executable(self, executable: bool) -> None:
        self._set_permission(stat.S_IXGRP, executable)

    @property
    def group_permissions(self) -> str:
        return self._get_permissions(stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP)
    
    @group_permissions.setter
    def group_permissions(self, permissions: str) -> None:
        self._set_permissions(permissions, stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP)

    @property
    def other_readable(self) -> bool:
        return self._get_permission(stat.S_IROTH)

    @other_readable.setter
    def other_readable(self, readable: bool) -> None:
        self._set_permission(stat.S_IROTH, readable)
    
    @property
    def other_writable(self) -> bool:
        return self._get_permission(stat.S_IWOTH)

    @other_writable.setter
    def other_writable(self, writable: bool) -> None:
        self._set_permission(stat.S_IWOTH, writable)

    @property
    def other_executable(self) -> bool:
        return self._get_permission(stat.S_IXOTH)

    @other_executable.setter
    def other_executable(self, executable: bool) -> None:
        self._set_permission(stat.S_IXOTH, executable)

    @property
    def other_permissions(self) -> str:
        return self._get_permissions(stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH)
    
    @other_permissions.setter
    def other_permissions(self, permissions: str) -> None:
        self._set_permissions(permissions, stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH)

    def rename(
            self,
            target: PathType,
            *,
            into_directory: bool = None,
            overwrite: bool = None,
    ) -> Path:
        target = self._resolve_target(target, into_directory, overwrite)
        self._driver.rename(self._path, target._path)
        return target

    def with_basename(self, basename: str) -> Path:
        return self._clone(self._path.with_name(basename))
    
    def with_name(self, name: str) -> Path:
        return self._clone(self._path.with_name(name + self.extension))
    
    def with_extension(self, extension: str) -> Path:
        return self._clone(self._path.with_name(self.name + extension))
    
    def create_directory(self) -> None:
        self._driver.create_directory(self._path)
        self._refresh(exists=True, is_directory=True)
    
    def list(self) -> Iterator[Path]:
        for name in self._driver.list_directory(self._path):
            yield self._clone(resolve_path(name, relative_to=self), skippable=True)
    
    def walk(
            self,
            *,
            max_depth: int = None,
            depth_first: bool = None,
    ) -> Iterator[Path]:
        if depth_first is None:
            depth_first = self.default_depth_first
        if depth_first:
            return self._dfs_walk(max_depth)
        else:
            return self._bfs_walk(max_depth)
    
    def skip(self) -> None:
        if self._skip is None:
            raise TypeError(f'path {self!r} was not created in a directory walk and cannot be skipped')
        self._skip = True

    @contextlib.contextmanager
    def inside(self) -> ContextManager[None]:
        with self._driver.inside_directory(self._path):
            yield

    def read(self, size: int = None, offset: int = None) -> bytes:
        return self._driver.read(self._path, size, offset)
    
    def read_chunks(self, size: int = None, offset: int = None) -> Iterator[bytes]:
        if size is None:
            size = self.default_chunk_size
        yield from self._driver.read_chunks(self._path, size, offset)
    
    def read_text(
            self,
            encoding: str = None,
            on_encoding_error: str = None,
    ) -> str:
        if encoding is None:
            encoding = self.default_encoding
        if on_encoding_error is None:
            on_encoding_error = self.default_on_encoding_error
        return self.read().decode(encoding, on_encoding_error)
    
    def read_lines(
            self,
            encoding: str = None,
            on_encoding_error: str = None,
            *,
            linebreak: str = None,
    ) -> Iterator[str]:
        if encoding is None:
            encoding = self.default_encoding
        if on_encoding_error is None:
            on_encoding_error = self.default_on_encoding_error
        if linebreak is None:
            linebreak = self.default_linebreak
        linebreak = linebreak.encode()
        data: bytearray = bytearray()
        for chunk in self.read_chunks():
            data.extend(chunk)
            index = data.find(linebreak)
            if index == -1:
                continue
            line, data = data[:index], data[index + len(linebreak):]
            yield line.decode(encoding, on_encoding_error)
    
    def write(
            self,
            data: bytes,
            offset: int = None,
            *,
            append: bool = None,
            truncate: bool = None,
    ) -> None:
        offset, truncate = self._resolve_offset_and_truncate(offset, append, truncate)
        self._driver.write(self._path, data, offset, truncate=truncate)
        self._refresh(exists=True, is_directory=False)
    
    def write_chunks(
            self,
            chunks: Iterable[bytes],
            offset: int = None,
            *,
            append: bool = None,
            truncate: bool = None,
    ) -> None:
        offset, truncate = self._resolve_offset_and_truncate(offset, append, truncate)
        self._driver.write_chunks(self._path, chunks, offset, truncate=truncate)
        self._refresh(exists=True, is_directory=False)

    def write_text(
            self,
            text: str,
            encoding: str = None,
            on_encoding_error: str = None,
            *,
            append: bool = None,
            truncate: bool = None,
    ) -> None:
        if encoding is None:
            encoding = self.default_encoding
        if on_encoding_error is None:
            on_encoding_error = self.default_on_encoding_error
        offset, truncate = self._resolve_offset_and_truncate(offset, append, truncate)
        self.write(text.encode(encoding, on_encoding_error), offset, truncate=truncate)
    
    def write_lines(
            self,
            lines: Iterable[str],
            encoding: str = None,
            on_encoding_error: str = None,
            *,
            linebreak: str = None,
            truncate: bool = None,
            append: bool = None,
    ) -> None:
        if encoding is None:
            encoding = self.default_encoding
        if on_encoding_error is None:
            on_encoding_error = self.default_on_encoding_error
        if linebreak is None:
            linebreak = self.default_linebreak
        linebreak = linebreak.encode()
        offset, truncate = self._resolve_offset_and_truncate(offset, append, truncate)
        def chunks() -> Iterator[bytes]:
            for line in lines:
                yield line.encode(encoding, on_encoding_error)
                yield linebreak
        self.write_chunks(chunks, offset, truncate=truncate)
    
    def execute(
            self,
            *arguments: str,
            stdin: str|bytes = None,
            timeout: float = None,
    ) -> Execution:
        if isinstance(stdin, str):
            stdin = stdin.encode()
        exit_code, stdout, stderr = self._driver.execute(self._path, arguments, stdin, timeout)
        return Execution(exit_code, stdout, stderr)
    
    def delete(self) -> None:
        if self.is_directory:
            self._driver.delete_directory(self._path)
        else:
            self._driver.delete_file(self._path)
        self._refresh(exists=False, is_directory=False)

    def copy(
            self,
            target: PathType,
            *,
            into_directory: bool = None,
            overwrite: bool = None,
    ) -> Path:
        target = self._resolve_target(target, into_directory, overwrite)
        if self.is_directory:
            self._driver.copy_directory(self._path, target._path)
        else:
            self._driver.copy_file(self._path, target._path)
        return target
    
    def archive(self, target: PathType, format: str = None) -> Path:
        if format is None:
            format = self.default_archive_format
        target = resolve_path(target, relative_to=self)
        self._driver.archive(self._path, target, format)
        return target
    
    def extract(self, target: PathType, format: str = None) -> Path:
        target = resolve_path(target, relative_to=self)
        self._driver.extract(self._path, target, format)
        return target
    
    @cached_property
    def _dot_index(self) -> int:
        return self.basename.find('.', 1)

    def _clone(self, path: pathlib.Path, skippable: bool = None) -> Path:
        return Path(self._driver, path, skippable=skippable)
    
    def _refresh(self, exists: bool = None, is_directory: bool = None) -> None:
        if exists is not None:
            self.exists = exists
        if is_directory is not None:
            self.is_directory = is_directory
        del self.status

    def _get_permission(self, mask: int) -> bool:
        return bool(self.status.mode & mask)

    def _set_permission(self, mask: int, on: bool) -> int:
        mode = self._mask(self.status.mode, mask, on)
        self._driver.change_mode(self._path, mode)
        self.status.mode = mode
    
    def _get_permissions(self, readable_mask: int, writable_mask: int, executable_mask: int) -> str:
        output = []
        if self.status.mode & readable_mask:
            output.append(self.readable)
        if self.status.mode & writable_mask:
            output.append(self.writable)
        if self.status.mode & executable_mask:
            output.append(self.executable)
        return ''.join(output)

    def _set_permissions(
            self,
            permissions: str,
            readable_mask: int,
            writable_mask: int,
            executable_mask: int,
    ) -> None:
        permissions = permissions.lower()
        mode = self.status.mode
        mode = self._mask(mode, readable_mask, self.readable in permissions)
        mode = self._mask(mode, writable_mask, self.writable in permissions)
        mode = self._mask(mode, executable_mask, self.executable in permissions)
        self._driver.change_mode(self._path, mode)
        self.status.mode = mode

    def _mask(self, mode: int, mask: int, on: bool) -> int:
        return (mode | mask) if on else (mode & ~mask)
    
    def _resolve_target(self, path: PathType, into_directory: bool, overwrite: bool) -> Path:
        if into_directory is None:
            into_directory = self.default_into_directory
        if overwrite is None:
            overwrite = self.default_overwrite
        path = resolve_path(path, relative_to=self)
        if into_directory:
            path = path / self.basename
        target = self._clone(path)
        if target.exists:
            if overwrite:
                target.delete()
            else:
                raise ValueError(f'path {target!r} already exists')
        return target
    
    def _dfs_walk(self, max_depth: int) -> Iterator[Path]:
        for entry in self.list():
            yield entry
            if entry.is_directory:
                if entry._skip or max_depth == 0:
                    continue
                yield from entry._dfs_walk(max_depth and max_depth - 1)

    def _bfs_walk(self, max_depth: int) -> Iterator[Path]:
        roots = collections.deque([(0, self)])
        while roots:
            depth, root = roots.popleft()
            for entry in root.list():
                yield entry
                if entry.is_directory:
                    if entry._skip or depth == max_depth:
                        continue
                    roots.append((depth + 1, entry))

    def _resolve_offset_and_truncate(self, offset: int, append: bool, truncate: bool) -> tuple[int, bool]:
        if offset is not None:
            if append:
                raise ValueError(f'cannot write data at offset {offset} while also appending it')
            if truncate:
                raise ValueError(f'cannot write data at offset {offset} while also truncating the file')
        else:
            if append is None:
                append = self.default_append
            if truncate is None:
                truncate = self.default_truncate
            if append and truncate:
                raise ValueError(f'cannot append data while also truncating the file')
            offset = self._driver.end if append else 0
        return offset, truncate


PathType = str | pathlib.Path | Path


def resolve_path(path: PathType, relative_to: Path = None) -> pathlib.Path:
    if isinstance(path, Path):
        return path._path
    if isinstance(path, pathlib.Path):
        return path.resolve()
    if relative_to is not None:
        return (relative_to._path / path).resolve()
    return pathlib.Path(path).resolve()