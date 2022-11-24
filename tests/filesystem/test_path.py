import io
import os
import pathlib
import subprocess
import tarfile
import time
import zipfile

try:
    import pwd, grp
    unix_security = True
except ImportError:
    pwd = grp = None
    unix_security = False

import pytest

from hextile.filesystem import Path
from hextile.utils import now, datetime_to_timestamp
from tests.filesystem.conftest import Context


if_unix_security = pytest.mark.skipif(not unix_security, reason='unix security features are not available')


def test_path(c: Context):
    path = c.fs.path(c.file)
    assert str(path) == str(c.file)
    assert repr(path) == repr(str(c.file))
    assert isinstance(path, str)
    assert c.fs.path(c.file) is path


def test_path_context(c: Context):
    with c.fs.temporary_directory() as path:
        assert path.exists()
    assert not path.exists()
    with pytest.raises(TypeError, match=rf'path {str(c.directory)!r} is not temporary and cannot be used in a with statement'):
        with c.fs.path(c.directory) as path:
            pass


def test_path_concatenation(c: Context):
    path = c.fs.path(c.root)
    assert path / c.file_name == str(c.file)
    assert path / str(c.directory) == str(c.directory)
    assert path / pathlib.Path(c.file_name) == str(c.file)
    assert path / c.directory == str(c.directory)
    assert path / c.fs.path(c.file) is c.fs.path(c.file)


def test_drive(c: Context):
    assert c.fs.path(c.file).drive == c.root.drive
    assert c.fs.path(c.directory).drive == c.root.drive


def test_is_root(c: Context):
    assert not c.fs.path(c.file).is_root
    assert not c.fs.path(c.directory).is_root
    assert c.fs.path('/').is_root


def test_directory(c: Context):
    path = c.fs.path(c.file1)
    assert path.directory is c.fs.path(c.directory1)
    assert path.directory.directory is c.fs.path(c.root)
    assert c.fs.path(c.no_file).directory is c.fs.path(c.root)


def test_basename(c: Context):
    assert c.fs.path('directory').basename == 'directory'
    assert c.fs.path('file.txt').basename == 'file.txt'
    assert c.fs.path('archive.tar.gz').basename == 'archive.tar.gz'


def test_name(c: Context):
    assert c.fs.path('directory').name == 'directory'
    assert c.fs.path('file.txt').name == 'file'
    assert c.fs.path('archive.tar.gz').name == 'archive'


def test_extension(c: Context):
    assert c.fs.path('directory').extension == ''
    assert c.fs.path('file.txt').extension == '.txt'
    assert c.fs.path('archive.tar.gz').extension == '.tar.gz'


def test_exists(c: Context):
    assert not c.fs.path(c.no_file).exists()
    assert not c.fs.path(c.no_directory).exists()
    assert c.fs.path(c.file).exists()
    assert c.fs.path(c.directory).exists()


def test_is_directory(c: Context):
    assert not c.fs.path(c.no_file).is_directory()
    assert not c.fs.path(c.no_directory).is_directory()
    assert not c.fs.path(c.file).is_directory()
    assert c.fs.path(c.directory).is_directory()


def test_is_file(c: Context):
    assert not c.fs.path(c.no_file).is_file()
    assert not c.fs.path(c.no_directory).is_file()
    assert c.fs.path(c.file).is_file()
    assert not c.fs.path(c.directory).is_file()


def test_size(c: Context):
    assert c.fs.path(c.file).size() == len(c.text)
    assert c.fs.path(c.directory).size() is None
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).size()


def test_time(c: Context):
    path = c.fs.path(c.file)
    create_time = datetime_to_timestamp(now())
    assert create_time - path.timestamp() < 0.1
    time.sleep(0.1)
    change_time = datetime_to_timestamp(now())
    c.write(c.text)
    assert path.timestamp() - create_time > 0.1
    assert path.timestamp() - change_time < 0.1
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).timestamp()


def test_datetime(c: Context):
    path = c.fs.path(c.file)
    create_datetime = now()
    assert (create_datetime - path.datetime()).total_seconds() < 0.1
    time.sleep(0.1)
    change_datetime = now()
    c.write(c.text)
    assert (path.datetime() - create_datetime).total_seconds() > 0.1
    assert (path.datetime() - change_datetime).total_seconds() < 0.1
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).datetime()


@if_unix_security
def test_owner_id(c: Context):
    owner_id = os.getuid()
    assert c.fs.path(c.file).owner_id() == owner_id
    assert c.fs.path(c.directory).owner_id() == owner_id
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).owner_id()


@if_unix_security
def test_group_id(c: Context):
    group_id = os.getgid()
    assert c.fs.path(c.file).group_id() == group_id
    assert c.fs.path(c.directory).group_id() == group_id
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).group_id()


@if_unix_security
def test_owner_name(c: Context):
    owner_name = pwd.getpwuid(os.getuid()).pw_name
    assert c.fs.path(c.file).owner_name() == owner_name
    assert c.fs.path(c.directory).owner_name() == owner_name
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).owner_name()


