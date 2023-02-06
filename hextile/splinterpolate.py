from __future__ import annotations
from types import CodeType
from typing import Any, Callable, Iterator


quotes = "'", '"'
escape = '\\'


def splinterpolate(
        start_token: str,
        end_token: str,
        string: str,
) -> Iterator[Splinter]:
    if (
        start_token is None
        or string == start_token
        or string == end_token
        or (start_token not in string and end_token not in string)
    ):
        yield Splinter(string)
        return
    length, start_length, end_length = len(string), len(start_token), len(end_token)
    splinter = []
    cursor = 0
    while cursor < length:
        if string[cursor:cursor + start_length] == start_token:
            if string[cursor + start_length:cursor + 2*start_length] == start_token:
                splinter.extend(start_token)
                cursor += 2 * start_length
            else:
                start = cursor + start_length
                end = skip_expression(start_token, end_token, string, start)
                expression = string[start:end].strip()
                if splinter:
                    yield Splinter(''.join(splinter))
                    splinter.clear()
                yield Splinter(expression, is_code=True)
                end += end_length
                cursor = end
        elif string[cursor:cursor + end_length] == end_token:
            if string[cursor + end_length:cursor + 2*end_length] == end_token:
                splinter.extend(end_token)
                cursor += 2 * end_length
            else:
                raise ValueError(f'failed to parse {string!r}: unmatched {end_token!r} at offset {cursor}')
        else:
            splinter.append(string[cursor])
            cursor += 1
    if splinter:
        yield Splinter(''.join(splinter))
    

def skip_expression(start_token: str, end_token: str, string: str, cursor: int) -> int:
    length, start_length, end_length = len(string), len(start_token), len(end_token)
    depth = 1
    while cursor < length:
        if string[cursor:cursor + start_length] == start_token:
            depth += 1
            cursor += start_length
        elif string[cursor:cursor + end_length] == end_token:
            depth -= 1
            if depth == 0:
                break
            cursor += end_length
        elif string[cursor] in quotes:
            cursor = skip_string(string, cursor)
        else:
            cursor += 1
    else:
        raise ValueError(f'failed to parse {string!r}: unmatched {start_token!r} at offset {cursor}')
    return cursor


def skip_string(string: str, cursor: int) -> int:
    length = len(string)
    quote = string[cursor]
    cursor += 1
    while cursor < length:
        if string[cursor] == quote:
            cursor += 1
            break
        if string[cursor] == escape:
            cursor += 2
        else:
            cursor += 1
    else:
        raise ValueError(f'failed to parse {string!r}: unterminated quote at offset {cursor}')
    return cursor


class Splinter:

    _conversions: dict[str, Callable[[Any], str]] = dict(
        a = ascii,
        r = repr,
        s = str,
    )

    def __init__(self, text: str, is_code: bool = False):
        self.text = text
        self.is_code = is_code
        self.code: CodeType = None
        self.format: str = None
        self.conversion: Callable[[Any], str] = None

    def compile(self) -> None:
        if not self.is_code or self.code:
            return
        if len(self.text) > 2 and self.text[-2] == '!':
            self.text, conversion = self.text[:-2], self.text[-1]
            if conversion not in self._conversions:
                raise SyntaxError(f'failed to compile {self.text!r}: invalid conversion character {conversion!r} (expected one of: {", ".join(self._conversions)})')
            self.conversion = self._conversions[conversion]
        try:
            self.code = compile(self.text, '', 'eval')
        except SyntaxError as error:
            offset = error.offset - 1
            if error.text[offset] == ':':
                self.text, self.format = self.text[:offset], self.text[offset + 1:]
                self.code = compile(self.text, '', 'eval')
            else:
                raise