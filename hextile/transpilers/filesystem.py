import os
import pathlib

from .. import Blueprint, Junk, Line, TranspilerState, transpiler


class FilesystemState(TranspilerState):

    def __init__(self, junk: Junk):
        self.directory_suffix = junk.setting('directory_suffix', '/')
        self.root_name = junk.setting('root_name', 'root')
        self.directory_name = junk.setting('directory_name', 'directory')
        self.file_name = junk.setting('file_name', 'file')
        self.template_name = junk.setting('template_name', 'template')
        self.raw = junk.setting('raw', False)
        root = junk.setting('root', '.')
        junk.add_imports('os', 'pathlib')
        junk.add_definition(f'''
            try:
                {self.root_name}
            except NameError:
                {self.root_name} = {root!r}
            {self.root_name} = pathlib.Path({self.root_name}).absolute()
            {self.root_name}.mkdir(parents=True, exist_ok=True)
            os.chdir({self.root_name})
        ''')


@transpiler(name='fs', priority=2, state=FilesystemState)
def filesystem_transpiler(junk: Junk) -> None:
    state: FilesystemState = junk.state
    if '(' in junk.line.content:
        path, args = junk.line.content[:-1].split('(', 1)
    else:
        path, args = junk.line.content, None
    path = path.strip()
    is_directory = path.endswith(state.directory_suffix)
    if is_directory:
        generate = generate_directory
    else:
        generate = generate_file
    junk.evaluate(f'generate(junk, {path!r}, {args})', generate=generate, junk=junk)


def generate_directory(
        junk: Junk,
        path: str,
        copy: pathlib.Path = None,
        read: pathlib.Path = None,
        render: pathlib.Path = None,
) -> None:
    state: FilesystemState = junk.state
    path = junk.interpolate(path, as_string=True)
    junk.emit_code(f'{state.directory_name} = pathlib.Path({path})')
    if copy:
        copy = junk.blueprint.path.parent / copy
        junk.add_imports('shutil')
        junk.emit_code(f'shutil.copytree({str(copy)!r}, {state.directory_name})')
    else:
        junk.emit_code(f'{state.directory_name}.mkdir(parents=True, exist_ok=True)')
    junk.emit_code(f'os.chdir({state.directory_name})')
    if read or render:
        directory = junk.blueprint.path.parent / (read or render)
        for entry in directory.iterdir():
            transpile_from(junk, entry, raw=bool(read))
    if junk.line.children:
        junk.recurse()
    junk.emit_code(f"os.chdir('..')")


def generate_file(
        junk: Junk,
        path: str,
        copy: pathlib.Path = None,
        read: pathlib.Path = None,
        render: pathlib.Path = None,
) -> None:
    state: FilesystemState = junk.state
    path = junk.interpolate(path)
    junk.emit_code(f'{state.file_name} = pathlib.Path({path})')
    if copy:
        copy = junk.blueprint.path.parent / copy
        junk.add_imports('shutil')
        junk.emit_code(f'shutil.copy({str(copy)!r}, {state.file_name})')
    elif read or render:
        file = junk.blueprint.path.parent / (read or render)
        transpile_from_file(junk, file, raw=bool(read))
    elif junk.line.children:
        language = os.path.splitext(path)[1][1:]
        junk.line.align_children(to=0)
        transpile_from_lines(junk, junk.line.children, language)
    else:
        junk.emit_code(f'{state.file_name}.touch()')


def transpile_from(junk: Junk, path: pathlib.Path, raw: bool = None) -> None:
    state: FilesystemState = junk.state
    if path.is_dir():
        junk.emit_code(f'{state.directory_name} = pathlib.Path({path.name!r})')
        junk.emit_code(f'{state.directory_name}.mkdir(exist_ok=True)')
        junk.emit_code(f'os.chdir({state.directory_name})')
        for entry in path.iterdir():
            transpile_from(junk, entry, raw=raw)
        junk.emit_code(f"os.chdir('..')")
    else:
        transpile_from_file(junk, path, raw=raw)


def transpile_from_file(junk: Junk, path: pathlib.Path, raw: bool = None) -> None:
    state: FilesystemState = junk.state
    junk.emit_code(f'{state.file_name} = pathlib.Path({path.name!r})')
    if raw is None:
        raw = state.raw
    if raw:
        junk.emit_code(f'{state.file_name}.write_bytes({path.read_bytes()!r})')
    else:
        blueprint = Blueprint.resolve(path)
        transpile_from_lines(junk, blueprint.lines, language=path.suffix[1:])


def transpile_from_lines(junk: Junk, lines: list[Line], language: str) -> None:
    state: FilesystemState = junk.state
    with junk.interpolation_for(language):
        with junk.suspend_transpiler():
            with junk.emit_to_variable(state.template_name):
                junk.recurse(lines)
        junk.emit_code(f'{state.file_name}.write_text({state.template_name})')