@if_unix_security
def test_group_name(c: Context):
    group_name = grp.getgrgid(os.getgid()).gr_name
    assert c.fs.path(c.file).group_name() == group_name
    assert c.fs.path(c.directory).group_name() == group_name
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).group_name()


@if_unix_security
def test_owner_readable(c: Context):
    assert c.fs.path(c.owner_readable).owner_readable()
    assert not c.fs.path(c.owner_writable).owner_readable()
    assert not c.fs.path(c.owner_executable).owner_readable()
    assert not c.fs.path(c.group_readable).owner_readable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).owner_readable()


@if_unix_security
def test_set_owner_readable(c: Context):
    path = c.fs.path(c.owner_readable)
    assert path.owner_readable()
    path.set_owner_readable(False)
    assert not path.owner_readable()
    path.set_owner_readable(True)
    assert path.owner_readable()
    path.read()
    path.set_owner_readable(False)
    with pytest.raises(PermissionError):
        path.read()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).set_owner_readable(True)


@if_unix_security
def test_owner_writable(c: Context):
    assert not c.fs.path(c.owner_readable).owner_writable()
    assert c.fs.path(c.owner_writable).owner_writable()
    assert not c.fs.path(c.owner_readable).owner_writable()
    assert not c.fs.path(c.group_writable).owner_writable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).owner_writable()


@if_unix_security
def test_set_owner_writable(c: Context):
    path = c.fs.path(c.owner_writable)
    path.set_owner_writable(False)
    assert not path.owner_writable()
    path.set_owner_writable(True)
    assert path.owner_writable()
    path.write(b'')
    path.set_owner_writable(False)
    with pytest.raises(PermissionError):
        path.write(b'')
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).set_owner_writable(True)


@if_unix_security
def test_owner_executable(c: Context):
    assert not c.fs.path(c.owner_readable).owner_executable()
    assert not c.fs.path(c.owner_writable).owner_executable()
    assert c.fs.path(c.owner_executable).owner_executable()
    assert not c.fs.path(c.group_executable).owner_executable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).owner_executable()


@if_unix_security
def test_set_owner_executable(c: Context):
    path = c.fs.path(c.owner_executable)
    path.set_owner_executable(False)
    assert not path.owner_executable()
    path.set_owner_executable(True)
    assert path.owner_executable()
    script = c.fs.path(c.script)
    script.execute()
    script.set_owner_executable(False)
    with pytest.raises(PermissionError):
        script.execute()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).set_owner_executable(True)


@if_unix_security
def test_owner_permissions(c: Context):
    assert c.fs.path(c.owner_readable).owner_permissions() == 'r'
    assert c.fs.path(c.owner_writable).owner_permissions() == 'w'
    assert c.fs.path(c.owner_executable).owner_permissions() == 'x'
    assert c.fs.path(c.owner_all).owner_permissions() == 'rwx'
    assert c.fs.path(c.none).owner_permissions() == ''
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).owner_permissions()


@if_unix_security
def test_set_owner_permissions(c: Context):
    path = c.fs.path(c.none)
    path.set_owner_permissions('rw')
    assert path.owner_readable()
    assert path.owner_writable()
    assert not path.owner_executable()
    path.set_owner_permissions('wx')
    assert not path.owner_readable()
    assert path.owner_writable()
    assert path.owner_executable()
    path = c.fs.path(c.owner_all)
    path.set_owner_permissions('')
    assert not path.owner_readable()
    assert not path.owner_writable()
    assert not path.owner_executable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).set_owner_permissions('rwx')


@if_unix_security
def test_group_readable(c: Context):
    assert c.fs.path(c.group_readable).group_readable()
    assert not c.fs.path(c.group_writable).group_readable()
    assert not c.fs.path(c.group_executable).group_readable()
    assert not c.fs.path(c.other_readable).group_readable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).group_readable()


@if_unix_security
def test_set_group_readable(c: Context):
    path = c.fs.path(c.group_readable)
    assert path.group_readable()
    path.set_group_readable(False)
    assert not path.group_readable()
    path.set_group_readable(True)
    assert path.group_readable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).set_group_readable(True)


@if_unix_security
def test_group_writable(c: Context):
    print(c.group_writable.stat())
    assert not c.fs.path(c.group_readable).group_writable()
    assert c.fs.path(c.group_writable).group_writable()
    assert not c.fs.path(c.group_readable).group_writable()
    assert not c.fs.path(c.other_writable).group_writable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).group_writable()


@if_unix_security
def test_set_group_writable(c: Context):
    path = c.fs.path(c.group_writable)
    path.set_group_writable(False)
    assert not path.group_writable()
    path.set_group_writable(True)
    assert path.group_writable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).set_group_writable(True)


@if_unix_security
def test_group_executable(c: Context):
    assert not c.fs.path(c.group_readable).group_executable()
    assert not c.fs.path(c.group_writable).group_executable()
    assert c.fs.path(c.group_executable).group_executable()
    assert not c.fs.path(c.other_executable).group_executable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).group_executable()


