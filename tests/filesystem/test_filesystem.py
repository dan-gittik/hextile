import os
import pathlib

import pytest

from hextile.filesystem import FileSystem, local_filesystem as fs


def test_filesystem():
    assert str(fs) == 'filesystem at local://'
    assert repr(fs) == '<filesystem at local://>'
    with pytest.raises(ValueError, match=r"unsupported URL scheme 'scheme' \(expected one of: .*\)"):
        FileSystem('scheme://')


def test_current_directory():
    assert fs.current_directory() == os.getcwd()


def test_home_directory():
    assert fs.home_directory() == os.environ['HOME']


def test_temporary_directory():
    path = fs.temporary_directory()
    assert path.startswith('/tmp')
    with path:
        assert path.exists
    assert not path.exists


def test_path():
    assert fs.path('/foo') == '/foo'
    assert fs.path('/foo/../bar') == '/bar'
    assert fs.path('/etc', exists=True) == '/etc'
    assert fs.path('/foo', exists=False) == '/foo'
    with pytest.raises(FileNotFoundError, match=r"path '/foo' does not exist"):
        fs.path('/foo', exists=True)
    with pytest.raises(FileExistsError, match=r"path '/etc' exists"):
        fs.path('/etc', exists=False)


def test_directory():
    assert fs.directory('/foo') == '/foo'
    assert fs.directory('/etc', exists=True) == '/etc'
    assert fs.directory('/foo', exists=False) == '/foo'
    with pytest.raises(FileNotFoundError, match=r"directory '/foo' does not exist"):
        fs.directory('/foo', exists=True)
    with pytest.raises(FileExistsError, match=r"directory '/etc' exists"):
        fs.directory('/etc', exists=False)
    with pytest.raises(NotADirectoryError, match=r"path '/etc/passwd' is not a directory"):
        fs.directory('/etc/passwd', exists=True)


def test_directory_create(tmp_path: pathlib.Path):
    d = tmp_path / 'd1' / 'd2' / 'd3'
    assert not d.exists()
    assert fs.directory(d, create=True) == str(d)
    assert d.exists()


def test_file():
    assert fs.file('/foo') == '/foo'
    assert fs.file('/etc/passwd', exists=True) == '/etc/passwd'
    assert fs.file('/foo', exists=False) == '/foo'
    with pytest.raises(FileNotFoundError, match=r"file '/foo' does not exist"):
        fs.file('/foo', exists=True)
    with pytest.raises(FileExistsError, match=r"file '/etc/passwd' exists"):
        fs.file('/etc/passwd', exists=False)
    with pytest.raises(IsADirectoryError, match=r"path '/etc' is not a file"):
        fs.file('/etc', exists=True)