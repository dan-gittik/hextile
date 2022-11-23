import pytest

from hextile.utils import URL


def test_url():
    url = URL.parse('scheme://user:1234@host:8000/path?x=1&y=2#fragment')
    assert url.scheme == 'scheme'
    assert url.username == 'user'
    assert url.password == '1234'
    assert url.host == 'host'
    assert url.port == 8000
    assert url.path == '/path'
    assert url.query == {'x': '1', 'y': '2'}
    assert url.fragment == 'fragment'
    assert str(url) == 'scheme://user:********@host:8000/path?x=1&y=2#fragment'
    assert repr(url) == "URL('scheme://user:********@host:8000/path?x=1&y=2#fragment')"


def test_scheme():
    assert URL.parse('path').scheme is None
    assert URL.parse('//host').scheme is None
    assert URL.parse('scheme://host').scheme == 'scheme'
    assert URL.parse('scheme+extra://host').scheme == 'scheme+extra'


def test_username():
    assert URL.parse('path').username is None
    assert URL.parse('user@path').username is None
    assert URL.parse('//host').username is None
    assert URL.parse('//user@host').username == 'user'


def test_password():
    assert URL.parse('path').password is None
    assert URL.parse('user:1234@path').password is None
    assert URL.parse('//user@host').password is None
    assert URL.parse('//user:1234@host').password == '1234'
    assert URL.parse('//user::@@host').password == ':@'
    assert URL.parse('//user:@:@host').password == '@:'


def test_host():
    assert URL.parse('path').host is None
    assert URL.parse('//host').host == 'host'
    assert URL.parse('//host/').host == 'host'
    assert URL.parse('//www.example.com').host == 'www.example.com'


def test_port():
    assert URL.parse('path').port is None
    assert URL.parse('path:8000').port is None
    assert URL.parse('//host').port is None
    assert URL.parse('//host:8000').port == 8000
    with pytest.raises(ValueError, match=r'invalid port port \(expected an integer\)'):
        URL.parse('//host:port')
    with pytest.raises(ValueError, match=r'invalid port 0 \(expected an integer between 1 and 65535\)'):
        URL.parse('//host:0')
    with pytest.raises(ValueError, match=r'invalid port 65536 \(expected an integer between 1 and 65535\)'):
        URL.parse('//host:65536')


def test_path():
    assert URL.parse('').path is None
    assert URL.parse('path').path == 'path'
    assert URL.parse('//host').path is None
    assert URL.parse('//host/').path == '/'
    assert URL.parse('//host/path').path == '/path'
    assert URL.parse('//host/path/').path == '/path/'
    assert URL.parse('//host/directory/file.txt').path == '/directory/file.txt'


def test_query():
    assert URL.parse('path').query == {}
    assert URL.parse('path?').query == {}
    assert URL.parse('path?x=1').query == {'x': '1'}
    assert URL.parse('//host?x=1').query == {'x': '1'}
    assert URL.parse('path?x=1&x=2').query == {'x': '2'}
    assert URL.parse('path?x=1&y=2').query == {'x': '1', 'y': '2'}


def test_fragment():
    assert URL.parse('path').fragment is None
    assert URL.parse('path#').fragment is None
    assert URL.parse('path#fragment').fragment == 'fragment'
    assert URL.parse('//host#fragment').fragment == 'fragment'


def test_format():
    assert str(URL(scheme='scheme')) == 'scheme://'
    assert str(URL(scheme='scheme', host='host')) == 'scheme://host'
    assert str(URL(host='host')) == '//host'
    assert str(URL(username='user')) == ''
    assert str(URL(host='host', username='user')) == '//user@host'
    assert str(URL(password='1234')) == ''
    assert str(URL(host='host', password='1234')) == '//host'
    assert str(URL(host='host', username='user', password='1234')) == '//user:********@host'
    assert str(URL(port=8000)) == ''
    assert str(URL(host='host', port=8000)) == '//host:8000'
    assert str(URL(path='path')) == 'path'
    assert str(URL(path='/path')) == '/path'
    assert str(URL(path='/path/')) == '/path/'
    assert str(URL(host='host', path='path')) == '//host/path'
    assert str(URL(host='host', path='/path')) == '//host/path'
    assert str(URL(host='host', path='/path/')) == '//host/path/'
    assert str(URL(query={'x': 1})) == '?x=1'
    assert str(URL(query={'x': 1, 'y': 2})) == '?x=1&y=2'
    assert str(URL(path='path', query={'x': 1})) == 'path?x=1'
    assert str(URL(host='host', query={'x': 1})) == '//host?x=1'
    assert str(URL(fragment='fragment')) == '#fragment'
    assert str(URL(path='path', fragment='fragment')) == 'path#fragment'
    assert str(URL(host='host', fragment='fragment')) == '//host#fragment'


def test_reveal():
    url = URL(host='host', username='user', password='1234')
    assert str(url) == '//user:********@host'
    assert url.reveal() == '//user:1234@host'


def test_from_url():
    url = URL()
    assert url.parse(url) is url


def test_equality():
    url = URL.parse('scheme://host/path')
    assert url == 'scheme://host/path'
    assert url != 'scheme://host'
    assert url != '//host/path'
    assert url == URL.parse('scheme://host/path')
    assert url != URL.parse('scheme://host')
    assert url != URL.parse('//host/path')


def test_hash():
    url1 = URL.parse('scheme://host/path')
    url2 = URL.parse('scheme://host')
    url3 = URL.parse('//host/path')
    assert len({url1, url1, url2, url2, url3, url3}) == 3