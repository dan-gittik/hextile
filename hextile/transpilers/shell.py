import re

from .. import Junk, TranspilerState, transpiler


class ShellState(TranspilerState):

    def __init__(self, junk: Junk):
        super().__init__(junk)
        self.shell_regex = re.compile(r'''
            ^
            (!)?
            \s*
            (?:
                ([a-zA-Z_][a-zA-Z0-9_]*)
                :\s*
            )?
            (.+)
            $
        ''', flags=re.VERBOSE)
        self.command_name = junk.setting('command_name', 'shell')


@transpiler(name='shell', prefix='$', state=ShellState)
def shell_transpiler(junk: Junk):
    if junk.line.children:
        raise junk.error(f'a shell line cannot have nested lines')
    if not junk.line.content:
        return
    state: ShellState = junk.state
    raise_error, command_name, command = state.shell_regex.match(junk.line.content).groups()
    if not command_name:
        command_name = state.command_name
    junk.add_imports('subprocess', 'shlex', 'functools')
    junk.add_definition('''
        class ShellCommand:

            def __init__(self, exit_code, stdout, stderr):
                self.exit_code = exit_code
                self.stdout = stdout
                self.stderr = stderr
            
            @classmethod
            def execute(cls, *command, raise_error=False):
                command = ' '.join(map(str, command))
                process = subprocess.run(command, shell=True, capture_output=True)
                result = cls(process.returncode, process.stdout, process.stderr)
                if raise_error and not result.success:
                    raise RuntimeError(f'command {command!r} failed: {result.error or result.output}')
                return result
            
            @functools.cached_property
            def success(self):
                return self.exit_code == 0
            
            @functools.cached_property
            def output(self):
                return self.stdout.decode().strip()
            
            @functools.cached_property
            def error(self):
                return self.stderr.decode().strip()
    ''')
    command = junk.interpolate(command)
    junk.emit_code(f'{command_name} = ShellCommand.execute({command}, raise_error={bool(raise_error)})')