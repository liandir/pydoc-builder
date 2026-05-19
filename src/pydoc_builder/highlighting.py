"""Render Python source as HTML with tokenize-based syntax classes."""

from __future__ import annotations

import io
import keyword
import tokenize

from .utils import escape


_FSTRING_TYPES = {
    getattr(tokenize, name)
    for name in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END")
    if hasattr(tokenize, name)
}

_BUILTIN_FUNCS = frozenset({
    "abs", "all", "any", "ascii", "bin", "callable", "chr", "compile",
    "delattr", "dir", "divmod", "enumerate", "eval", "exec", "filter",
    "format", "getattr", "globals", "hasattr", "hash", "help", "hex", "id",
    "input", "isinstance", "issubclass", "iter", "len", "locals", "map",
    "max", "min", "next", "oct", "open", "ord", "pow", "print", "range",
    "repr", "reversed", "round", "setattr", "slice", "sorted", "sum",
    "super", "vars", "zip", "classmethod", "staticmethod", "property",
})

_BUILTIN_TYPES = frozenset({
    "bool", "bytearray", "bytes", "complex", "dict", "float", "frozenset",
    "int", "list", "object", "set", "str", "tuple", "type", "memoryview",
    "BaseException", "Exception", "ValueError", "TypeError", "KeyError",
    "IndexError", "RuntimeError", "StopIteration", "NotImplementedError",
    "FileNotFoundError", "IOError", "OSError", "AttributeError",
    "ImportError", "ModuleNotFoundError", "ZeroDivisionError",
    "ArithmeticError", "AssertionError", "LookupError", "NameError",
    "UnboundLocalError", "OverflowError", "RecursionError",
    "PermissionError", "TimeoutError", "ConnectionError",
})


def highlight_python(source: str) -> str:
    """Render Python source as HTML with tokenize-based syntax classes."""

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenizeError, IndentationError, SyntaxError):
        return escape(source)

    line_starts = [0]
    for index, character in enumerate(source):
        if character == "\n":
            line_starts.append(index + 1)

    def offset(line: int, col: int) -> int:
        if line - 1 >= len(line_starts):
            return len(source)
        return min(line_starts[line - 1] + col, len(source))

    spans: list[tuple[int, int, str]] = []
    prev_keyword = ""
    for tok in tokens:
        kind = tok.type
        text = tok.string
        css: str | None = None
        if kind == tokenize.COMMENT:
            css = "tok-comment"
        elif kind == tokenize.STRING or kind in _FSTRING_TYPES:
            css = "tok-string"
        elif kind == tokenize.NUMBER:
            css = "tok-number"
        elif kind == tokenize.NAME:
            if keyword.iskeyword(text) or text in keyword.softkwlist:
                css = "tok-keyword"
                prev_keyword = text
                start = offset(*tok.start)
                end = offset(*tok.end)
                if start < end:
                    spans.append((start, end, css))
                continue
            if prev_keyword == "def":
                css = "tok-def-name"
            elif prev_keyword == "class":
                css = "tok-class-name"
            elif text in {"self", "cls"}:
                css = "tok-self"
            elif text in _BUILTIN_TYPES:
                css = "tok-builtin-type"
            elif text in _BUILTIN_FUNCS:
                css = "tok-builtin-func"
        elif kind == tokenize.OP:
            css = "tok-punct"

        prev_keyword = ""
        if css is None:
            continue
        start = offset(*tok.start)
        end = offset(*tok.end)
        if start < end:
            spans.append((start, end, css))

    out: list[str] = []
    cursor = 0
    for start, end, css in spans:
        if start > cursor:
            out.append(escape(source[cursor:start]))
        out.append(f'<span class="{css}">{escape(source[start:end])}</span>')
        cursor = end
    if cursor < len(source):
        out.append(escape(source[cursor:]))
    return "".join(out)
