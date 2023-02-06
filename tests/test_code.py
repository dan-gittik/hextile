import pytest

from hextile import transpile


def test_code_block():
    transpile('''
        !
            x = 1
            y = 2
        {x + y}
    ''').render() == '3'
    transpile('''
        !
            def f():
                return {n}
        {f()}
    ''').render(n=3) == '3'


def test_comment():
    transpile('''
        !# This is a comment.
    ''').render() == ''
    transpile('''
        !#
            This is a comment
            that has multiple
            lines.
    ''').render() == ''


def test_tryspilation():
    with pytest.raises(ZeroDivisionError):
        transpile('''
            ! 1/0
        ''').render()
    transpile('''
        !? 1/0
        line
    ''').render() == 'line'
    transpile('''
        !?
            ! 1/0
            never happens
    ''').render() == ''
    transpile('''
        !?
            {line}
    ''').render() == ''
    transpile('''
        !?
            {line}
    ''').render(line='line') == 'line'


def test_interpolation():
    with pytest.raises(NameError):
        transpile('''
            {line}
        ''').render()
    transpile('''
        {line:?''}
    ''').render() == ''
    transpile('''
        {line:?'line' }
    ''').render() == 'line'
    transpile('''
        {line:?default}
    ''').render(default='default') == 'default'


def test_recursion():
    transpile('''
        !.f(n):
            ! if n > 0:
                !.f(n - 1)
            ! else:
                line {n}
        !.f(n)
    ''').render(n=3) == '''
line 3
line 2
line 1
'''