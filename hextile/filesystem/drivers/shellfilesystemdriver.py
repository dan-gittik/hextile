from __future__ import annotations
from typing import ContextManager, Iterable, Iterator

import contextlib
import pathlib

from .filesystemdriver import FileSystemDriver


class ShellFileSystemDriver(FileSystemDriver):
    
    scheme = 'shell'
    tar_flags = {
        'tar': '',
        'gztar': '--gzip',
        'bztar': '--bzip2',
        'xztar': '--xz',
    }

    def current_directory(self) -> pathlib.Path:
        path = self._read_string('pwd')
        return pathlib.Path(path)

    def home_directory(self) -> pathlib.Path:
        return self._read_string('echo $HOME')

    def temporary_directory(self) -> pathlib.Path:
        return self._read_string('mktemp -d')

    def exists(self, path: pathlib.Path) -> bool:
        return self._read_string(f'[ -d {str(path)!r} ] && echo 1') == '1'

    def status(self, path: pathlib.Path) -> FileSystemDriver.Status:
        stat = self._read_string(f'stat {str(path)!r} -c "%s;%a;%u;%U;%g;%G;%X;%Yt')
        size, mode, owner_id, group_id, owner_name, group_name, access_time, modification_time = stat.split(';')
        return self.Status(
            size = int(size),
            mode = int(mode, 8),
            owner_id = int(owner_id),
            group_id = int(group_id),
            owner_name = owner_name,
            group_name = group_name,
            access_time = int(access_time),
            modification_time = int(modification_time),
        )
    
    def rename(self, path: pathlib.Path, target: pathlib.Path) -> None:
        self._run(f'mv {str(path)!r} {str(target)!r}')
    
    def change_mode(self, path: pathlib.Path, mode: int) -> None:
        self._run(f'chmod {mode:o} {str(path)!r}')
    
    def create_directory(self, path: pathlib.Path) -> None:
        self._run(f'mkdir -p {str(path)!r}')
    
    def delete_directory(self, path: pathlib.Path) -> None:
        self._run(f'rm -rf {str(path)!r}')
    
    def copy_directory(self, path: pathlib.Path, target: pathlib.Path) -> None:
        self._run(f'cp -r {str(path)!r} {str(target)!r}')
    
    def list_directory(self, path: pathlib.Path) -> Iterator[str]:
        return self._read_string(f'ls -1 {str(path)!r}').splitlines()
    
    @contextlib.contextmanager
    def inside_directory(self, path: pathlib.Path) -> ContextManager[None]:
        try:
            source = self._read_string('pwd')
            self._run(f'cd {path!r}')
            yield
        finally:
            self._run(f'cd {source!r}')
    
    def read(self, path: pathlib.Path, size: int, offset: int) -> bytes:
        if size is None and offset is None:
            command = f'cat {str(path)!r}'
        elif size is not None:
            command = f'head -c {size} {str(path)!r}'
        elif offset is not None:
            command = f'tail -c +{offset} {str(path)!r}'
        else:
            command = f'tail -c +{offset} {str(path)!r} | head -c {size}'
        return self._read(command)
    
    def read_chunks(self, path: pathlib.Path, size: int, offset: int) -> Iterator[bytes]:
        if offset is not None:
            command = f'tail -c +{offset} {str(path)!r}'
        else:
            command = f'cat {str(path)!r}'
        yield from self._read_chunks(command, size)
        
    def write(self, path: pathlib.Path, data: bytes, offset: int, truncate: bool) -> None:
        command = self._write_command(path, offset, truncate)
        self._write(command, data)
    
    def write_chunks(
            self,
            path: pathlib.Path,
            chunks: Iterable[bytes],
            offset: int,
            truncate: bool,
    ) -> None:
        command = self._write_command(path, offset, truncate)
        self._write_chunks(command, chunks)
        
    def execute(
            self,
            path: pathlib.Path,
            arguments: Iterable[str],
            stdin: bytes,
            timeout: float,
    ) -> tuple[int, bytes, bytes]:
        raise NotImplementedError()

    def delete_file(self, path: pathlib.Path) -> None:
        self._run(f'rm {path!r}')
    
    def copy_file(self, path: pathlib.Path, target: pathlib.Path) -> None:
        self._run(f'cp {path!r} {target!r}')
    
    def archive(self, path: pathlib.Path, target: pathlib.Path, format: str) -> None:
        if format == 'zip':
            with self.inside_directory(path):
                self._run(f'zip -r {str(target)!r} .')
        elif format in self.tar_flags:
            flags = self.tar_flags[format]
            with self.inside_directory(path):
                self._run(f'tar -c {flags} -f {str(target)!r} .')
        else:
            raise ValueError(f'unsupported format {format!r} (expected zip, tar, gztar, bztar or xztar)')
    
    def extract(self, path: pathlib.Path, target: pathlib.Path, format: str) -> None:
        if format == 'zip':
            self._run(f'unzip {str(path)!r} -d {str(target)!r}')
        elif format in self.tar_flags:
            flags = self.tar_flags[format]
            self._run(f'tar -x {flags} -f {str(path)!r} {str(target)!r}')
        else:
            raise ValueError(f'unsupported format {format!r} (expected zip, tar, gztar, bztar or xztar)')
    
    def _write_command(self, path: pathlib.Path, offset: int, truncate: bool) -> str:
        if truncate:
            return f'cat - > {str(path)!r}'
        if offset == self.end:
            return f'cat - >> {str(path)!r}'
        return f'cat - | dd bs=1 skip={offset} conv=notrunc of={str(path)!r}'
 
    def _run(self, command: str) -> None:
        raise NotImplementedError()

    def _read(self, command: str) -> bytes:
        raise NotImplementedError()

    def _read_chunks(self, command: str, size: int) -> Iterator[bytes]:
        raise NotImplementedError()

    def _read_string(self, command: str) -> str:
        return self._read(command).decode().strip()
    
    def _write(self, command: str, data: bytes) -> None:
        raise NotImplementedError()
    
    def _write_chunks(self, command: str, chunks: Iterable[bytes]) -> None:
        raise NotImplementedError()