import itertools

from .. import Junk, Splinter, TranspilerState, transpiler


class CodeState(TranspilerState):

    def __init__(self, junk: Junk):
        super().__init__(junk)
        self.variable_name = junk.setting('variable_name', '_{id}')
        self._id = itertools.count()
    
    def get_variable_name(self) -> str:
        return self.variable_name.format(id=next(self._id))


@transpiler(name='code', prefix='!', core=True, state=CodeState)
def code_transpiler(junk: Junk) -> None:
    junk.line.align_children()
    if junk.line.content.startswith('#'):
        return
    elif junk.line.content.startswith('?'):
        code = junk.line.content[1:].lstrip()
        with junk.try_emit_code():
            if code:
                junk.emit_code(code)
            junk.recurse(indent=+1)
    elif junk.line.content.startswith('.'):
        if junk.line.content.endswith(':'):
            if not junk.line.children:
                raise junk.error('function definitions should have nested lines')
            name, parameters = junk.line.content[1:-2].strip().split('(', 1)
            junk.emit_code(f'def __function_{name}__({parameters}):')
            junk.line.align_children(to=0)
            junk.recurse(indent=+1)
        else:
            if junk.line.children:
                raise junk.error('function invocations should not have nested lines')
            name, arguments = junk.line.content[1:-1].strip().split('(', 1)
            junk.emit_code(f'{junk.CALL}({junk.line.indent}, __function_{name}__, {arguments})')
    elif junk.line.content:
        junk.emit_code(junk.line.content)
        junk.recurse(indent=+1)
    elif junk.line.children:
        junk.emit_code(junk.line.to_string(children_only=True))


@code_transpiler.extend_interpolation
def interpolate(junk: Junk, splinter: Splinter) -> None:
    if not splinter.format or '?' not in splinter.format:
        return
    state: CodeState = junk.state
    splinter.format, default = splinter.format.split('?', 1)
    variable_name = state.get_variable_name()
    junk.emit_code(f'''
        try:
            {variable_name} = {splinter.text}
        except Exception:
            {variable_name} = {default}
    ''')
    splinter.text = variable_name