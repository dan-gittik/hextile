from __future__ import annotations
from typing import Callable, ContextManager, Iterable

import base64
import contextlib
import mimetypes
import os
import pathlib
import shlex
import shutil
import tempfile

from .meta import meta_transpiler
from .. import Junk, JunkPlaceholder, TranspilerState, transpile, transpiler


class HTMLState(TranspilerState):

    default_meta_tags = [
        '<meta charset="utf-8" />',
        '<meta name="viewport" content="width=device-width, initial-scale=1" />',
        '<meta name="theme-color" content="{theme_color:?"#000000"}"/>',
        '<meta name="twitter:card" content="summary_large_image" />',
    ]
    meta_tags = {
        'title': [
            '<title>{value}</title>',
            '<meta name="title" content="{value}" />',
            '<meta property="og:title" content="{value}" />',
            '<meta name="twitter:title" content="{value}" />',
        ],
        'description': [
            '<meta name="description" content="{value}" />',
            '<meta property="og:description" content="{value}" />',
            '<meta name="twitter:description" content="{value}" />',
        ],
        'image': [
            '<meta property="og:image" content="{value}" />',
            '<meta name="twitter:image:src" content="{value}" />',
        ],
    }

    def __init__(self, junk: Junk):
        self.static_path = junk.setting('static_path', '/static/')
        self.max_include_size = junk.setting('max_include_size', 1024 * 1024)
        self.max_stylesheet_size = junk.setting('max_stylesheet_size', self.max_include_size)
        self.max_script_size = junk.setting('max_script_size', self.max_include_size)
        self.api = junk.setting('api', False)
        self.development = junk.setting('development', True)
        self.static_directory = junk.setting('static_directory', None)
        self.static_name = junk.setting('static_name', 'asset')
        self.images_directory = junk.setting('image_directory', 'images')
        self.stylesheets_directory = junk.setting('stylesheets_directory', 'css')
        self.scripts_directory = junk.setting('scripts_directory', 'js')
        self.components_directory = junk.setting('components_directory', None)
        self.build_directory = junk.setting('build_directory', None)
        self.open_html: JunkPlaceholder = None
        self.close_head: JunkPlaceholder = None
        self.metadata: dict[str, str] = {}
        self.scripts: set[str] = set()
        self.stylesheets: set[str] = set()
        self.components: set[str] = set()
        junk.on_complete(inject_tags_into_head)

    @classmethod
    def upload(cls, junk: Junk, source: pathlib.Path, target: pathlib.Path) -> str:
        static_directory = junk.setting('static_directory')
        if not static_directory:
            raise RuntimeError('cannot include large static assets without static directory')
        static_directory = pathlib.Path(static_directory).absolute()
        target = static_directory / target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(source, target)
        return os.path.relpath(target, static_directory)


class Tag:

    extensions: dict[str, Callable[[Tag], None]] = {}

    def __init__(
            self,
            junk: Junk,
            tag: str,
            id: str = None,
            classes: list[str] = None,
            attributes: dict[str, str] = None,
            body: str|None = None,
    ):
        self.junk = junk
        self.tag = tag
        self.id = id
        self.classes = classes
        self.attributes = attributes
        self.body = body
    
    @classmethod
    def extend(cls, function: Callable[[Tag], None]) -> Callable[[Tag], None]:
        cls.extensions[function.__name__] = function
        return function
    
    @property
    def is_extended(self) -> bool:
        return self.tag in self.extensions
    
    @property
    def state(self) -> HTMLState:
        return self.junk.state

    @contextlib.contextmanager
    def wrap(
            self,
            tag: str = None,
            id: str = None,
            classes: list[str] = None,
            attributes: dict[str, str] = None,
    ) -> ContextManager[None]:
        if tag is None:
            tag = self.tag
        if id is None:
            id = self.id
        if classes is None:
            classes = self.classes
        if attributes is None:
            attributes = self.attributes
        open_tag = format_tag(tag, id, classes, attributes, has_body=True)
        self.junk.emit_text(open_tag)
        try:
            yield
        finally:
            close_tag = f'</{tag}>'
            self.junk.emit_text(close_tag)

    def add_script(self, url: str) -> None:
        self.state.scripts.add(url)

    def add_stylesheet(self, url: str) -> None:
        self.state.stylesheets.add(url)

    def add_component(self, component: str) -> None:
        self.state.components.add(component)
    
    def run_extension(self) -> None:
        self.extensions[self.tag](self)