@if_unix_security
def test_set_group_executable(c: Context):
    path = c.fs.path(c.group_executable)
    path.set_group_executable(False)
    assert not path.group_executable()
    path.set_group_executable(True)
    assert path.group_executable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).set_group_executable(True)


@if_unix_security
def test_group_permissions(c: Context):
    assert c.fs.path(c.group_readable).group_permissions() == 'r'
    assert c.fs.path(c.group_writable).group_permissions() == 'w'
    assert c.fs.path(c.group_executable).group_permissions() == 'x'
    assert c.fs.path(c.group_all).group_permissions() == 'rwx'
    assert c.fs.path(c.none).group_permissions() == ''
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).group_permissions()


@if_unix_security
def test_set_group_permissions(c: Context):
    path = c.fs.path(c.none)
    path.set_group_permissions('rw')
    assert path.group_readable()
    assert path.group_writable()
    assert not path.group_executable()
    path.set_group_permissions('wx')
    assert not path.group_readable()
    assert path.group_writable()
    assert path.group_executable()
    path = c.fs.path(c.group_all)
    path.set_group_permissions('')
    assert not path.group_readable()
    assert not path.group_writable()
    assert not path.group_executable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).set_group_permissions('rwx')


@if_unix_security
def test_other_readable(c: Context):
    assert c.fs.path(c.other_readable).other_readable()
    assert not c.fs.path(c.other_writable).other_readable()
    assert not c.fs.path(c.other_executable).other_readable()
    assert not c.fs.path(c.owner_readable).other_readable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).other_readable()


@if_unix_security
def test_set_other_readable(c: Context):
    path = c.fs.path(c.other_readable)
    assert path.other_readable()
    path.set_other_readable(False)
    assert not path.other_readable()
    path.set_other_readable(True)
    assert path.other_readable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).set_other_readable(True)


@if_unix_security
def test_other_writable(c: Context):
    assert not c.fs.path(c.other_readable).other_writable()
    assert c.fs.path(c.other_writable).other_writable()
    assert not c.fs.path(c.other_readable).other_writable()
    assert not c.fs.path(c.owner_writable).other_writable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).other_writable()


@if_unix_security
def test_set_other_writable(c: Context):
    path = c.fs.path(c.other_writable)
    path.set_other_writable(False)
    assert not path.other_writable()
    path.set_other_writable(True)
    assert path.other_writable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).set_other_writable(True)


@if_unix_security
def test_other_executable(c: Context):
    assert not c.fs.path(c.other_readable).other_executable()
    assert not c.fs.path(c.other_writable).other_executable()
    assert c.fs.path(c.other_executable).other_executable()
    assert not c.fs.path(c.owner_executable).other_executable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).other_executable()


@if_unix_security
def test_set_other_executable(c: Context):
    path = c.fs.path(c.other_executable)
    path.set_other_executable(False)
    assert not path.other_executable()
    path.set_other_executable(True)
    assert path.other_executable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).set_other_executable(True)


@if_unix_security
def test_other_permissions(c: Context):
    assert c.fs.path(c.other_readable).other_permissions() == 'r'
    assert c.fs.path(c.other_writable).other_permissions() == 'w'
    assert c.fs.path(c.other_executable).other_permissions() == 'x'
    assert c.fs.path(c.other_all).other_permissions() == 'rwx'
    assert c.fs.path(c.none).other_permissions() == ''
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).other_permissions()


@if_unix_security
def test_set_other_permissions(c: Context):
    path = c.fs.path(c.none)
    path.set_other_permissions('rw')
    assert path.other_readable()
    assert path.other_writable()
    assert not path.other_executable()
    path.set_other_permissions('wx')
    assert not path.other_readable()
    assert path.other_writable()
    assert path.other_executable()
    path = c.fs.path(c.other_all)
    path.set_other_permissions('')
    assert not path.other_readable()
    assert not path.other_writable()
    assert not path.other_executable()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).set_other_permissions('rwx')


def test_with_basename(c: Context):
    root = c.fs.path(c.root)
    assert (root / 'file.txt').with_basename('archive.tar.gz') is root / 'archive.tar.gz'


def test_with_name(c: Context):
    root = c.fs.path(c.root)
    assert (root / 'file.txt').with_name('file1') is root / 'file1.txt'


def test_with_extension(c: Context):
    root = c.fs.path(c.root)
    assert (root / 'file.txt').with_extension('.json') is root / 'file.json'


def test_create_directory(c: Context):
    path = c.fs.path(c.no_directory)
    assert not path.exists()
    path.create_directory()
    assert path.is_directory()
    path = c.fs.path(c.directory)
    path.create_directory()
    path = c.fs.path(c.root) / 'd1' / 'd2' / 'd3'
    path.create_directory()
    assert path.is_directory()
    with pytest.raises(FileExistsError):
        c.fs.path(c.file).create_directory()


