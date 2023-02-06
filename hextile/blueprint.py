from __future__ import annotations
from types import FrameType
from typing import Any, Callable

import inspect
import pathlib
import re


open_suffix = '\\'
line_regex = re.compile(r'^(\s*)(.*)$')


class Blueprint:

    def __init__(self, name: str, path: pathlib.Path, text: str, settings: dict[str, Any]):
        self.name = name
        self.path = path
        self.text = text
        self.settings = settings
        self.lines = parse_lines(self.text, name=self.name)
    
    def __str__(self) -> str:
        return f'blueprint {self.name!r}'
    
    def __repr__(self) -> str:
        return f'<{self}>'

    @classmethod
    def resolve(
            cls,
            config: str|pathlib.Path|Blueprint,
            relative_to: pathlib.Path = None,
            /,
            **settings: Any,
    ) -> Blueprint:
        if isinstance(config, Blueprint):
            blueprint = config
            blueprint.settings.update(settings)
            return blueprint
        if isinstance(config, str) and '\n' in config:
            frame = get_caller_frame(__package__)
            path = pathlib.Path(frame.f_code.co_filename)
            name = f'{path.stem}:{frame.f_lineno}'
            text = '\n'.join(trim(config))
            return Blueprint(name, path, text, settings)
        if relative_to is not None:
            path = pathlib.Path(relative_to).absolute() / config
        else:
            path = pathlib.Path(config).absolute()
        name = path.stem
        text = path.read_text()
        return Blueprint(name, path, text, settings)


class Line:

    def __init__(self, name: str, number: int, indent: int, content: str):
        self.name = name
        self.number = number
        self.indent = indent
        self.content = content
        self.children: list[Line] = []

    def __str__(self) -> str:
        return f'{self.name}:{self.number}'
    
    def __repr__(self) -> str:
        return f'<{self}>'

    def recurse(self, callback: Callable[[Line], None]) -> None:
        for child in self.children:
            callback(child)
            child.recurse(callback)
    
    def to_string(self, children_only: bool = False) -> str:
        body = []
        if not children_only:
            body.append(' ' * self.indent + self.content)
        self.recurse(lambda line: body.append(' ' * line.indent + line.content))
        return '\n'.join(body)
    
    def shift(self, delta: int) -> None:
        self.indent = max(self.indent + delta, 0)
        for child in self.children:
            child.shift(delta)
    
    def align_children(self, to: int = None) -> None:
        if to is None:
            to = self.indent
        for child in self.children:
            child.shift(to - child.indent)


def parse_lines(text: str, name: str = None) -> list[Line]:
    lines: list[Line] = []
    stack: list[Line] = []
    open_line: Line = None
    for number, line in enumerate(text.splitlines(), 1):
        indent, content = parse_line(line)
        line = Line(name, number, indent, content)
        if open_line:
            line.content = open_line.content[:-len(open_suffix)] + content
            if line.content.endswith(open_suffix):
                open_line = line
            else:
                open_line = None
            continue
        while stack and stack[-1].indent >= indent:
            stack.pop()
        if stack:
            stack[-1].children.append(line)
        else:
            lines.append(line)
        stack.append(line)
        if line.content.endswith(open_suffix):
            open_line = line
    return lines


def parse_line(line: str) -> tuple[int, str]:
    whitespace, content = line_regex.match(line).groups()
    return len(whitespace), content.strip()


def trim(string: str) -> list[str]:
    lines = []
    first_indent = None
    for line in string.rstrip().splitlines():
        indent, content = parse_line(line)
        if not content:
            continue
        if first_indent is None:
            first_indent = indent
            lines.append(content)
        else:
            indent_diff = max(indent - first_indent, 0)
            lines.append(indent_diff * ' ' + content)
    return lines


def get_caller_frame(package: str) -> FrameType:
    frame = inspect.currentframe()
    while frame and frame.f_globals.get('__package__') == package:
        frame = frame.f_back
    return frame