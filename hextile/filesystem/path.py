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
from ..utils import attribute, datetime_from_timestamp, Execution


class Path(str):

    readable = 'r'
    writable = 'w'
    executable = 'x'
    archive_extensions = {
        '.zip': 'zip',
        '.tar': 'tar',
        '.tar.gz': 'gzip',
        '.tar.bz': 'bzip2',
        '.tar.xz': 'xz',
    }
    _archive_formats = {value: key for key, value in archive_extensions.items()}

    default_depth_first = False
    default_encoding = 'utf8'
    default_on_encoding_error = 'strict'
    default_chunk_size = 4096
    default_linebreak = '\n'
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
        instance = super().__new__(cls, value)
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
    
    @attribute(readonly=True, cached=True)
    def drive(self) -> str:
        return self._path.drive
    
    @attribute(readonly=True, cached=True)
    def is_root(self) -> bool:
        return self._path.parent == self._path

    @attribute(readonly=True, cached=True)
    def directory(self) -> Path:
        return self._clone(self._path.parent)
    
    @attribute(readonly=True, cached=True)
    def basename(self) -> str:
        return self._path.name
    
    @attribute(readonly=True, cached=True)
    def name(self) -> str:
        index = self.basename.find('.', 1)
        if index == -1:
            return self._path.name
        return self._path.name[:index]
    
    @attribute(readonly=True, cached=True)
    def extension(self) -> str:
        index = self.basename.find('.', 1)
        if index == -1:
            return ''
        return self._path.name[index:]
    
    def exists(self) -> bool:
        return self._driver.exists(self._path)
    
    def is_directory(self) -> bool:
        return self._driver.is_directory(self._path)
    
    def is_file(self) -> bool:
        return self.exists() and not self.is_directory()
    
    def size(self) -> int:
        if self.is_directory():
            return None
        return self._driver.status(self._path).size
    
    def timestamp(self) -> float:
        return self._driver.status(self._path).time
    
    def datetime(self) -> dt.datetime:
        timestamp = self.timestamp()
        return timestamp and datetime_from_timestamp(timestamp)

    def owner_id(self) -> int:
        return self._driver.status(self._path).owner_id
    
    def group_id(self) -> int:
        return self._driver.status(self._path).group_id
    
    def owner_name(self) -> str:
        return self._driver.owner_name(self._path)
    
    def group_name(self) -> str:
        return self._driver.group_name(self._path)
    
    def owner_readable(self) -> bool:
        return self._get_permission(stat.S_IRUSR)

    def set_owner_readable(self, readable: bool) -> None:
        self._set_permission(stat.S_IRUSR, readable)
    
    def owner_writable(self) -> bool:
        return self._get_permission(stat.S_IWUSR)

    def set_owner_writable(self, writable: bool) -> None:
        self._set_permission(stat.S_IWUSR, writable)

    def owner_executable(self) -> bool:
        return self._get_permission(stat.S_IXUSR)

    def set_owner_executable(self, executable: bool) -> None:
        self._set_permission(stat.S_IXUSR, executable)
    
    def owner_permissions(self) -> str:
        return self._get_permissions(stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR)
    
    def set_owner_permissions(self, permissions: str) -> None:
        self._set_permissions(permissions, stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR)

    def group_readable(self) -> bool:
        return self._get_permission(stat.S_IRGRP)

    def set_group_readable(self, readable: bool) -> None:
        self._set_permission(stat.S_IRGRP, readable)
    
    def group_writable(self) -> bool:
        return self._get_permission(stat.S_IWGRP)

    def set_group_writable(self, writable: bool) -> None:
        self._set_permission(stat.S_IWGRP, writable)

    def group_executable(self) -> bool:
        return self._get_permission(stat.S_IXGRP)

    def set_group_executable(self, executable: bool) -> None:
        self._set_permission(stat.S_IXGRP, executable)

    def group_permissions(self) -> str:
        return self._get_permissions(stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP)
    
    def set_group_permissions(self, permissions: str) -> None:
        self._set_permissions(permissions, stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP)

    def other_readable(self) -> bool:
        return self._get_permission(stat.S_IROTH)

    def set_other_readable(self, readable: bool) -> None:
        self._set_permission(stat.S_IROTH, readable)
    
    def other_writable(self) -> bool:
        return self._get_permission(stat.S_IWOTH)

    def set_other_writable(self, writable: bool) -> None:
        self._set_permission(stat.S_IWOTH, writable)

    def other_executable(self) -> bool:
        return self._get_permission(stat.S_IXOTH)

    def set_other_executable(self, executable: bool) -> None:
        self._set_permission(stat.S_IXOTH, executable)

    def other_permissions(self) -> str:
        return self._get_permissions(stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH)
    
    def set_other_permissions(self, permissions: str) -> None:
        self._set_permissions(permissions, stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH)

    def with_basename(self, basename: str) -> Path:
        return self._clone(self._path.with_name(basename))
    
    def with_name(self, name: str) -> Path:
        return self._clone(self._path.with_name(name + self.extension))
    
    def with_extension(self, extension: str) -> Path:
        return self._clone(self._path.with_name(self.name + extension))
    
    def create_directory(self) -> None:
        self._driver.create_directory(self._path)
    
    def list(self) -> Iterator[Path]:
        for name in self._driver.list_directory(self._path):
            yield self._clone(resolve_path(name, relative_to=self), skippable=True)
    
    def walk(
            self,
            *,
            max_depth: int = None,
            depth_first: bool = None,
    ) -> Iterator[Path]:
        if max_depth is not None and max_depth <= 0:
            return []
        if depth_first is None:
            depth_first = self.default_depth_first
        if depth_first:
            return self._dfs_walk(max_depth - 1 if max_depth is not None else None)
        else:
            return self._bfs_walk(max_depth - 1 if max_depth is not None else None)
    
    def skip(self) -> None:
        if self._skip is None:
            raise TypeError(f'path {self!r} was not created in a directory walk and cannot be skipped')
        self._skip = True

    @contextlib.contextmanager
    def inside(self) -> ContextManager[None]:
        with self._driver.inside_directory(self._path):
            yield

    def read(self, size: int = None, offset: int = None) -> bytes:
        if offset is None:
            offset = self._driver.start
        return self._driver.read(self._path, size, offset)
    
    def read_chunks(self, size: int = None, offset: int = None) -> Iterator[bytes]:
        if size is None:
            size = self.default_chunk_size
        if offset is None:
            offset = self._driver.start
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
            while True:
                index = data.find(linebreak)
                if index == -1:
                    break
                line, data = data[:index], data[index + len(linebreak):]
                yield line.decode(encoding, on_encoding_error)
        if data:
            yield data.decode(encoding, on_encoding_error)
        else:
            yield ''
    
    def write(
            self,
            data: bytes,
            offset: int = None,
            *,
            append: bool = None,
            truncate: bool = None,
    ) -> None:
        offset, truncate = self._resolve_position(offset, append, truncate)
        self._driver.write(self._path, data, offset, truncate=truncate)
    
    def write_chunks(
            self,
            chunks: Iterable[bytes],
            offset: int = None,
            *,
            append: bool = None,
            truncate: bool = None,
    ) -> None:
        offset, truncate = self._resolve_position(offset, append, truncate)
        self._driver.write_chunks(self._path, chunks, offset, truncate=truncate)

    def write_text(
            self,
            text: str,
            encoding: str = None,
            on_encoding_error: str = None,
            *,
            append: bool = None,
    ) -> None:
        if encoding is None:
            encoding = self.default_encoding
        if on_encoding_error is None:
            on_encoding_error = self.default_on_encoding_error
        self.write(
            data = text.encode(encoding, on_encoding_error),
            append = append,
        )
    
    def write_lines(
            self,
            lines: Iterable[str],
            encoding: str = None,
            on_encoding_error: str = None,
            *,
            linebreak: str = None,
            append: bool = None,
    ) -> None:
        if encoding is None:
            encoding = self.default_encoding
        if on_encoding_error is None:
            on_encoding_error = self.default_on_encoding_error
        if linebreak is None:
            linebreak = self.default_linebreak
        linebreak = linebreak.encode()
        def chunks() -> Iterator[bytes]:
            for line in lines:
                yield line.encode(encoding, on_encoding_error)
                yield linebreak
        self.write_chunks(
            chunks = chunks(),
            append = append,
        )
    
    def execute(
            self,
            *arguments: str,
            stdin: str|bytes = None,
            timeout: float = None,
    ) -> Execution:
        if isinstance(stdin, str):
            stdin = stdin.encode()
        return self._driver.execute(self._path, arguments, stdin, timeout)
    
    def delete(self) -> None:
        if self.is_directory():
            self._driver.delete_directory(self._path)
        else:
            self._driver.delete_file(self._path)

    def move(
            self,
            target: PathType,
            *,
            into_directory: bool = None,
            overwrite: bool = None,
    ) -> Path:
        target = self._resolve_target(target, into_directory, overwrite)
        self._driver.move(self._path, target._path)
        return target

    def copy(
            self,
            target: PathType,
            *,
            into_directory: bool = None,
            overwrite: bool = None,
    ) -> Path:
        target = self._resolve_target(target, into_directory, overwrite)
        if self.is_directory():
            self._driver.copy_directory(self._path, target._path)
        else:
            self._driver.copy_file(self._path, target._path)
        return target
    
    def archive(
            self,
            target: PathType,
            format: str = None,
            *,
            into_directory: bool = None,
            overwrite: bool = None,
    ) -> Path:
        if not self.exists():
            raise FileNotFoundError(f'path {self!r} does not exist')
        target = self._resolve_target(target, into_directory, overwrite)
        format = self._resolve_archive_format(format, target.extension)
        if into_directory:
            target = target.with_extension(self._archive_formats[format])
        if format == 'zip':
            self._driver.archive_zip(self._path, target._path)
        elif format == 'tar':
            self._driver.archive_tar(self._path, target._path)
        elif format == 'gzip':
            self._driver.archive_gzip(self._path, target._path)
        elif format == 'bzip2':
            self._driver.archive_bzip2(self._path, target._path)
        elif format == 'xz':
            self._driver.archive_xz(self._path, target._path)
        return target
    
    def extract(
            self,
            target: PathType,
            format: str = None,
            *,
            into_directory: bool = None,
            overwrite: bool = None,
    ) -> Path:
        # merge ?
        format = self._resolve_archive_format(format, self.extension)
        target = self._resolve_target(target, into_directory, overwrite)
        if into_directory:
            target = target.with_extension('')
        if format == 'zip':
            self._driver.extract_zip(self._path, target._path)
        elif format == 'tar':
            self._driver.extract_tar(self._path, target._path)
        elif format == 'gzip':
            self._driver.extract_gzip(self._path, target._path)
        elif format == 'bzip2':
            self._driver.extract_bzip2(self._path, target._path)
        elif format == 'xz':
            self._driver.extract_xz(self._path, target._path)
        return target
    
    def _clone(self, path: pathlib.Path, skippable: bool = None) -> Path:
        return Path(self._driver, path, skippable=skippable)
    
    def _get_permission(self, mask: int) -> bool:
        mode = self._driver.status(self._path).mode
        return bool(mode & mask)

    def _set_permission(self, mask: int, on: bool) -> int:
        mode = self._driver.status(self._path).mode
        mode = self._mask(mode, mask, on)
        self._driver.change_mode(self._path, mode)
    
    def _get_permissions(self, readable_mask: int, writable_mask: int, executable_mask: int) -> str:
        mode = self._driver.status(self._path).mode
        output = []
        if mode & readable_mask:
            output.append(self.readable)
        if mode & writable_mask:
            output.append(self.writable)
        if mode & executable_mask:
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
        mode = self._driver.status(self._path).mode
        mode = self._mask(mode, readable_mask, self.readable in permissions)
        mode = self._mask(mode, writable_mask, self.writable in permissions)
        mode = self._mask(mode, executable_mask, self.executable in permissions)
        self._driver.change_mode(self._path, mode)

    def _mask(self, mode: int, mask: int, on: bool) -> int:
        return (mode | mask) if on else (mode & ~mask)
    
    def _resolve_target(self, path: PathType, into_directory: bool, overwrite: bool) -> Path:
        if into_directory is None:
            into_directory = self.default_into_directory
        if overwrite is None:
            overwrite = self.default_overwrite
        path = resolve_path(path, relative_to=self.directory)
        if into_directory:
            path = path / self.basename
        target = self._clone(path)
        if target.exists():
            if overwrite:
                target.delete()
            else:
                raise FileExistsError(f'path {target!r} already exists')
        return target
    
    def _dfs_walk(self, max_depth: int) -> Iterator[Path]:
        for entry in self.list():
            yield entry
            if entry.is_directory():
                if entry._skip or (max_depth is not None and max_depth <= 0):
                    continue
                yield from entry._dfs_walk(max_depth - 1 if max_depth is not None else None)

    def _bfs_walk(self, max_depth: int) -> Iterator[Path]:
        roots = collections.deque([(0, self)])
        while roots:
            depth, root = roots.popleft()
            for entry in root.list():
                yield entry
                if entry.is_directory():
                    if entry._skip or (max_depth is not None and depth >= max_depth):
                        continue
                    roots.append((depth + 1, entry))

    def _resolve_position(
            self,
            offset: int,
            append: bool,
            truncate: bool,
    ) -> tuple[int, bool]:
        if offset:
            if append:
                raise ValueError(f'cannot write data at offset {offset} while also appending it')
            if truncate:
                raise ValueError(f'cannot write data at offset {offset} while also truncating the file')
        else:
            if append is None and truncate is None:
                append = self.default_append
                truncate = self.default_truncate
            if append and truncate:
                raise ValueError(f'cannot append data while also truncating the file')
            offset = self._driver.end if append else self._driver.start
        return offset, truncate

    def _resolve_archive_format(self, format: str, extension: str) -> str:
        if format is None:
            if extension not in self.archive_extensions:
                raise ValueError(f'unfamiliar archive extension {extension!r} (expected one of: {", ".join(self.archive_extensions)})')
            return self.archive_extensions[extension]
        elif format not in self.archive_extensions.values():
            raise ValueError(f'unfamiliar archive format {format!r} (expected one of: {", ".join(self.archive_extensions.values())})')
        return format


PathType = str | pathlib.Path | Path


def resolve_path(path: PathType, relative_to: Path = None) -> pathlib.Path:
    if isinstance(path, Path):
        return path._path
    if relative_to is not None:
        return (relative_to._path / path).resolve()
    if isinstance(path, pathlib.Path):
        return path.resolve()
    return pathlib.Path(path).resolve()