import pathlib

import pytest

from hextile import Blueprint, Junk, Transpiler, transpile, transpiler


@pytest.fixture
def content(tmp_path: pathlib.Path):
    path = tmp_path / 'include.blueprint'
    path.write_text('content')
    return path


@pytest.fixture
def base(tmp_path: pathlib.Path):
    path = tmp_path / 'base.blueprint'
    path.write_text('''
<html>
    <head>
        % insert('head')
    </head>
    <body>
        % insert('body', required=True)
    </body>
</html>
'''.strip())
    return path


@pytest.fixture
def line_transpiler():
    @transpiler()
    def line(junk: Junk):
        junk.emit_text('line')
    try:
        yield
    finally:
        del Transpiler.all_transpilers[line.name]


def test_include(content: pathlib.Path):
    assert transpile(f'''
        <p>
            % include({str(content)!r})
        </p>
    ''').render() == '''
<p>
    content
</p>
'''.strip()
    assert transpile('''
        <p>
            % include(path)
        </p>
    ''', path=content).render() == '''
<p>
    content
</p>
'''.strip()


def test_extend(base: pathlib.Path):
    assert transpile(f'''
        % extend({str(base)!r})
        % define('head')
            <title>title</title>

        % define('body')
            <p>content</p>
    ''').render() == '''
<html>
    <head>
        <title>title</title>
    </head>
    <body>
        <p>content</p>
    </body>
</html>
'''.strip()
    assert transpile('''
        % extend(path)
        % define('body')
            <p>content</p>
''', path=base).render() == '''
<html>
    <head>
    </head>
    <body>
        <p>content</p>
    </body>
</html>
'''.strip()
    with pytest.raises(Junk.TranspilationError):
        assert transpile('''
            % extend(path)
            % define('head')
                <title>title</title>
        ''', path=base).render()
    blueprint = Blueprint.resolve('''
% insert('one')
    line 1
''')
    transpile('''
        % extend(base)
        % define('two')
            line 2
    ''', base=blueprint).render() == 'line 1'


def test_transpilers(line_transpiler: Transpiler):
    assert transpile('''
        % transpilers('line')
        ! for i in range(n):
            line {i}
    ''').render(n=3) == '''
line
line
line
'''.strip()
    assert transpile('''
        % transpilers('line')
            ! for i in range(n):
                line {i}
        line {i}
    ''').render(n=3) == '''
line
line
line
line 2
'''.strip()
    assert transpile('''
        % transpilers('text', core=False)
        ! code
        % meta
    ''').render() == '''
! code
% meta
'''.strip()


def test_interpolation():
    assert transpile('''
        % interpolate('<', '>')
        line <x>
        line {x}
    ''').render(x=1) == '''
line 1
line {x}
'''.strip()
    assert transpile('''
        % interpolate('<', '>')
            line <x>
        line {x}
    ''').render(x=1) == '''
line 1
line 1
'''.strip()
    assert transpile('''
        % interpolate(None)
        line <x>
        line {x}
    ''').render(x=1) == '''
line <x>
line {x}
'''.strip()


def test_raw():
    transpile('''
        %:
        ! code
        % meta
        {text}
''') == '''
! code
% meta
{text}
'''
    transpile('''
        %:
            ! code
            % meta
            {text}
        ! x = 1
        {x}
''') == '''
! code
% meta
{text}
1
'''


def test_empty_line():
    transpile('''
        line 1
        
        line 2
        %
        line 3
    ''').render() == '''
line 1
line 2

line 3
'''.strip()


def test_evaluate(content: pathlib.Path):
    transpile(f'''
        %!
            def f():
                return {str(content)!r}
        % include(f())
    ''').render() == 'content'


def test_rerender():
    transpile('''
        %!
            print('!x -= 1')
        {x}
    ''').render(x=2) == '1'