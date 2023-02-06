from __future__ import annotations
from typing import Any, Callable, ContextManager, TypeVar

import contextlib


T = TypeVar('T')


class Junk:

    class TranspilationError(Exception):
        pass

    class StopTranspilation(Exception):
        pass

    EMIT = '__emit__'
    CALL = '__call__'
    CAPTURE = '__capture__'

    default_interpolation = '{', '}'
    interpolations: dict[str, tuple[str, str]] = dict(
        css = ('<', '>'),
        js = ('(|', '|)'),
        json = ('<', '>'),
    )

    def __init__(self, blueprint: Blueprint, transpilers: list[Transpiler]):
        self.blueprint = blueprint
        self.transpilers = transpilers
        self.active_transpilers: list[Transpiler] = []
        self.builtins = {
            self.EMIT: self._render_emit,
            self.CALL: self._render_call,
            self.CAPTURE: self._render_capture,
            self.StopTranspilation.__name__: self.StopTranspilation,
        }
        self._lines: list[Line] = []
        self._transpilers: list[Transpiler] = []
        self._states: dict[Transpiler, TranspilerState] = {}
        self._interpolations: list[tuple[str, str]] = [self.default_interpolation]
        self._imports: set[str] = set()
        self._definitions: set[str] = set()
        self._code_indent = 0
        self._text_indent: int = None
        self._code_output: list[str] = []
        self._on_complete: dict[Transpiler, Callable[[Junk], None]] = {}
        self._render_indent = 0
        self._render_output: list[str] = []
    
    def __str__(self) -> str:
        return f'junk of {self.blueprint} with transpilers {", ".join(transpiler.name for transpiler in self.transpilers)}'

    def __repr__(self) -> str:
        return f'<{self}>'
    
    @property
    def line(self) -> None|Line:
        if not self._lines:
            return None
        return self._lines[-1]
    
    @property
    def transpiler(self) -> None|Transpiler:
        if not self._transpilers:
            return None
        return self._transpilers[-1]
    
    @property
    def interpolation(self) -> tuple[str, str]:
        return self._interpolations[-1]
    
    @property
    def state(self) -> TranspilerState:
        self._assert_transpiler()
        return self._states[self.transpiler]
    
    def to_string(self) -> str:
        output: list[str] = []
        for name in sorted(self._imports):
            output.append(f'import {name}')
        output.extend(self._definitions)
        for line in self._code_output:
            if isinstance(line, JunkPlaceholder):
                continue
            output.append(line)
        return '\n'.join(output)
    
    def transpile(
            self,
            blueprint: Blueprint = None,
            transpilers: list[Transpiler] = None,
    ) -> None:
        if not blueprint:
            blueprint = self.blueprint
        if not transpilers and not self.active_transpilers:
            transpilers = self.transpilers
        self._code_output.clear()
        self._interpolations = [self.default_interpolation]
        if transpilers:
            self.set_active_transpilers(transpilers)
        with contextlib.suppress(self.StopTranspilation):
            self._run_transpilers(blueprint.lines)
        on_complete = self._on_complete.copy()
        self._on_complete.clear()
        for transpiler, callback in reversed(on_complete.items()):
            with self._set_transpiler(transpiler):
                callback(self)
        if transpilers:
            self.active_transpilers.clear()
    
    def render(self, context: dict[str, Any] = None, /, **more_context: Any) -> str:
        if context is None:
            context = {}
            context.update(more_context)
        context.update(self.builtins)
        text = self.to_string()
        code = compile(text, self.blueprint.name, 'exec')
        self._render_output.clear()
        exec(code, context)
        return '\n'.join(self._render_output)

    def error(self, message: str) -> TranspilationError:
        if not self.line:
            message = f'{self} failed: {message}'
        else:
            message = f'cannot transpile {self.line}: {message} | {self.line.content}'
        return self.TranspilationError(message)
    
    def setting(self, setting: str, default: T = None) -> T:
        self._assert_transpiler()
        return self.blueprint.settings.get(self.transpiler.name, {}).get(setting, default)
    
    def set_active_transpilers(self, transpilers: list[Transpiler]) -> None:
        for transpiler in transpilers:
            if transpiler not in self._states:
                with self._set_transpiler(transpiler):
                    self._states[transpiler] = transpiler.state(self)
        self.active_transpilers = transpilers
    
    @contextlib.contextmanager
    def suspend_transpiler(self) -> ContextManager[None]:
        self._assert_transpiler()
        transpiler = self.transpiler
        transpilers = self.active_transpilers.copy()
        if transpiler not in transpilers:
            yield
            return
        self.set_active_transpilers([transpiler for transpiler in transpilers if transpiler is not self.current_transpiler])
        try:
            yield
        finally:
            self.set_active_transpilers(transpilers)
       
    def set_interpolation(self, start_token: str, end_token: str = None) -> None:
        if end_token is None:
            start_token = end_token
        self._interpolations[-1] = start_token, end_token
    
    @contextlib.contextmanager
    def use_interpolation(self, start_token: str, end_token: str = None) -> ContextManager[None]:
        if end_token is None:
            start_token = end_token
        self._interpolations.append((start_token, end_token))
        try:
            yield
        finally:
            self._interpolations.pop()
    
    @contextlib.contextmanager
    def interpolation_for(self, language: str) -> ContextManager[None]:
        interpolation = self.interpolations.get(language, self.default_interpolation)
        with self.use_interpolation(*interpolation):
            yield

    def interpolate(self, text: str, as_string: bool = False) -> str:
        words: list[str] = []
        has_code = False
        for splinter in splinterpolate(*self.interpolation, text):
            if not splinter.is_code:
                words.append(repr(splinter.text))
                continue
            has_code = True
            splinter.compile()
            for transpiler in self.active_transpilers:
                if transpiler.extensions:
                    with self._set_transpiler(transpiler):
                        for extension in transpiler.extensions:
                            extension(self, splinter)
            code = splinter.text
            if splinter.format:
                code = f'({code}).__format__({splinter.format!r})'
            if splinter.conversion:
                code = f'{splinter.conversion.__name__}({code})'
            words.append(code)
        if as_string:
            if not words:
                return repr('')
            if len(words) == 1:
                return f'str({words[0]})' if has_code else words[0]
            return f"''.join(map(str, ({', '.join(words)})))"
        if not words:
            return ''
        return ', '.join(words)

    def evaluate(self, code: str, **context: Any) -> None:
        try:
            eval(code, {
                **self.blueprint.settings,
                **self.state.__dict__,
                **context,
            })
        except Exception as error:
            raise self.error(str(error))
    
    def add_imports(self, *modules: str) -> None:
        self._imports.update(modules)

    def add_definition(self, definition: str) -> None:
        self._definitions.add('\n'.join(trim(definition)) + '\n\n')
    
    def add_placeholder(self, indent: int = None) -> JunkPlaceholder:
        placeholder = JunkPlaceholder(self, indent)
        self._code_output.append(placeholder)
        return placeholder
 
    def on_complete(self, callback: Callable[[Junk], None]) -> Callable[[Junk], None]:
        self._assert_transpiler()
        self._on_complete[self.transpiler] = callback
        return callback   

    def run_transpiler_command(self) -> None:
        self.evaluate(self.line.content, **self.state.commands)

    def recurse(self, lines: list[Line] = None, indent: int = 0) -> None:
        if lines is None:
            self._assert_line()
            lines = self.line.children
        self._code_indent += indent
        try:
            self._run_transpilers(lines)
        finally:
            self._code_indent -= indent

    def emit_code(self, code: str) -> None:
        whitespace = ' ' * 4 * self._code_indent
        for line in trim(code):
            self._code_output.append(whitespace + line)
    
    @contextlib.contextmanager
    def try_emit_code(self) -> ContextManager[None]:
        self.emit_code('try:')
        last_emit = self._code_output[-1]
        self._code_indent += 1
        try:
            yield
        finally:
            self._code_indent -= 1
            if self._code_output[-1] == last_emit:
                self._code_output.pop()
            else:
                self.emit_code('''
                    except:
                        pass
                ''')

    def emit_text(self, text: str, indent: int = None, *, interpolate: bool = True) -> None:
        if indent is None:
            indent = self.line.indent if self.line else 0
        if self._text_indent:
            indent += self._text_indent
        for line in trim(text):
            if not line:
                continue
            if interpolate:
                words = self.interpolate(line)
            else:
                words = repr(line)
            self.emit_code(f'{self.EMIT}({indent:<3}, {" " * (indent - 4 * self._code_indent)}{words})')
   
    def emit_empty_line(self) -> None:
        self.emit_code(f'{self.EMIT}(0, "")')

    @contextlib.contextmanager
    def capture_emit(self, into: list[str], indent: int = None) -> ContextManager[None]:
        emit_output, text_indent = self._code_output, self._text_indent
        self._code_output, self._text_indent = into, indent
        try:
            yield
        finally:
            self._code_output,self._text_indent = emit_output, text_indent
 
    @contextlib.contextmanager
    def emit_to_variable(self, name: str) -> ContextManager[None]:
        self.emit_code(f'with {self.CAPTURE}() as _:')
        last_emit = self._code_output[-1]
        self._code_indent += 1
        try:
            yield
        finally:
            self._code_indent -= 1
            if self._code_output[-1] == last_emit:
                self._code_output.pop(0)
            else:
                self.emit_code(f"{name} = '\\n'.join(_)")   

    def _assert_line(self) -> None:
        if not self.line:
            raise RuntimeError(f'{self} has no current line')

    def _assert_transpiler(self) -> None:
        if not self.transpiler:
            raise RuntimeError(f'{self} has no current transpiler')
    
    @contextlib.contextmanager
    def _set_line(self, line: Line) -> ContextManager[None]:
        self._lines.append(line)
        try:
            yield
        finally:
            self._lines.pop()
   
    @contextlib.contextmanager
    def _set_transpiler(self, transpiler: Transpiler) -> ContextManager[None]:
        self._transpilers.append(transpiler)
        try:
            yield
        finally:
            self._transpilers.pop()
    
    @contextlib.contextmanager
    def _set_interpolation(self, start_token: str, end_token: str) -> ContextManager[None]:
        self._interpolations.append((start_token, end_token))
        try:
            yield
        finally:
            self._interpolations.pop()
    
    def _run_transpilers(self, lines: list[Line]) -> None:
        for line in lines:
            with self._set_line(line):
                for transpiler in self.active_transpilers:
                    if not transpiler.matches(self):
                        continue
                    with self._set_transpiler(transpiler):
                        transpiler.transpile(self)
                    break
                else:
                    raise self.error(f'no transpiler matched (tried: {", ".join(transpiler.name for transpiler in self.active_transpilers)})')
    
    def _render_emit(self, indent: int, *output: Any) -> None:
        whitespace = ' ' * (indent + self._render_indent)
        self._render_output.append(whitespace + ''.join(map(str, output)))

    def _render_call(self, indent: int, function: Callable, *args: Any, **kwargs: Any) -> None:
        self._render_indent += indent
        try:
            function(*args, **kwargs)
        finally:
            self._render_indent -= indent

    @contextlib.contextmanager
    def _render_capture(self) -> ContextManager[list[str]]:
        output = self._render_output
        self._render_output = []
        try:
            yield self._render_output
        except self.StopTranspilation:
            pass
        finally:
            self._render_output = output
        

class JunkPlaceholder:

    def __init__(self, junk: Junk, indent: int):
        self.junk = junk
        self.indent = indent
    
    def inject(self, lines: list[str]) -> None:
        index = self.junk._code_output.index(self)
        self.junk._code_output[index:index] = lines
    

from .blueprint import Blueprint, Line, trim
from .splinterpolate import splinterpolate
from .transpiler import Transpiler, TranspilerState