@transpiler(name='html', state=HTMLState)
def html_transpiler(junk: Junk) -> None:
    if not junk.line.content:
        return
    tag, id, classes, attributes, body = parse_element(junk.line.content)
    if not tag:
        raise junk.error(f'invalid element (expected [tag][#id][.class]*[attributes*][:])')
    tag = Tag(junk, tag, id, classes, attributes, body)
    if tag.is_extended:
        tag.run_extension()
        return
    has_body = body or junk.line.children
    open_tag = format_tag(tag, id, classes, attributes, has_body)
    junk.emit_text(open_tag)
    indent = junk.line.indent + 4
    if tag == 'html':
        tag.state.open_html = junk.add_placeholder(indent)
    if has_body:
        if body == '':
            junk.line.align_children(to=0)
            text = junk.line.to_string(children_only=True)
            junk.emit_text(text, indent)
        else:
            if body:
                junk.emit_text(body, indent)
            junk.recurse()
        close_tag = f'</{tag}>'
        if tag == 'head':
            tag.state.close_head = junk.add_placeholder(indent)
        junk.emit_text(close_tag)


def inject_tags_into_head(junk: Junk) -> None:
    state: HTMLState = junk.state
    placeholder = state.close_head
    if placeholder:
        add_head = False
    else:
        placeholder = state.open_html
        add_head = True
    if not placeholder:
        return
    tags: list[str] = []
    with junk.capture_emit(tags, placeholder.indent):
        with junk.use_interpolation('{', '}'):
            if add_head:
                junk.emit_text('<head>')
                indent = 4
            else:
                indent = 0
            for tag in state.default_meta_tags:
                junk.emit_text(tag, indent)
            for key, value in state.metadata.items():
                for tag in state.meta_tags.get(key, []):
                    junk.emit_text(tag.format(value=value), indent)
            for url in state.stylesheets:
                inline, asset = get_static(junk, url, state.stylesheets_directory, state.max_stylesheet_size)
                if inline:
                    junk.emit_text('<style>', indent)
                    junk.emit_text(asset, indent + 4, interpolate=False)
                    junk.emit_text('</style>', indent)
                else:
                    junk.emit_text(f'<link href="{asset}" rel="stylesheet" />', indent)
            for url in state.scripts:
                inline, asset = get_static(junk, url, state.scripts_directory, state.max_script_size)
                if inline:
                    junk.emit_text('<script>', indent)
                    junk.emit_text(asset, indent + 4, interpolate=False)
                    junk.emit_text('</script>')
                else:
                    junk.emit_text(f'<script src="{asset}"></script>', indent)
            if state.components:
                inline, bundle = build_react_components(junk, state.components)
                if inline:
                    junk.emit_text('<script>', indent)
                    junk.emit_text(bundle, indent + 4, interpolate=False)
                    junk.emit_text('</script>', indent)
                else:
                    junk.emit_text(f'<script>__webpack_public_path__ = {{static_path:?{state.static_path!r}}}</script>', indent)
                    junk.emit_text(f'<script src="{bundle}">/script>', indent)
            if add_head:
                junk.emit_text('</head>')
    placeholder.inject(tags)


def parse_element(string: str) -> tuple[str, str, str, dict[str, str], None|str]:
    for cursor, character in enumerate(string):
        if character in '#. :':
            tag, string = string[:cursor].lower(), string[cursor+1:]
            break
    else:
        tag, string = string.lower(), ''
    if not tag:
        tag = 'div'
    id = None
    if character == '#':
        for cursor, character in enumerate(string):
            if character in '. :':
                id, string = string[:cursor], string[cursor+1:]
                break
        else:
            id, string = string, ''
    classes = []
    if character == '.':
        for cursor, character in enumerate(string):
            if character in ' :':
                class_list, string = string[:cursor], string[cursor+1:]
                break
        else:
            class_list, string = string, ''
        classes = [class_name for class_name in class_list.split('.') if class_name]
    cursor = 0
    attributes = {}
    if character == ' ':
        while cursor < len(string):
            if string[cursor] == ':':
                break
            if string[cursor] in '"\'':
                quote = string[cursor]
                cursor += 1
                while cursor < len(string):
                    if string[cursor] == quote:
                        break
                    if string[cursor] == '\\':
                        cursor += 2
                    else:
                        cursor += 1
            cursor += 1
        for attribute in shlex.split(string[:cursor]):
            if '=' in attribute:
                name, value = attribute.split('=', 1)
            else:
                name = value = attribute
            attributes[name] = value
    if cursor < len(string):
        body = string[cursor+1:]
    else:
        body = None
    return tag, id, classes, attributes, body


def format_tag(
        tag: str,
        id: str = None,
        classes: list[str] = None,
        attributes: dict[str, str] = None,
        has_body: bool = False,
) -> str:
    open_tag = [f'<{tag}']
    if id:
        open_tag.append(f' id="{id}"')
    if classes:
        open_tag.append(f' class="{" ".join(classes)}"')
    if attributes:
        for name, value in attributes.items():
            open_tag.append(f' {name}="{value}"')
    if has_body:
        open_tag.append('>')
    else:
        open_tag.append(' />')
    return ''.join(open_tag)


