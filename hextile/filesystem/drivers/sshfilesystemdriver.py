from __future__ import annotations
from typing import Iterable, Iterator

import pathlib

try:
    import paramiko
    import paramiko.channel
except ImportError:
    paramiko = None

from .shellfilesystemdriver import ShellFileSystemDriver


class SSHFileSystemDriver(ShellFileSystemDriver):
    
    scheme = 'SSH'
    default_port = 22

    def on_init(self):
        if paramiko is None:
            raise RuntimeError('paramiko is not installed')
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        public_key = self.url.fragment and paramiko.RSAKey.from_private_key_file(self.url.fragment)
        self.client.connect(
            hostname = self.url.host,
            port = self.url.port or self.default_port,
            username = self.url.username,
            password = self.url.password,
            pkey = public_key,
        )
        if self.url.path:
            self.client.exec_command(f'cd {self.url.path}')
    
    def execute(
            self,
            path: pathlib.Path,
            arguments: Iterable[str],
            stdin: bytes,
            timeout: float,
    ) -> tuple[int, bytes, bytes]:
        stdin_, stdout, stderr = self.client.exec_command(f' '.join(map([path, *arguments], str)), timeout=timeout)
        if stdin:
            stdin_.write(stdin)
        exit_code = stdout.channel.recv_exit_status()
        return exit_code, stdout.read(), stderr.read()
 
    def _run(self, command: str) -> None:
        self._execute(command)

    def _read(self, command: str) -> bytes:
        return self._execute(command).read()
    
    def _read_chunks(self, command: str, size: int) -> Iterator[bytes]:
        stdout = self._execute(command, check_status=False)
        while True:
            chunk = stdout.read(size)
            if not chunk:
                break
            yield chunk
    
    def _write(self, command: str, data: bytes) -> None:
        self._execute(command, input=data)
    
    def _write_chunks(self, command: str, chunks: Iterable[bytes]) -> None:
        self._execute(command, input=chunks)

    def _execute(
            self,
            command: str,
            input: bytes|Iterable[bytes] = None,
            timeout: float = None,
            check_status: bool = True,
    ) -> paramiko.channel.ChannelFile:
        stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
        if isinstance(input, bytes):
            stdin.write(stdin)
        elif input is not None:
            for chunk in input:
                stdin.write(chunk)
        if check_status:
            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0:
                error = stderr.read().decode().strip()
                raise ValueError(f'failed to execute {command!r}: {error}')
        return stdout