from __future__ import annotations

import urllib.parse


class URL:

    min_port = 1
    max_port = 2**16 - 1
    password_placeholder = 8 * '*'

    def __init__(
            self,
            *,
            scheme: str = None,
            username: str = None,
            password: str = None,
            host: str = None,
            port: int = None,
            path: str = None,
            query: dict[str, str] = None,
            fragment: str = None,
    ):
        if query is None:
            query = {}
        self.scheme = scheme
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.path = path
        self.query = query
        self.fragment = fragment
    
    def __str__(self):
        return self._format(show_password=False)

    def __repr__(self):
        return f'<URL {self}>'
    
    @classmethod
    def parse(cls, string: URLType) -> URL:
        if isinstance(string, URL):
            return string
        result = urllib.parse.urlparse(string)
        scheme = username = password = host = port = path = query = fragment = None
        if result.scheme:
            scheme = result.scheme
        if result.netloc:
            if '@' in result.netloc:
                credentials, domain = result.netloc.rsplit('@', 1)
                if ':' in credentials:
                    username, password = credentials.split(':', 1)
                else:
                    username = credentials
            else:
                domain = result.netloc
            if ':' in domain:
                host, port = domain.split(':', 1)
                try:
                    port = int(port)
                except ValueError:
                    raise ValueError(f'invalid port {port} (expected an integer)')
                if not cls.min_port <= port <= cls.max_port:
                    raise ValueError(f'invalid port {port} (expected an integer between {cls.min_port} and {cls.max_port})')
            else:
                host = domain
        if result.path:
            path = result.path
        if result.query:
            query = dict(urllib.parse.parse_qsl(result.query))
        if result.fragment:
            fragment = result.fragment
        return cls(
            scheme = scheme,
            username = username,
            password = password,
            host = host,
            port = port,
            path = path,
            query = query,
            fragment = fragment,
        )
    
    def reveal(self) -> str:
        return self._format(show_password=True)
    
    def _format(self, show_password: bool) -> str:
        output = []
        if self.scheme:
            output.append(f'{self.scheme}:')
        if self.scheme or self.host:
            output.append('//')
        if self.host:
            if self.username:
                output.append(self.username)
                if self.password:
                    if show_password:
                        password = self.password
                    else:
                        password = self.password_placeholder
                    output.append(f':{password}')
                output.append('@')
            output.append(self.host)
            if self.port:
                output.append(f':{self.port}')
        if self.path:
            if self.host and not self.path.startswith('/'):
                output.append('/')
            output.append(self.path)
        if self.query:
            output.append('?' + urllib.parse.urlencode(self.query))
        if self.fragment:
            output.append(f'#{self.fragment}')
        return ''.join(output)
    

URLType = str | URL