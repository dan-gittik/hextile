from __future__ import annotations
from typing import Any, Callable

import importlib
import pathlib


class Transpiler:

    all_transpilers: dict[str, Transpiler] = {}
    core_transpilers: list[Transpiler] = []

    def __init__(
            self,
            transpile: Callable[[Junk], None] = None,
            match: Callable[[Junk], bool] = None,
            name: str = None,
            prefix: str = None,
            escape_prefix: str = None,
            core: bool = False,
            priority: int = None,
            state: type[TranspilerState] = None,
    ):
        if prefix is None:
            prefix = ''
        if escape_prefix is None:
            escape_prefix = 2 * prefix
        if priority is None:
            if core:
                priority = 0
            elif prefix:
                priority = 1
            else:
                priority = 2
        if state is None:
            state = TranspilerState
        if name is not None:
            if name in self.all_transpilers:
                raise ValueError(f'transpiler {name!r} already exists')
            self.all_transpilers[name] = self
        self.transpile = transpile
        self.name = name
        self.core = core
        self.priority = priority
        self.prefix = prefix
        self.escape_prefix = escape_prefix
        self.state = state
        self.commands: dict[str, Callable[..., None]] = {}
        self.extensions: list[Callable[[Junk, Splinter], None]] = []
        self._match = match
        if self.core:
            self.core_transpilers.append(self)
    
    def __str__(self) -> str:
        return f'{"core " if self.core else ""}transpiler {self.name!r}'
    
    def __repr__(self) -> str:
        return f'<{self}>'
    
    @classmethod
    def resolve(self, *configs: str|Transpiler, core: bool = True) -> list[Transpiler]:
        seen: set[str] = set()
        transpilers: list[Transpiler] = []
        for config in configs:
            if isinstance(config, Transpiler):
                transpiler = config
                transpilers.append(transpiler)
                continue
            if '.' in config:
                module_name, name = config.rsplit('.', 1)
                module = importlib.import_module(module_name)
                transpiler = getattr(module, name)
            else:
                transpiler = Transpiler.all_transpilers.get(config)
                if not transpiler:
                    raise ValueError(f'transpiler {config!r} does not exist (expected one of: {", ".join(Transpiler.all_transpilers)})')
            transpilers.append(transpiler)
            seen.add(transpiler.name)
        if core:
            for transpiler in Transpiler.core_transpilers:
                if transpiler.name in seen:
                    continue
                transpilers.append(transpiler)
        transpilers.sort(key=lambda transpiler: transpiler.priority)
        return transpilers
    
    def match(self, match: Callable[[Junk], bool]) -> Callable[[Junk], bool]:
        self._match = match
        return match
    
    def extend_interpolation(self, extension: Callable[[Junk, Splinter], None]) -> Callable[[Junk, Splinter], None]:
        self.extensions.append(extension)
        return extension
    
    def command(self, command: Callable[..., None]) -> Callable[..., None]:
        self.commands[command.__name__] = command
        return command
    
    def matches(self, junk: Junk) -> bool:
        if self._match:
            return self._match(junk)
        if self.escape_prefix and junk.line.content.startswith(self.escape_prefix):
            junk.line.content = self.prefix + junk.line.content[len(self.escape_prefix):]
            return False
        if not junk.line.content.startswith(self.prefix):
            return False
        junk.line.content = junk.line.content[len(self.prefix):].lstrip()
        return True


class TranspilerState:

    def __init__(self, junk: Junk):
        self.commands = {name: command.__get__(junk) for name, command in junk.transpiler.commands.items()}


def transpiler(
        transpile: Callable[[Junk, Line], None] = None,
        /,
        *,
        name: str = None,
        prefix: str = None,
        escape_prefix: str = None,
        core: bool = False,
        priority: int = None,
        state: type[TranspilerState] = None,
) -> Transpiler:
    if transpile is None:
        return lambda transpile: transpiler(transpile,
            name = name,
            prefix = prefix,
            escape_prefix = escape_prefix,
            priority = priority,
            core = core,
            state = state,
        )
    if name is None:
        name = transpile.__name__
    return Transpiler(
        transpile = transpile,
        name = name,
        prefix = prefix,
        escape_prefix = escape_prefix,
        core = core,
        priority = priority,
        state = state,
    )


def transpile(
        blueprint: str|pathlib.Path|Blueprint,
        *transpilers: str|Transpiler,
        core: bool = True,
        **settings: Any,
) -> Junk:
    """
    Resolves a blueprint and transpilers into a transpiled junk object.

        >>> junk = transpile('''
        ... !for i in range(n):
        ...     line {i}
        ... ''')
        >>> print(junk.render(n=3))
        line 0
        line 1
        line 2

        # Don't add core transpilers (i.e. use specified transpilers only):
        >>> junk = transpile('''
        ... !for i in range(n):
        ...     line {i}
        ... ''', text_transpiler, core=False)
        >>> print(junk.render(i=0))
        !for i in range(n):
            line 0
        
        # Add blueprint settings (e.g. for meta transpilation):
        >>> junk = transpile('''
        ... % include(path)
        ... ''', path='/path/to/blueprint')

    Arguments:
        blueprint: The blueprint path (as a one-line string or a path object),
            the blueprint text (as a multi-line string), or a blueprint object.
        *transpilers: The transpiler import paths (as dot-delimited strings),
            names (as dotless strings), or transpiler objects.
        core: If true, core transpilers are added as well (this is the default);
            otherwise, only the specified transpilers are used.
        **settings: The blueprint settings.
    
    Returns:
        The corresponding junk object.
    """
    blueprint = Blueprint.resolve(blueprint, **settings)
    transpilers = Transpiler.resolve(*transpilers, core=core)
    junk = Junk(blueprint, transpilers)
    junk.transpile()
    return junk


from .blueprint import Blueprint, Line
from .junk import Junk
from .splinterpolate import Splinter