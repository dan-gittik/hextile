from __future__ import annotations

import pathlib

from .drivers import FileSystemDriver
from ..utils import URL, URLType


class FileSystem:

    def __init__(self, url: URLType):
        self.url = URL.parse(url)
        self._driver: FileSystemDriver = FileSystemDriver.from_url(self.url)
    
    def __str__(self):
        return f'filesystem at {self.url}'
    
    def __repr__(self):
        return f'{self.__class__.__name__}({str(self.url)!r})'
    
    def current_directory(self) -> Path:
        return self._path(self._driver.current_directory())
    
    def home_directory(self) -> Path:
        return self._path(self._driver.home_directory())
    
    def temporary_directory(self) -> Path:
        return self._path(self._driver.temporary_directory(), temporary=True)

    def path(self, path: PathType, exists: bool = None) -> Path:
        path = self._path(path)
        if exists is not None:
            self._assert_exists(path, exists)
        return path
    
    def directory(
            self,
            path: PathType,
            exists: bool = None,
            create: bool = None,
    ) -> Path:
        path = self._path(path)
        if exists is not None:
            self._assert_directory(path, exists)
        if create:
            path.create_directory()
        return path

    def file(
            self,
            path: PathType,
            exists: bool = None,
    ) -> Path:
        path = self._path(path)
        if exists is not None:
            self._assert_file(path, exists)
        return path

    def _path(self, path: pathlib.Path, temporary: bool = None) -> Path:
        return Path(self._driver, path, temporary=temporary)

    def _assert_exists(self, path: Path, exists: bool) -> None:
        if exists and not path.exists():
            raise FileNotFoundError(f'path {path!r} does not exist')
        if not exists and path.exists():
            raise FileExistsError(f'path {path!r} exists')

    def _assert_directory(self, path: Path, exists: bool) -> None:
        if exists:
            if not path.exists():
                raise FileNotFoundError(f'directory {path!r} does not exist')
            if not path.is_directory():
                raise NotADirectoryError(f'path {path!r} is not a directory')
        if not exists and path.exists():
            raise FileExistsError(f'directory {path!r} exists')

    def _assert_file(self, path: Path, exists: bool) -> None:
        if exists:
            if not path.exists():
                raise FileNotFoundError(f'file {path!r} does not exist')
            if path.is_directory():
                raise IsADirectoryError(f'path {path!r} is not a file')
        if not exists and path.exists():
            raise FileExistsError(f'file {path!r} exists')
    

local_filesystem = FileSystem('local://')


from .path import Path, PathType