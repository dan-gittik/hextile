from .. import Junk, transpiler


@transpiler(name='text', core=True, priority=3)
def text_transpiler(junk: Junk) -> None:
    junk.emit_text(junk.line.content)
    junk.recurse()