from __future__ import annotations

import pathlib

from .drivers import FileSystemDriver
from ..utils import URL


class FileSystem:

    def __init__(self, url: str|URL):
        self.url = URL.from_string(url)
        self.driver = FileSystemDriver.from_url(self.url)
    
    def __str__(self):
        return f'filesystem at {self.url}'
    
    def __repr__(self):
        return f'<{self}>'
    
    def current_directory(self) -> Path:
        return Path(self, self.driver.current_directory())
    
    def home_directory(self) -> Path:
        return Path(self, self.driver.home_directory())
    
    def temporary_directory(self) -> Path:
        return Path(self, self.driver.temporary_directory(), temporary=True)

    def path(self, path: str|pathlib.Path|Path, exists: bool = None) -> Path:
        path = Path(self, path)
        if exists is not None:
            if exists and not path.exists:
                raise FileNotFoundError(f'path {path!r} does not exist')
            if not exists and path.exists:
                raise FileExistsError(f'path {path!r} exists')
        return path
    
    def directory(
            self,
            path: str|pathlib.Path|Path,
            exists: bool = None,
            create: bool = None,
    ) -> Path:
        path = Path(self, str(path))
        if exists is not None:
            if exists:
                if not path.exists:
                    raise FileNotFoundError(f'path {path!r} does not exist')
                if not path.is_directory:
                    raise NotADirectoryError(f'path {path!r} is not a directory')
            if not exists and path.exists:
                raise FileExistsError(f'path {path!r} exists')
        if create:
            path.create_directory()
        return path

    def file(
            self,
            path: str|pathlib.Path|Path,
            exists: bool = None,
    ) -> Path:
        path = Path(self, path)
        if exists is not None:
            if exists:
                if not path.exists:
                    raise FileNotFoundError(f'path {path!r} does not exist')
                if path.is_directory:
                    raise IsADirectoryError(f'path {path!r} is not a file')
            if not exists and path.exists:
                raise FileExistsError(f'path {path!r} exists')
        return path


local_filesystem = FileSystem('local://')


from .path import Path