def test_list(c: Context):
    assert list(c.fs.path(c.directory).list()) == []
    assert list(c.fs.path(c.directory1).list()) == [
        c.fs.path(c.directory2),
        c.fs.path(c.file1),
        c.fs.path(c.file2),
    ]
    with pytest.raises(FileNotFoundError):
        next(c.fs.path(c.no_directory).list())
    with pytest.raises(NotADirectoryError):
        next(c.fs.path(c.file).list())


def test_walk(c: Context):
    assert list(c.fs.path(c.directory).walk()) == []
    assert set(c.fs.path(c.directory1).walk()) == {
        c.fs.path(c.directory2),
        c.fs.path(c.directory3),
        c.fs.path(c.file1),
        c.fs.path(c.file2),
        c.fs.path(c.file3),
        c.fs.path(c.file4),
        c.fs.path(c.file5),
        c.fs.path(c.file6),
    }
    with pytest.raises(FileNotFoundError):
        next(c.fs.path(c.no_directory).walk())
    with pytest.raises(NotADirectoryError):
        next(c.fs.path(c.file).walk())


def test_walk_max_depth(c: Context):
    path = c.fs.path(c.directory1)
    assert list(path.walk(max_depth=0)) == []
    assert set(path.walk(max_depth=1)) == {
        c.fs.path(c.directory2),
        c.fs.path(c.file1),
        c.fs.path(c.file2),
    }
    assert set(path.walk(max_depth=2)) == {
        c.fs.path(c.directory2),
        c.fs.path(c.directory3),
        c.fs.path(c.file1),
        c.fs.path(c.file2),
        c.fs.path(c.file3),
        c.fs.path(c.file4),
    }


def test_walk_dfs(c: Context):
    assert list(c.fs.path(c.directory1).walk(depth_first=True)) == [
        c.fs.path(c.directory2),
        c.fs.path(c.directory3),
        c.fs.path(c.file5),
        c.fs.path(c.file6),
        c.fs.path(c.file3),
        c.fs.path(c.file4),
        c.fs.path(c.file1),
        c.fs.path(c.file2),
    ]


def test_walk_bfs(c: Context):
    assert list(c.fs.path(c.directory1).walk(depth_first=False)) == [
        c.fs.path(c.directory2),
        c.fs.path(c.file1),
        c.fs.path(c.file2),
        c.fs.path(c.directory3),
        c.fs.path(c.file3),
        c.fs.path(c.file4),
        c.fs.path(c.file5),
        c.fs.path(c.file6),
    ]


def test_skip(c: Context):
    entries = set()
    for entry in c.fs.path(c.directory1).walk():
        if entry.name == c.directory2_name:
            entry.skip()
        entries.add(entry)
    assert entries == {
        c.fs.path(c.file1),
        c.fs.path(c.file2),
        c.fs.path(c.directory2),
    }
    with pytest.raises(TypeError, match=rf'path {str(c.directory)!r} was not created in a directory walk and cannot be skipped'):
        c.fs.path(c.directory).skip()
 

def test_inside(c: Context):
    with c.fs.path(c.directory).inside():
        process = subprocess.run(['pwd'], capture_output=True)
        assert process.stdout.decode().strip() == str(c.directory)
    with pytest.raises(FileNotFoundError):
        with c.fs.path(c.no_directory).inside():
            pass
    with pytest.raises(NotADirectoryError):
        with c.fs.path(c.file).inside():
            pass


def test_read(c: Context):
    assert c.fs.path(c.file).read() == c.text.encode()
    assert c.fs.path(c.long).read() == c.binary
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).read()
    with pytest.raises(IsADirectoryError):
        c.fs.path(c.directory).read()


def test_read_size(c: Context):
    assert c.fs.path(c.file).read(1) == c.text[0].encode()
    assert c.fs.path(c.file).read(5) == c.text[:5].encode()
    assert c.fs.path(c.long).read(1024) == c.binary[:1024]


def test_read_offset(c: Context):
    assert c.fs.path(c.file).read(offset=1) == c.text[1:].encode()
    assert c.fs.path(c.long).read(offset=5120) == c.binary[5120:]
    assert c.fs.path(c.long).read(1024, offset=5120) == c.binary[5120:6144]


def test_read_chunks(c: Context):
    assert b''.join(c.fs.path(c.long).read_chunks()) == c.binary
    with pytest.raises(FileNotFoundError):
        next(c.fs.path(c.no_file).read_chunks())
    with pytest.raises(IsADirectoryError):
        next(c.fs.path(c.directory).read_chunks())


def test_read_chunks_size(c: Context):
    assert len(list(c.fs.path(c.long).read_chunks(1024))) == len(c.binary) / 1024


def test_read_chunks_offset(c: Context):
    path = c.fs.path(c.long)
    assert len(list(path.read_chunks(1024, offset=5120))) == len(c.binary) / 1024 - 5


