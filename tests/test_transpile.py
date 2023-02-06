from hextile import transpile


def test_transpile_text():
    assert transpile('''
        line
    ''').render() == 'line'


def test_transpile_code():
    context = {}
    assert transpile('''
        ! x = 1
    ''').render(context) == ''
    assert context['x'] == 1


def test_transpile_text_and_code():
    assert transpile('''
        ! if condition:
            line
    ''').render(condition=True) == 'line'
    assert transpile('''
        ! for i in range(n):
            line {i}
    ''').render(n=3) == '''
line 0
line 1
line 2
'''.strip()