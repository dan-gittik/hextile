from __future__ import annotations

from functools import cached_property
import os
import signal
import subprocess


class Execution:

    default_timeout = None
    default_sigterm_timeout = 3.0

    def __init__(
            self,
            exit_code: int,
            stdout: bytes,
            stderr: bytes,
    ):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
    
    def __str__(self):
        if self.success:
            return f'successful execution: {self.output or "no output"}'
        return f'failed execution ({self.exit_code}): {self.error or "no error"}'
    
    def __repr__(self):
        return f'<{self}>'

    @classmethod
    def run(
            cls,
            *command: str,
            stdin: str|bytes = None,
            timeout: float = None,
            sigterm_timeout: float = None,
    ) -> Execution:
        if timeout is None:
            timeout = cls.default_timeout
        if sigterm_timeout is None:
            sigterm_timeout = cls.default_sigterm_timeout
        if isinstance(stdin, str):
            stdin = stdin.encode()
        process = subprocess.Popen(
            [str(part) for part in command],
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            preexec_fn = os.setsid,
        )
        try:
            stdout, stderr = process.communicate(stdin, timeout)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=sigterm_timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        return cls(
            exit_code = process.returncode,
            stdout = stdout,
            stderr = stderr,
        )
    
    @cached_property
    def success(self) -> bool:
        return self.exit_code == 0
    
    @cached_property
    def output(self) -> str:
        return self.stdout.decode().strip()
    
    @cached_property
    def error(self) -> str:
        return self.stderr.decode().strip()