def test_read_text(c: Context):
    assert c.fs.path(c.file).read_text() == c.text
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).read_text()
    with pytest.raises(IsADirectoryError):
        c.fs.path(c.directory).read_text()


def test_read_text_encoding(c: Context):
    assert c.fs.path(c.long).read_text('latin1') == c.binary.decode('latin1')
    assert c.fs.path(c.long).read_text('utf8', 'replace') == c.binary.decode(errors='replace')


def test_read_lines(c: Context):
    lines = ['line 1', 'line2', '', 'line3']
    c.write('\n'.join(lines))
    assert list(c.fs.path(c.file).read_lines()) == lines
    c.write('\n' + '\n'.join(lines) + '\n')
    assert list(c.fs.path(c.file).read_lines()) == ['', *lines, '']
    c.write('')
    assert list(c.fs.path(c.file).read_lines()) == ['']
    with pytest.raises(FileNotFoundError):
        next(c.fs.path(c.no_file).read_lines())
    with pytest.raises(IsADirectoryError):
        next(c.fs.path(c.directory).read_lines())


def test_read_lines_linbreak(c: Context):
    lines = ['line1', 'line2', '', 'line3']
    separator = '...'
    c.write(separator.join(lines))
    assert list(c.fs.path(c.file).read_lines(linebreak=separator)) == lines
    c.write('')
    assert list(c.fs.path(c.file).read_lines(linebreak=separator)) == ['']


def test_read_lines_encoding(c: Context):
    lines = ['\x80\x81\x82', '\x83\x84\x85']
    c.write('\n'.join(lines).encode('latin1'))
    assert list(c.fs.path(c.file).read_lines('latin1')) == lines


def test_write(c: Context):
    data = os.urandom(1024)
    c.fs.path(c.long).write(data)
    assert c.read() == data
    with pytest.raises(IsADirectoryError):
        c.fs.path(c.directory).write(data)


def test_write_offset(c: Context):
    data = os.urandom(1024)
    c.fs.path(c.long).write(data, offset=1024)
    assert c.read() == c.binary[:1024] + data + c.binary[2048:]


def test_write_append(c: Context):
    data = os.urandom(1024)
    c.fs.path(c.long).write(data, append=True)
    assert c.read() == c.binary + data


def test_write_truncate(c: Context):
    data = os.urandom(1024)
    c.fs.path(c.long).write(data, truncate=False)
    assert c.read() == data + c.binary[1024:]
    c.fs.path(c.long).write(data, truncate=True)
    assert c.read() == data


def test_write_invalid_arguments(c: Context):
    data = os.urandom(1024)
    path = c.fs.path(c.file)
    with pytest.raises(ValueError, match=r'cannot write data at offset 1 while also truncating the file'):
        path.write(data, offset=1, truncate=True)
    with pytest.raises(ValueError, match=r'cannot write data at offset 1 while also appending it'):
        path.write(data, offset=1, append=True)
    with pytest.raises(ValueError, match=r'cannot append data while also truncating the file'):
        path.write(data, append=True, truncate=True)


def test_write_chunks(c: Context):
    data = [os.urandom(1024) for _ in range(1024)]
    def chunks(data):
        yield from data
    c.fs.path(c.long).write_chunks(chunks(data))
    assert c.read() == b''.join(data)
    with pytest.raises(IsADirectoryError):
        c.fs.path(c.directory).write(chunks(data))


def test_write_chunks_offset(c: Context):
    data = [os.urandom(1024) for _ in range(5)]
    def chunks(data):
        yield from data
    c.fs.path(c.long).write_chunks(chunks(data), offset=5120)
    assert c.read() == c.binary[:5120] + b''.join(data) + c.binary[10240:]


def test_write_chunks_append(c: Context):
    data = [os.urandom(1024) for _ in range(5)]
    def chunks(data):
        yield from data
    c.fs.path(c.long).write_chunks(chunks(data), append=True)
    assert c.read() == c.binary + b''.join(data)


def test_write_chunks_truncate(c: Context):
    data = [os.urandom(1024) for _ in range(5)]
    def chunks(data):
        yield from data
    c.fs.path(c.long).write_chunks(chunks(data), truncate=False)
    assert c.read() == b''.join(data) + c.binary[5120:]
    c.fs.path(c.long).write_chunks(chunks(data), truncate=True)
    assert c.read() == b''.join(data)


def test_write_chunks_invalid_arguments(c: Context):
    data = [os.urandom(1024) for _ in range(5)]
    path = c.fs.path(c.file)
    def chunks(data):
        yield from data
    with pytest.raises(ValueError, match=r'cannot write data at offset 1 while also truncating the file'):
        path.write(chunks(data), offset=1, truncate=True)
    with pytest.raises(ValueError, match=r'cannot write data at offset 1 while also appending it'):
        path.write(chunks(data), offset=1, append=True)
    with pytest.raises(ValueError, match=r'cannot append data while also truncating the file'):
        path.write(chunks(data), append=True, truncate=True)