def get_static(
        junk: Junk,
        url: str|pathlib.Path,
        name: str = None,
        directory: str = None,
        max_size: int = None,
        encode: str = None,
) -> tuple[bool, str]:
    state: HTMLState = junk.state
    if max_size is None:
        max_size = state.max_include_size
    if isinstance(url, str) and '://' in url:
        return False, url
    source = junk.blueprint.path.parent / url
    if max_size is not False and source.stat().st_size > max_size:
        if name is not None:
            target = name
        else:
            target = source.name
        if directory is not None:
            target = pathlib.Path(directory) / target
        upload_url = state.upload(junk, source, target)
        if '://' in upload_url:
            return False, upload_url
        return False, f'{{static_path:?{state.static_path!r}}}{upload_url}'
    data = source.read_text()
    if encode:
        data = f'data:{encode};base64,{base64.b64encode(data.encode()).decode()}'
    return True, data

    
def build_react_components(junk: Junk, components: Iterable[str]) -> tuple[bool, str]:
    state: HTMLState = junk.state
    if not state.components_directory:
        raise RuntimeError('cannot build react components without components directory')
    components_directory = pathlib.Path(state.components_directory).absolute()
    build_directory = state.build_directory
    if build_directory:
        cleanup = False
    else:
        build_directory = tempfile.mkdtemp()
        cleanup = True
    build_directory = pathlib.Path(build_directory).absolute()
    try:
        output_filename = f'{junk.blueprint.name}.js'
        output_directory = build_directory / 'output'
        transpile(
            '''
                react/ (render='./react')
                    src/ (read=components_directory)
                    $! npm install
                    $! npm run build
            ''',
            'filesystem',
            'shell',
            components_directory = components_directory,
        ).render(
            root = build_directory,
            output_directory = output_directory,
            output_filename = output_filename,
            components = components,
            api = state.api,
            development = state.development,
        )
        inline, bundle = True, ''
        for entry in output_directory.iterdir():
            target = state.components_directory / entry.name
            if entry.name == output_filename:
                inline, bundle = get_static(junk, entry, max_size=0 if state.static_directory else False)
            elif state.static_directory:
                state.upload(junk, entry, target)
        return inline, bundle
    finally:
        if cleanup:
            shutil.rmtree(build_directory)


@Tag.extend
def doctype(tag: Tag) -> None:
    tag.junk.emit_text('<!DOCTYPE html>')


@Tag.extend
def metadata(tag: Tag) -> None:
    tag.junk.line.align_children(to=0)
    for line in tag.junk.line.to_string(children_only=True).splitlines():
        key, value = line.split(':', 1)
        tag.state.metadata[key.strip()] = value.strip()


@Tag.extend
def img(tag: Tag) -> None:
    url = tag.attributes.get('src')
    if url:
        mimetype, encoding = mimetypes.guess_type(url)
        inline, asset = get_static(url, encode=mimetype)
        tag.attributes['src'] = asset
    return format_tag(tag.tag, tag.id, tag.classes, tag.attributes)


@Tag.extend
def style(tag: Tag) -> None:
    with tag.wrap():
        with tag.junk.suspend_transpiler():
            with tag.junk.interpolation_for('css'):
                tag.junk.recurse()


@Tag.extend
def script(tag: Tag) -> None:
    with tag.wrap():
        with tag.junk.suspend_transpiler():
            with tag.junk.interpolation_for('js'):
                tag.junk.recurse()
    

@Tag.extend
def component(tag: Tag) -> None:
    component = tag.attributes['class']
    tag.add_component(component)
    tag.junk.emit_text(f'<div id="{tag.id}"></div>')
    indent = tag.junk.line.indent + 4
    with_props = False
    if tag.junk.line.children:
        with_props = True
        with tag.junk.suspend_transpiler():
            with tag.junk.emit_to_variable('props'):
                tag.junk.line.align_children(to=indent + 4)
                tag.junk.recurse()
    else:
        tag.junk.emit_code("props = 'null'")
    with tag.wrap(tag='script', id=False, attributes=False):
        if with_props:
            tag.junk.emit_text(f'load{component}({tag.id!r},', indent)
            tag.junk.emit_text('{props}')
            tag.junk.emit_text(');', indent)
        else:
            tag.junk.emit_text(f'load{component}({tag.id!r});', indent)


@meta_transpiler.command
def static(
        junk: Junk,
        path: str,
        /,
        name: str = None,
        directory: str = None,
        max_size: int = None,
        encode: str = None,
) -> None:
    state: HTMLState = junk.state
    if name is None:
        name = state.static_name
    inline, asset = get_static(junk, path, directory, max_size, encode)
    if inline:
        junk.emit_code(f'{name} = f{asset!r}')
    else:
        junk.emit_code(f'{name} = {asset!r}')