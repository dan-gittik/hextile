import os
import pathlib

import pytest

from hextile.filesystem import FileSystem, local_filesystem as fs


def test_filesystem():
    assert str(fs) == 'filesystem at local://'
    assert repr(fs) == "FileSystem('local://')"
    with pytest.raises(ValueError, match=r"unsupported URL scheme 'scheme' \(expected one of: .*\)"):
        FileSystem('scheme://')


def test_current_directory():
    assert fs.current_directory() == os.getcwd()


def test_home_directory():
    assert fs.home_directory() == os.environ['HOME']


def test_temporary_directory():
    path = fs.temporary_directory()
    with path:
        assert path.exists()
    assert not path.exists()


def test_path(tmp_path: pathlib.Path):
    directory = tmp_path / 'directory'
    path = str(directory)
    assert fs.path(directory) == path
    assert fs.path(str(directory)) == path
    file = directory / '..' / 'file.txt'
    path = str(tmp_path / file.name)
    assert fs.path(file) == path
    assert fs.path(str(file)) == path


def test_path_exists(tmp_path: pathlib.Path):
    file1 = tmp_path / 'file1.txt'
    file1.touch()
    file2 = tmp_path / 'file2.txt'
    assert fs.path(file1, exists=True) == str(file1)
    assert fs.path(file2, exists=False) == str(file2)
    with pytest.raises(FileExistsError, match=rf'path {str(file1)!r} exists'):
        fs.path(file1, exists=False)
    with pytest.raises(FileNotFoundError, match=rf'path {str(file2)!r} does not exist'):
        fs.path(file2, exists=True)


def test_directory(tmp_path: pathlib.Path):
    directory1 = tmp_path / 'directory1'
    directory1.mkdir()
    directory2 = tmp_path / 'directory2'
    assert fs.directory(directory1, exists=True) == str(directory1)
    assert fs.directory(directory2, exists=False) == str(directory2)
    with pytest.raises(FileExistsError, match=rf'directory {str(directory1)!r} exists'):
        fs.directory(directory1, exists=False)
    with pytest.raises(FileNotFoundError, match=rf'directory {str(directory2)!r} does not exist'):
        fs.directory(directory2, exists=True)
    file = tmp_path / 'file.txt'
    file.touch()
    with pytest.raises(NotADirectoryError, match=rf'path {str(file)!r} is not a directory'):
        fs.directory(file, exists=True)


def test_directory_create(tmp_path: pathlib.Path):
    directory = tmp_path / 'd1' / 'd2' / 'd3'
    assert not directory.exists()
    assert fs.directory(directory, create=True) == str(directory)
    assert directory.exists()


def test_file(tmp_path: pathlib.Path):
    file1 = tmp_path / 'file1.txt'
    file1.touch()
    file2 = tmp_path / 'file2.txt'
    assert fs.file(file1, exists=True) == str(file1)
    assert fs.file(file2, exists=False) == str(file2)
    with pytest.raises(FileExistsError, match=rf'file {str(file1)!r} exists'):
        fs.file(file1, exists=False)
    with pytest.raises(FileNotFoundError, match=rf'file {str(file2)!r} does not exist'):
        fs.file(file2, exists=True)
    directory = tmp_path / 'directory'
    directory.mkdir()
    with pytest.raises(IsADirectoryError, match=rf'path {str(directory)!r} is not a file'):
        fs.file(directory, exists=True)