def test_write_text(c: Context):
    c.fs.path(c.long).write_text(c.text)
    assert c.read() == c.text.encode()
    with pytest.raises(IsADirectoryError):
        c.fs.path(c.directory).write_text(c.text)


def test_write_text_append(c: Context):
    c.fs.path(c.long).write_text(c.text, append=True)
    assert c.read().decode('latin1') == c.binary.decode('latin1') + c.text


def test_write_text_encoding(c: Context):
    data = os.urandom(1024)
    c.fs.path(c.long).write_text(data.decode('latin1'), 'latin1')
    assert c.read() == data


def test_write_lines(c: Context):
    texts = ['line1', 'line2', '', 'line3']
    def lines(texts):
        yield from texts
    c.fs.path(c.long).write_lines(lines(texts))
    assert c.read() == '\n'.join(texts).encode() + b'\n'
    c.fs.path(c.long).write_lines(lines([]))
    assert c.read() == b''
    with pytest.raises(IsADirectoryError):
        c.fs.path(c.directory).write_lines(lines(texts))


def test_write_lines_linebreak(c: Context):
    texts = ['line1', 'line2', '', 'line3']
    separator = '...'
    def lines(texts):
        yield from texts
    c.fs.path(c.long).write_lines(lines(texts), linebreak=separator)
    assert c.read() == separator.join(texts).encode() + separator.encode()


def test_write_lines_append(c: Context):
    texts = ['line1', 'line2', '', 'line3']
    def lines(texts):
        yield from texts
    c.fs.path(c.long).write_lines(lines(texts), append=True)
    assert c.read() == c.binary + '\n'.join(texts).encode() + b'\n'


def test_write_lines_encoding(c: Context):
    texts = ['\x80\x81\x82', '\x83\x84\x85']
    def lines(texts):
        yield from texts
    c.fs.path(c.long).write_lines(lines(texts), 'latin1')
    assert c.read() == '\n'.join(texts).encode('latin1') + b'\n'


def test_execute(c: Context):
    path = c.fs.path(c.script)
    execution = path.execute('echo success')
    assert execution.exit_code == 0
    assert execution.stdout == b'success\n'
    assert execution.stderr == b''
    execution = path.execute('echo error >&2; exit 2')
    assert execution.exit_code == 2
    assert execution.stdout == b''
    assert execution.stderr == b'error\n'
    execution = path.execute('cat -', stdin='input')
    assert execution.exit_code == 0
    assert execution.stdout == b'input'
    assert execution.stderr == b''
    started = time.time()
    execution = path.execute('sleep 3', timeout=1)
    elapsed = time.time() - started
    assert execution.exit_code == -15
    assert execution.stdout == b''
    assert execution.stderr == b''
    assert 1 < elapsed < 1.1
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).execute()


def test_delete(c: Context):
    path = c.fs.path(c.file)
    path.delete()
    assert not path.exists()
    path = c.fs.path(c.directory)
    path.delete()
    assert not path.exists()
    path = c.fs.path(c.directory1)
    path.delete()
    assert not path.exists()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).delete()


def test_move(c: Context):
    path1 = c.fs.path(c.file)
    path2 = path1.move(c.no_file)
    assert not path1.exists()
    assert path2.read_text() == c.text
    dir1 = c.fs.path(c.directory)
    dir2 = dir1.move(c.no_directory)
    assert not dir1.exists()
    assert list(dir2.list()) == []
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.file).move(c.directory)


def test_move_into_directory(c: Context):
    path1 = c.fs.path(c.file1)
    with pytest.raises(FileExistsError, match=rf'path {str(c.directory2)!r} already exists'):
        path1.move(c.directory2, into_directory=False, overwrite=False)
    path2 = path1.move(c.directory2, into_directory=True)
    assert not path1.exists()
    assert path2 == c.fs.path(c.directory2) / c.file1_name
    assert path2.read_text() == c.text1
    path3 = path2.move('..', into_directory=True)
    assert not path2.exists()
    assert path3 is path1
    assert path3.read_text() == c.text1
    dir1 = c.fs.path(c.directory)
    dir2 = dir1.move(c.directory1, into_directory=True)
    assert not dir1.exists()
    assert list(dir2.list()) == []
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).move(c.directory1, into_directory=True)
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.file).move(c.no_directory, into_directory=True)


def test_move_overwrite(c: Context):
    path1 = c.fs.path(c.file1)
    with pytest.raises(FileExistsError, match=rf'path {str(c.file2)!r} already exists'):
        path1.move(c.file2, overwrite=False)
    path2 = path1.move(c.file2_name, overwrite=True)
    assert not path1.exists()
    assert path2.read_text() == c.text1
    path3 = path2.move(c.file3, overwrite=True)
    assert not path2.exists()
    assert path3.read_text() == c.text1
    path4 = path3.move(c.no_file, overwrite=True)
    assert not path3.exists()
    assert path4.read_text() == c.text1
    dir1 = c.fs.path(c.directory)
    dir2 = dir1.move(c.no_file, overwrite=True)
    assert not dir1.exists()
    assert list(dir2.list()) == []


