from __future__ import annotations

import os
import pathlib
import shutil
import tempfile

import pytest
try:
    import paramiko
except ImportError:
    pass

from hextile.filesystem import FileSystem


class FixtureRequest:
    param: str


class Context:
    '''
    root/
        # no-file
        # no-directory
        file.txt: Hello, world!
        directory/
        directory1/
            directory2/
                directory3/
                    file5.txt: text 5
                    file6.txt: text 6
                file3.txt: text 3
                file4.txt: text 4
            file1.txt: text 1
            file2.txt: text 2
        archive.tar.gz # directory1
        permissions/
            none # unreadable, unwritable and unexecutable
            owner-readable # owner readable
            owner-writable # owner writable
            owner-executable # owner executable
            owner-all # owner readable, writable and executable
            group-readable # group readable
            group-writable # group writable
            group-executable # group executable
            group-all # group readable, writable and executable
            other-readable # other readable
            other-writable # other writable
            other-executable # other executable
            other-all # other readable, writable and executable
            script: #!/bin/bash\necho 1 # readable and executable
    '''

    no_file_name = 'no-file'
    no_directory_name = 'no-directory'
    file_name = 'file.txt'
    long_name = 'long.txt'
    directory_name = 'directory'
    directory1_name = 'directory1'
    directory2_name = 'directory2'
    directory3_name = 'directory3'
    file1_name = 'file1.txt'
    file2_name = 'file2.txt'
    file3_name = 'file3.txt'
    file4_name = 'file4.txt'
    file5_name = 'file5.txt'
    file6_name = 'file6.txt'
    archive_name = 'archive.tar.gz'
    permissions_directory_name = 'permissions'
    none_name = 'none'
    owner_readlabe_name = 'owner-readable'
    owner_writable_name = 'owner-writable'
    owner_executable_name = 'owner-executable'
    owner_all_name = 'owner-all'
    group_readlabe_name = 'group-readable'
    group_writable_name = 'group-writable'
    group_executable_name = 'group-executable'
    group_all_name = 'group-all'
    other_readlabe_name = 'other-readable'
    other_writable_name = 'other-writable'
    other_executable_name = 'other-executable'
    other_all_name = 'other_all'
    script_name = 'script'

    text = 'Hello, world!'
    text1 = 'text 1'
    text2 = 'text 2'
    text3 = 'text 3'
    text4 = 'text 4'
    text5 = 'text 5'
    text6 = 'text 6'
    binary = os.urandom(1024 * 1024)
    script_code = f'''
#!/bin/sh
if [ -n "$1" ]
then
    eval "$1"
fi
'''.strip()

    def __init__(self, filesystem: FileSystem):
        self.fs = filesystem
        self.root = {
            'local': self.setup_local,
            'ssh': self.setup_ssh,
        }[self.fs.url.scheme]()
        self.no_file = self.root / self.no_file_name
        self.no_directory = self.root / self.no_directory_name
        self.file = self.root / self.file_name
        self.long = self.root / self.long_name
        self.directory = self.root / self.directory_name
        self.directory1 = self.root / self.directory1_name
        self.file1 = self.directory1 / self.file1_name
        self.file2 = self.directory1 / self.file2_name
        self.directory2 = self.directory1 / self.directory2_name
        self.file3 = self.directory2 / self.file3_name
        self.file4 = self.directory2 / self.file4_name
        self.directory3 = self.directory2 / self.directory3_name
        self.file5 = self.directory3 / self.file5_name
        self.file6 = self.directory3 / self.file6_name
        self.archive = self.root / self.archive_name
        self.permissions_directory = self.root / self.permissions_directory_name
        self.none = self.permissions_directory / self.none_name
        self.owner_readable = self.permissions_directory / self.owner_readlabe_name
        self.owner_writable = self.permissions_directory / self.owner_writable_name
        self.owner_executable = self.permissions_directory / self.owner_executable_name
        self.owner_all = self.permissions_directory / self.owner_all_name
        self.group_readable = self.permissions_directory / self.group_readlabe_name
        self.group_writable = self.permissions_directory / self.group_writable_name
        self.group_executable = self.permissions_directory / self.group_executable_name
        self.group_all = self.permissions_directory / self.group_all_name
        self.other_readable = self.permissions_directory / self.other_readlabe_name
        self.other_writable = self.permissions_directory / self.other_writable_name
        self.other_executable = self.permissions_directory / self.other_executable_name
        self.other_all = self.permissions_directory / self.other_all_name
        self.script = self.permissions_directory / self.script_name
    
    def setup_local(self) -> pathlib.Path:
        root = pathlib.Path(tempfile.mkdtemp())
        file = root / self.file_name
        file.write_text(self.text)
        long = root / self.long_name
        long.write_bytes(self.binary)
        directory = root / self.directory_name
        directory.mkdir()
        directory1 = root / self.directory1_name
        directory1.mkdir()
        file1 = directory1 / self.file1_name
        file1.write_text(self.text1)
        file2 = directory1 / self.file2_name
        file2.write_text(self.text2)
        directory2 = directory1 / self.directory2_name
        directory2.mkdir()
        file3 = directory2 / self.file3_name
        file3.write_text(self.text3)
        file4 = directory2 / self.file4_name
        file4.write_text(self.text4)
        directory3 = directory2 / self.directory3_name
        directory3.mkdir()
        file5 = directory3 / self.file5_name
        file5.write_text(self.text5)
        file6 = directory3 / self.file6_name
        file6.write_text(self.text6)
        archive = root / self.archive_name
        shutil.make_archive(root / self.archive_name.split('.', 1)[0], 'gztar', directory2)
        permissions_directory = root / self.permissions_directory_name
        permissions_directory.mkdir()
        none = permissions_directory / self.none_name
        none.touch(0o000)
        owner_readable = permissions_directory / self.owner_readlabe_name
        owner_readable.touch()
        owner_readable.chmod(0o400)
        owner_writable = permissions_directory / self.owner_writable_name
        owner_writable.touch()
        owner_writable.chmod(0o200)
        owner_executable = permissions_directory / self.owner_executable_name
        owner_executable.touch()
        owner_executable.chmod(0o100)
        owner_all = permissions_directory / self.owner_all_name
        owner_all.touch()
        owner_all.chmod(0o700)
        group_readable = permissions_directory / self.group_readlabe_name
        group_readable.touch()
        group_readable.chmod(0o040)
        group_writable = permissions_directory / self.group_writable_name
        group_writable.touch()
        group_writable.chmod(0o020)
        group_executable = permissions_directory / self.group_executable_name
        group_executable.touch()
        group_executable.chmod(0o010)
        group_all = permissions_directory / self.group_all_name
        group_all.touch()
        group_all.chmod(0o070)
        other_readable = permissions_directory / self.other_readlabe_name
        other_readable.touch()
        other_readable.chmod(0o004)
        other_writable = permissions_directory / self.other_writable_name
        other_writable.touch()
        other_writable.chmod(0o002)
        other_executable = permissions_directory / self.other_executable_name
        other_executable.touch()
        other_executable.chmod(0o001)
        other_all = permissions_directory / self.other_all_name
        other_all.touch()
        other_all.chmod(0o007)
        script = permissions_directory / self.script_name
        script.touch()
        script.chmod(0o777)
        script.write_text(self.script_code)
        return root
    
    def setup_ssh(self) -> pathlib.Path:
        raise NotImplementedError()

    def teardown(self) -> None:
        {
            'local': self.teardown_local,
            'ssh': self.teardown_ssh,
        }[self.fs.url.scheme]()
    
    def teardown_local(self) -> None:
        shutil.rmtree(self.root)
    
    def teardown_ssh(self) -> None:
        raise NotImplementedError()
    
    def read(self) -> bytes:
        return {
            'local': self.read_local,
            'ssh': self.read_ssh,
        }[self.fs.url.scheme]()
    
    def read_local(self) -> bytes:
        return self.long.read_bytes()
    
    def read_ssh(self) -> bytes:
        raise NotImplementedError()
    
    def write(self, data: str|bytes) -> None:
        if isinstance(data, str):
            data = data.encode()
        {
            'local': self.write_local,
            'ssh': self.write_ssh,
        }[self.fs.url.scheme](data)
    
    def write_local(self, data: bytes) -> None:
        self.file.write_bytes(data)
    
    def write_ssh(self, data: bytes) -> None:
        raise NotImplementedError()


@pytest.fixture(params=[
    'local://',
])
def c(request: FixtureRequest):
    filesystem = FileSystem(request.param)
    context = Context(filesystem)
    try:
        yield context
    finally:
        context.teardown()