import signal
import time

from hextile.utils import Execution


def test_execution():
    e = Execution(1, b'stdout', b'stderr')
    assert e.exit_code == 1
    assert e.stdout == b'stdout'
    assert e.stderr == b'stderr'


def test_run():
    e = Execution.run('echo', 'Hello, world!')
    assert e.exit_code == 0
    assert e.stdout == b'Hello, world!\n'
    assert e.stderr == b''


def test_exit_code():
    e = Execution.run('bash', '-c', 'exit 1')
    assert e.exit_code == 1
    e = Execution.run('bash', '-c', 'exit 2')
    assert e.exit_code == 2


def test_stdout():
    e = Execution.run('echo', 'Hello, world!')
    assert e.stdout == b'Hello, world!\n'
    assert e.output == 'Hello, world!'
    e = Execution.run('echo', 1, 2, 3)
    assert e.stdout == b'1 2 3\n'
    assert e.output == '1 2 3'


def test_stderr():
    e = Execution.run('bash', '-c', 'echo error >&2')
    assert e.stderr == b'error\n'
    assert e.error == 'error'


def test_stdin():
    e = Execution.run('cat', '-', stdin='Hello, world!')
    assert e.stdout == b'Hello, world!'
    e = Execution.run('cat', '-', stdin=b'Hello, world!')
    assert e.stdout == b'Hello, world!'


def test_timeout():
    started = time.time()
    e = Execution.run('sleep', 3, timeout=1)
    assert e.exit_code == -signal.SIGTERM
    elapsed = time.time() - started
    assert 1 <= elapsed < 1.1


def test_sigterm_timeout():
    started = time.time()
    e = Execution.run('bash', '-c', 'trap : SIGTERM; sleep 3', timeout=1, sigterm_timeout=1)
    assert e.exit_code == -signal.SIGKILL
    elapsed = time.time() - started
    assert 2 <= elapsed < 2.1


def test_exact_timeout():
    started = time.time()
    e = Execution.run('bash', '-c', 'trap : SIGTERM; sleep 3', timeout=1, sigterm_timeout=0)
    assert e.exit_code == -signal.SIGKILL
    elapsed = time.time() - started
    assert 1 <= elapsed < 1.1