def test_move_overwrite_directory(c: Context):
    path1 = c.fs.path(c.file1)
    with pytest.raises(FileExistsError, match=rf'path {str(c.directory2)!r} already exists'):
        path1.move(c.directory2, into_directory=False, overwrite=False)
    path2 = path1.move(c.directory2_name, into_directory=False, overwrite=True)
    assert not path1.exists()
    assert path2.read_text() == c.text1
    dir1 = c.fs.path(c.directory)
    dir2 = dir1.move(c.directory1, into_directory=False, overwrite=True)
    assert not dir1.exists()
    assert list(dir2.list()) == []


def test_copy(c: Context):
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).copy(c.no_directory)
    path1 = c.fs.path(c.file)
    path2 = path1.copy(c.no_file)
    assert path1.read_text() == c.text
    assert path2.read_text() == c.text
    dir1 = c.fs.path(c.directory)
    dir2 = dir1.copy(c.no_directory)
    assert list(dir1.list()) == []
    assert list(dir2.list()) == []


def test_copy_into_directory(c: Context):
    path1 = c.fs.path(c.file1)
    with pytest.raises(FileExistsError, match=rf'path {str(c.directory2)!r} already exists'):
        path1.copy(c.directory2, into_directory=False, overwrite=False)
    path2 = path1.copy(c.directory2, into_directory=True)
    assert path1.read_text() == c.text1
    assert path2 == c.fs.path(c.directory2) / c.file1_name
    assert path2.read_text() == c.text1
    path3 = c.fs.path(c.file3)
    path4 = path3.copy('..', into_directory=True)
    assert path3.read_text() == c.text3
    assert path4 == c.fs.path(c.directory1) / c.file3_name
    assert path4.read_text() == c.text3
    dir1 = c.fs.path(c.directory)
    dir2 = dir1.copy(c.directory1, into_directory=True)
    assert list(dir1.list()) == []
    assert list(dir2.list()) == []
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).move(c.directory1, into_directory=True)
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.file).move(c.no_directory, into_directory=True)


def test_copy_overwrite(c: Context):
    path1 = c.fs.path(c.file1)
    with pytest.raises(FileExistsError, match=rf'path {str(c.file2)!r} already exists'):
        path1.copy(c.file2, overwrite=False)
    path2 = path1.copy(c.file2_name, overwrite=True)
    assert path1.read_text() == c.text1
    assert path2.read_text() == c.text1
    path3 = path2.copy(c.file3, overwrite=True)
    assert path2.read_text() == c.text1
    assert path3.read_text() == c.text1
    path4 = path3.copy(c.no_file, overwrite=True)
    assert path3.read_text() == c.text1
    assert path4.read_text() == c.text1
    dir1 = c.fs.path(c.directory)
    dir2 = dir1.copy(c.no_file, overwrite=True)
    assert list(dir1.list()) == []
    assert list(dir2.list()) == []


def test_copy_overwrite_directory(c: Context):
    path1 = c.fs.path(c.file1)
    with pytest.raises(FileExistsError, match=rf'path {str(c.directory2)!r} already exists'):
        path1.copy(c.directory2, into_directory=False, overwrite=False)
    path2 = path1.copy(c.directory2_name, into_directory=False, overwrite=True)
    assert path1.read_text() == c.text1
    assert path2.read_text() == c.text1
    dir1 = c.fs.path(c.directory)
    dir2 = dir1.copy(c.directory1, into_directory=False, overwrite=True)
    assert list(dir1.list()) == []
    assert list(dir2.list()) == []


def test_archive(c: Context):
    archive = c.fs.path(c.directory2).archive(c.no_file, 'gzip')
    _assert_tar(c, archive.read())
    archive = c.fs.path(c.directory2).archive(c.archive_name)
    assert archive is c.fs.path(c.directory1 / c.archive_name)
    _assert_tar(c, archive.read())
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_directory).archive(c.no_file.with_suffix('.tar.gz'))
    with pytest.raises(NotADirectoryError):
        c.fs.path(c.file).archive(c.no_file.with_suffix('.tar.gz'))


def test_archive_into_directory(c: Context):
    path = c.fs.path(c.directory2)
    with pytest.raises(FileExistsError, match=rf'path {str(c.directory)!r} already exists'):
        path.archive(c.directory, into_directory=False, overwrite=False)
    archive = path.archive(c.directory, 'gzip', into_directory=True)
    assert archive is c.fs.path(c.directory) / (path.name + '.tar.gz')
    _assert_tar(c, archive.read())


def test_archive_overwrite(c: Context):
    path = c.fs.path(c.directory2)
    with pytest.raises(FileExistsError, match=rf'path {str(c.archive)!r} already exists'):
        path.archive(c.archive, overwrite=False)
    archive = path.archive(c.archive, overwrite=True)
    _assert_tar(c, archive.read())
    archive = path.archive(c.directory, 'gzip', overwrite=True)
    _assert_tar(c, archive.read())


