import os
import pathlib
import time

try:
    import pwd, grp
    is_windows = False
except ImportError:
    pwd = grp = None
    is_windows = True

import pytest

from hextile.filesystem import local_filesystem as fs
from hextile.utils import now, datetime_to_timestamp


skip_windows = pytest.mark.skipif(is_windows, reason='not supported on windows')


def test_path():
    path = fs.path('/directory/file.txt')
    assert str(path) == '/directory/file.txt'
    assert repr(path) == "'/directory/file.txt'"
    assert isinstance(path, str)
    assert path.startswith('/')
    assert fs.path('/directory/file.txt') is path


def test_path_context():
    with fs.temporary_directory() as path:
        assert path.exists
    assert not path.exists
    with pytest.raises(TypeError, match=r"path '/directory' is not temporary and cannot be used in a with statement"):
        with fs.path('/directory') as path:
            pass


def test_path_concatenation():
    path = fs.path('/directory')
    assert (path / 'file.txt') == '/directory/file.txt'
    assert (path / '/file.txt') == '/file.txt'
    assert (path / pathlib.Path('file.txt')) == '/directory/file.txt'
    assert (path / pathlib.Path('/file.txt')) == '/file.txt'
    assert (path / fs.path('/file.txt')) == '/file.txt'


def test_is_root():
    assert not fs.path('/directory').is_root
    assert fs.path('/').is_root


def test_directory():
    path = fs.path('/directory/file.txt')
    assert path.directory == '/directory'
    assert path.directory.directory == '/'


def test_basename():
    assert fs.path('/directory').basename == 'directory'
    assert fs.path('/directory/file.txt').basename == 'file.txt'
    assert fs.path('/directory/archive.tar.gz').basename == 'archive.tar.gz'


def test_name():
    assert fs.path('/directory').name == 'directory'
    assert fs.path('/directory/file.txt').name == 'file'
    assert fs.path('/directory/archive.tar.gz').name == 'archive'


def test_extension():
    assert fs.path('/directory').extension == ''
    assert fs.path('/directory/file.txt').extension == '.txt'
    assert fs.path('/directory/archive.tar.gz').extension == '.tar.gz'


def test_exists(tmp_path: pathlib.Path):
    directory = tmp_path / 'directory'
    path = fs.path(directory)
    assert not directory.exists()
    assert not path.exists
    path.create_directory()
    assert directory.exists()
    assert path.exists
    path.delete()
    assert not directory.exists()
    assert not path.exists
    file = tmp_path / 'file.txt'
    path = fs.path(file)
    assert not file.exists()
    assert not path.exists
    path.write_text('Hello, world!')
    assert file.exists()
    assert path.exists
    path.delete()
    assert not file.exists()
    assert not path.exists


def test_is_directory(tmp_path: pathlib.Path):
    directory = tmp_path / 'directory'
    path = fs.path(directory)
    assert not directory.exists()
    assert not path.is_directory
    directory.mkdir()
    assert directory.is_dir()
    assert path.is_directory
    directory.rmdir()
    assert not directory.exists()
    assert not path.is_directory
    file = tmp_path / 'file.txt'
    path = fs.path(file)
    assert not file.exists()
    assert not path.is_directory
    file.touch()
    assert file.is_file()
    assert not path.is_directory
    file.unlink()
    assert not file.exists()
    assert not path.is_directory


def test_is_file(tmp_path: pathlib.Path):
    directory = tmp_path / 'directory'
    path = fs.path(directory)
    assert not directory.exists()
    assert not path.is_file
    directory.mkdir()
    assert directory.is_dir()
    assert not path.is_file
    directory.rmdir()
    assert not directory.exists()
    assert not path.is_file
    file = tmp_path / 'file.txt'
    path = fs.path(file)
    assert not file.exists()
    assert not path.is_file
    file.touch()
    assert file.is_file()
    assert path.is_file
    file.unlink()
    assert not file.exists()
    assert not path.is_file


def test_size(tmp_path: pathlib.Path):
    directory = tmp_path / 'directory'
    directory.mkdir()
    path = fs.path(directory)
    assert path.size is None
    file = tmp_path / 'file.txt'
    file.write_text('Hello, world!')
    path = fs.path(file)
    assert path.size == 13


