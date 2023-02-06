from __future__ import annotations
from typing import Any

import pathlib

from .text import text_transpiler
from .. import Blueprint, Junk, Line, Transpiler, TranspilerState, transpiler


class MetaState(TranspilerState):

    def __init__(self, junk: Junk):
        super().__init__(junk)
        self.sections: dict[str, list[Line]] = {}


@transpiler(name='meta', prefix='%', core=True, state=MetaState)
def meta_transpiler(junk: Junk) -> None:
    if not junk.line.content:
        if junk.line.children:
            raise junk.error('empty meta line cannot have nested lines')
        else:
            junk.emit_empty_line()
    elif junk.line.content == ':':
        if junk.line.children:
            junk.line.align_children(to=0)
            string = junk.line.to_string(children_only=True)
            junk.emit_text(string, interpolate=False)
        else:
            junk.set_active_transpilers([text_transpiler])
            junk.set_interpolation(None)
    elif junk.line.content == '!':
        junk.line.align_children(to=0)
        text = junk.line.to_string(children_only=True)
        name = f'{junk.line.name}:{junk.line.number}'
        code = compile(text, name, 'exec')
        exec(code, junk.blueprint.settings)
    else:
        junk.run_transpiler_command()


@meta_transpiler.command
def include(junk: Junk, /, blueprint: str|pathlib.Path, **settings: Any) -> None:
    if junk.line.children:
        raise junk.error('include command cannot have nested lines')
    included = Blueprint.resolve(blueprint, relative_to=junk.blueprint.path.parent, **settings)
    for line in included.lines:
        line.shift(junk.line.indent)
    junk.recurse(included.lines)


@meta_transpiler.command
def define(junk: Junk, /, section: str) -> None:
    state: MetaState = junk.state
    junk.line.align_children(to=0)
    state.sections[section] = junk.line.children


@meta_transpiler.command
def insert(junk: Junk, /, section: str, *, required: bool = False) -> None:
    state: MetaState = junk.state
    lines = state.sections.get(section)
    if lines:
        for line in lines:
            line.shift(junk.line.indent)
        junk.recurse(lines)
    elif required:
        raise junk.error(f'required section {section!r} is missing')
    else:
        junk.line.align_children()
        junk.recurse()


@meta_transpiler.command
def extend(junk: Junk, /, blueprint: str|pathlib.Path, **settings: Any) -> None:
    if junk.line.children:
        raise junk.error('extend command cannot have nested lines')
    extended = Blueprint.resolve(blueprint, relative_to=junk.blueprint.path.parent, **settings)
    junk.on_complete(lambda junk: junk.transpile(extended))


@meta_transpiler.command
def transpilers(junk: Junk, /, *transpilers: str, core: bool = True) -> None:
    transpilers = Transpiler.resolve(*transpilers, core=core)
    active_transpilers = junk.active_transpilers.copy()
    junk.set_active_transpilers(transpilers)
    if junk.line.children:
        junk.line.align_children()
        try:
            junk.recurse()
        finally:
            junk.set_active_transpilers(active_transpilers)


@meta_transpiler.command
def interpolate(junk: Junk, /, start_token: str = None, end_token: str = None) -> None:
    if junk.line.children:
        junk.line.align_children()
        with junk.use_interpolation(start_token, end_token):
            junk.recurse()
    else:
        junk.set_interpolation(start_token, end_token)


@meta_transpiler.command
def stop(junk: Junk, /) -> None:
    junk.emit_code(f'raise {junk.StopTranspilation.__name__}()')