def test_archive_zip(c: Context):
    archive = c.fs.path(c.directory2).archive(c.no_file.with_suffix('.zip'))
    _assert_zip(c, archive.read())
    archive.delete()
    archive = c.fs.path(c.directory2).archive(c.no_file, 'zip')
    _assert_zip(c, archive.read())


def test_archive_tar(c: Context):
    archive = c.fs.path(c.directory2).archive(c.no_file.with_suffix('.tar'))
    _assert_tar(c, archive.read())
    archive.delete()
    archive = c.fs.path(c.directory2).archive(c.no_file, 'tar')
    _assert_tar(c, archive.read())


def test_archive_gzip(c: Context):
    archive = c.fs.path(c.directory2).archive(c.no_file.with_suffix('.tar.gz'))
    _assert_tar(c, archive.read())
    archive.delete()
    archive = c.fs.path(c.directory2).archive(c.no_file, 'gzip')
    _assert_tar(c, archive.read())


def test_archive_bzip2(c: Context):
    archive = c.fs.path(c.directory2).archive(c.no_file.with_suffix('.tar.bz'))
    _assert_tar(c, archive.read())
    archive.delete()
    archive = c.fs.path(c.directory2).archive(c.no_file, 'bzip2')
    _assert_tar(c, archive.read())


def test_archive_xz(c: Context):
    archive = c.fs.path(c.directory2).archive(c.no_file.with_suffix('.tar.xz'))
    _assert_tar(c, archive.read())
    archive.delete()
    archive = c.fs.path(c.directory2).archive(c.no_file, 'xz')
    _assert_tar(c, archive.read())


def test_archive_invalid_format(c: Context):
    with pytest.raises(ValueError, match=rf"unfamiliar archive extension '' \(expected one of: .*\)"):
        c.fs.path(c.directory).archive(c.no_file)
    with pytest.raises(ValueError, match=rf"unfamiliar archive extension '.foo' \(expected one of: .*\)"):
        c.fs.path(c.directory).archive(c.no_file.with_suffix('.foo'))
    with pytest.raises(ValueError, match=rf"unfamiliar archive format 'foo' \(expected one of: .*\)"):
        c.fs.path(c.directory).archive(c.no_file, 'foo')


def test_extract(c: Context):
    path = c.fs.path(c.archive).extract(c.no_directory)
    _assert_dir(c, path)
    path.delete()
    with pytest.raises(FileNotFoundError):
        c.fs.path(c.no_file).extract(c.no_directory, 'gzip')
    archive = c.fs.path(c.archive).move(c.no_file)
    path = archive.extract(c.no_directory, 'gzip')
    _assert_dir(c, path)
    path.delete()
    with pytest.raises(Exception):
        c.fs.path(c.file).extract(c.no_directory, 'gzip')


def test_extract_into_directory(c: Context):
    archive = c.fs.path(c.archive)
    with pytest.raises(FileExistsError, match=rf'path {str(c.directory)!r} already exists'):
        archive.extract(c.directory, into_directory=False, overwrite=False)
    path = archive.extract(c.directory, into_directory=True)
    assert path is c.fs.path(c.directory) / c.archive_name.split('.')[0]
    _assert_dir(c, path)


def test_extract_overwrite(c: Context):
    archive = c.fs.path(c.archive)
    with pytest.raises(FileExistsError, match=rf'path {str(c.directory)!r} already exists'):
        archive.extract(c.directory, overwrite=False)
    path = archive.extract(c.directory, overwrite=True)
    _assert_dir(c, path)
    path = archive.extract(c.file, overwrite=True)
    _assert_dir(c, path)


def test_extract_zip(c: Context):
    pass


def test_extract_tar(c: Context):
    pass


def test_extract_gzip(c: Context):
    pass


def test_extract_bzip2(c: Context):
    pass


def test_extract_xz(c: Context):
    pass


def test_extract_invalid_format(c: Context):
    pass


def _assert_tar(c: Context, data: bytes):
    stream = io.BytesIO(data)
    assert [name.strip('./') for name in tarfile.open(fileobj=stream).getnames() if name != '.'] == [
        c.directory3_name,
        f'{c.directory3_name}/{c.file5_name}',
        f'{c.directory3_name}/{c.file6_name}',
        c.file3_name,
        c.file4_name,
    ]


def _assert_zip(c: Context, data: bytes):
    stream = io.BytesIO(data)
    assert zipfile.ZipFile(stream).namelist() == [
        f'{c.directory3_name}/',
        c.file3_name,
        c.file4_name,
        f'{c.directory3_name}/{c.file5_name}',
        f'{c.directory3_name}/{c.file6_name}',
    ]


def _assert_dir(c: Context, root: Path):
    assert list(root.walk(depth_first=False)) == [
        root / c.directory3_name,
        root / c.file3_name,
        root / c.file4_name,
        root / c.directory3_name / c.file5_name,
        root / c.directory3_name / c.file6_name,
    ]