def test_time(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    create_time = datetime_to_timestamp(now())
    file.touch()
    path = fs.path(file)
    assert path.timestamp - create_time < 0.1
    prev_timestamp = path.timestamp
    time.sleep(0.1)
    write_time = datetime_to_timestamp(now())
    file.write_text('Hello, world!')
    assert path.timestamp > prev_timestamp
    assert path.timestamp - write_time < 0.1


def test_datetime(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    create_datetime = now()
    file.touch()
    path = fs.path(file)
    assert (path.datetime - create_datetime).total_seconds() < 0.1
    prev_datetime = path.datetime
    time.sleep(0.1)
    write_datetime = now()
    file.write_text('Hello, world!')
    assert path.datetime > prev_datetime
    assert (path.datetime - write_datetime).total_seconds() < 0.1


@skip_windows
def test_owner_id(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    path = fs.path(file)
    assert path.owner_id == os.getuid()


@skip_windows
def test_group_id(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    path = fs.path(file)
    assert path.group_id == os.getgid()


@skip_windows
def test_owner_name(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    path = fs.path(file)
    assert path.owner_name == pwd.getpwuid(os.getuid()).pw_name


@skip_windows
def test_group_name(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    path = fs.path(file)
    assert path.group_name == grp.getgrgid(os.getgid()).gr_name


def test_owner_readable(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    file.chmod(0o000)
    path = fs.path(file)
    assert not path.owner_readable
    file.chmod(0o400)
    assert path.owner_readable
    path.owner_readable = False
    assert file.stat().st_mode & 0o777 == 0o000
    path.owner_readable = True
    assert file.stat().st_mode & 0o777 == 0o400
    assert path.read_text() == ''
    path.owner_readable = False
    with pytest.raises(PermissionError):
        path.read_text()


def test_owner_writable(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    file.chmod(0o000)
    path = fs.path(file)
    assert not path.owner_writable
    file.chmod(0o200)
    assert path.owner_writable
    path.owner_writable = False
    assert file.stat().st_mode & 0o777 == 0o000
    path.owner_writable = True
    assert file.stat().st_mode & 0o777 == 0o200
    path.write_text('Hello, world!')
    path.owner_writable = False
    with pytest.raises(PermissionError):
        path.write_text('Hello, world!')


def test_owner_executable(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    file.chmod(0o000)
    path = fs.path(file)
    assert not path.owner_executable
    file.chmod(0o100)
    assert path.owner_executable
    path.owner_executable = False
    assert file.stat().st_mode & 0o777 == 0o000
    path.owner_executable = True
    assert file.stat().st_mode & 0o777 == 0o100
    path.owner_readable = path.owner_writable = True
    file.write_text('#!/bin/sh\necho "Hello, world!"\n')
    assert path.execute().exit_code == 0
    path.owner_executable = False
    with pytest.raises(PermissionError):
        path.execute()


def test_owner_permissions(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    file.chmod(0o700)
    path = fs.path(file)
    assert path.owner_permissions == 'rwx'
    path.owner_readable = False
    assert path.owner_permissions == 'wx'
    path.owner_writable = False
    assert path.owner_permissions == 'x'
    path.owner_executable = False
    assert path.owner_permissions == ''
    path.owner_permissions = 'x'
    assert path.owner_executable
    path.owner_permissions = 'rw'
    assert path.owner_readable
    assert path.owner_writable
    assert not path.owner_executable


def test_group_readable(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    file.chmod(0o000)
    path = fs.path(file)
    assert not path.group_readable
    file.chmod(0o040)
    assert path.group_readable
    path.group_readable = False
    assert file.stat().st_mode & 0o777 == 0o000
    path.group_readable = True
    assert file.stat().st_mode & 0o777 == 0o040


def test_group_writable(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    file.chmod(0o000)
    path = fs.path(file)
    assert not path.group_writable
    file.chmod(0o020)
    assert path.group_writable
    path.group_writable = False
    assert file.stat().st_mode & 0o777 == 0o000
    path.group_writable = True
    assert file.stat().st_mode & 0o777 == 0o020


def test_group_executable(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    file.chmod(0o000)
    path = fs.path(file)
    assert not path.group_executable
    file.chmod(0o010)
    assert path.group_executable
    path.group_executable = False
    assert file.stat().st_mode & 0o777 == 0o000
    path.group_executable = True
    assert file.stat().st_mode & 0o777 == 0o010


def test_group_permissions(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    file.chmod(0o070)
    path = fs.path(file)
    assert path.group_permissions == 'rwx'
    path.group_readable = False
    assert path.group_permissions == 'wx'
    path.group_writable = False
    assert path.group_permissions == 'x'
    path.group_executable = False
    assert path.group_permissions == ''
    path.group_permissions = 'x'
    assert path.group_executable
    path.group_permissions = 'rw'
    assert path.group_readable
    assert path.group_writable
    assert not path.group_executable


def test_other_readable(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    file.chmod(0o000)
    path = fs.path(file)
    assert not path.other_readable
    file.chmod(0o004)
    assert path.other_readable
    path.other_readable = False
    assert file.stat().st_mode & 0o777 == 0o000
    path.other_readable = True
    assert file.stat().st_mode & 0o777 == 0o004


def test_other_writable(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    file.chmod(0o000)
    path = fs.path(file)
    assert not path.other_writable
    file.chmod(0o002)
    assert path.other_writable
    path.other_writable = False
    assert file.stat().st_mode & 0o777 == 0o000
    path.other_writable = True
    assert file.stat().st_mode & 0o777 == 0o002


def test_other_executable(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    file.chmod(0o000)
    path = fs.path(file)
    assert not path.other_executable
    file.chmod(0o001)
    assert path.other_executable
    path.other_executable = False
    assert file.stat().st_mode & 0o777 == 0o000
    path.other_executable = True
    assert file.stat().st_mode & 0o777 == 0o001


def test_other_permissions(tmp_path: pathlib.Path):
    file = tmp_path / 'file.txt'
    file.touch()
    file.chmod(0o007)
    path = fs.path(file)
    assert path.other_permissions == 'rwx'
    path.other_readable = False
    assert path.other_permissions == 'wx'
    path.other_writable = False
    assert path.other_permissions == 'x'
    path.other_executable = False
    assert path.other_permissions == ''
    path.other_permissions = 'x'
    assert path.other_executable
    path.other_permissions = 'rw'
    assert path.other_readable
    assert path.other_writable
    assert not path.other_executable


def test_rename(tmp_path: pathlib.Path):
    file = tmp_path / '1'
    file.touch()
    one = fs.path(file)
    two = one.rename('2')
    assert not one.exists
    assert two.exists


def test_rename_into_directory(tmp_path: pathlib.Path):
    directory = tmp_path / 'directory'
    directory.mkdir()
    file = tmp_path / 'file.txt'
    file.touch()
    path = fs.path(file)
    with pytest.raises(FileExistsError, match=rf'path {str(directory)!r} already exists'):
        path.rename('directory', into_directory=False, overwrite=False)
    old, path = path, path.rename('directory', into_directory=True)
    assert not old.exists
    assert path.exists
    assert path.endswith('/directory/file.txt')
    path = path.rename('..', into_directory=True)
    assert path.directory is fs.path(tmp_path)


def test_rename_overwrite(tmp_path: pathlib.Path):
    one = tmp_path / '1'
    one.write_text('1')
    two = tmp_path / '2'
    two.write_text('2')
    path = fs.path(one)
    with pytest.raises(FileExistsError, match=rf'path {str(two)!r} already exists'):
        path.rename(two, overwrite=False)
    old, path = path, path.rename(two, overwrite=True)
    assert not old.exists
    assert path.read_text() == '1'


def test_rename_overwrite_directory(tmp_path: pathlib.Path):
    directory = tmp_path / 'directory'
    directory.mkdir()
    file = tmp_path / 'file.txt'
    file.write_text('Hello, world!')
    path = fs.path(file)
    with pytest.raises(FileExistsError, match=rf'path {str(directory)!r} already exists'):
        path.rename(directory, into_directory=False, overwrite=False)
    old, path = path, path.rename(directory, into_directory=False, overwrite=True)
    assert not old.exists
    assert path.read_text() == 'Hello, world!'


def test_with_basename():
    pass


def test_with_name():
    pass


def test_with_extension():
    pass


def test_create_directory():
    pass


def test_list():
    pass


def test_walk():
    pass


def test_walk_max_depth():
    pass


def test_walk_dfs():
    pass


def test_walk_bfs():
    pass


def test_skip():
    pass


def test_inside():
    pass


def test_read():
    pass


def test_read_size():
    pass


def test_read_offset():
    pass


def test_read_chunks():
    pass


def test_read_chunks_size():
    pass


def test_read_chunks_offset():
    pass


def test_read_text():
    pass


def test_read_text_encoding():
    pass


def test_read_lines():
    pass


def test_read_lines_linbreak():
    pass


def test_read_lines_encoding():
    pass


def test_write():
    pass


def test_write_offset():
    pass


def test_write_append():
    pass


def test_write_truncate():
    pass


def test_write_chunks():
    pass


def test_write_chunks_offset():
    pass


def test_write_chunks_append():
    pass


def test_write_chunks_truncate():
    pass


def test_write_text():
    pass


def test_write_text_append():
    pass


def test_write_text_truncate():
    pass # ?


def test_write_text_encoding():
    pass


def test_write_lines():
    pass


def test_write_lines_linebreak():
    pass


def test_write_lines_append():
    pass


def test_write_lines_truncate():
    pass # ?


def test_write_lines_encoding():
    pass


def test_execute():
    pass


def test_delete_directory():
    pass


def test_delete_file():
    pass


def test_copy_directory():
    pass


def test_copy_file():
    pass


def test_copy_into_directory():
    pass


def test_copy_overwrite():
    pass


def test_copy_overwrite_directory():
    pass


def test_archive():
    pass


def test_extract():
    pass