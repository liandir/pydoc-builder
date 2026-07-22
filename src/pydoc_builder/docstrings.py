"""Parse and render Google-style and free-form docstrings."""

from __future__ import annotations

import ast
import re
from collections.abc import Callable

from .highlighting import highlight_python
from .markdown import render_markdown
from .utils import escape

Resolver = Callable[[str], str | None]


_FIELD_HEAD = re.compile(r"^\*{0,2}[A-Za-z_]\w*(\.\w+)*(\s*\([^)]*\))?\s*:")


def doc_block(
    docstring: str,
    resolver: Resolver | None = None,
    param_annotations: dict[str, str] | None = None,
    return_annotation: str = "",
) -> str:
    """Render a docstring with structured sections when available.

    Args:
        docstring: Raw docstring text extracted from a module or API object.
        resolver: Optional symbol resolver for inline ``code`` cross-references.
        param_annotations: Optional ``name -> annotation`` map used to backfill
            argument types that the docstring author omitted.
        return_annotation: Optional return-type annotation from the signature,
            used to backfill the Returns section when the docstring lists a
            return value but omits its type.

    Returns:
        HTML fragment for the rendered docstring, or a muted placeholder
        when ``docstring`` is empty.
    """

    if not docstring:
        return '<p class="muted">No docstring.</p>'
    if _has_structured_sections(docstring):
        return _structured_doc_block(docstring, resolver, param_annotations, return_annotation)
    return _plain_doc_block(docstring, resolver)


def split_docstring_sections(docstring: str) -> dict[str, list[str]]:
    """Split a docstring into summary and named structured sections.

    Args:
        docstring: Raw docstring text to partition by Google-style headings.

    Returns:
        A mapping from section name (``summary``, ``args``, ``returns``,
        ``yields``, ``raises``, ``examples``, ``other``) to the lines that
        belong to it.
    """

    aliases = {
        "args:": "args",
        "arguments:": "args",
        "parameters:": "args",
        "attributes:": "attributes",
        "returns:": "returns",
        "yields:": "yields",
        "raises:": "raises",
    }
    sections: dict[str, list[str]] = {
        "summary": [],
        "args": [],
        "attributes": [],
        "examples": [],
        "returns": [],
        "yields": [],
        "raises": [],
        "other": [],
    }
    current = "summary"
    lines = docstring.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped_lower = line.strip().lower()
        if stripped_lower in {"example", "examples"}:
            current = "examples"
            if index + 1 < len(lines) and set(lines[index + 1].strip()) <= {"-"}:
                index += 2
                continue
            index += 1
            continue
        key = aliases.get(line.strip().lower())
        if key is not None:
            current = key
            index += 1
            continue
        sections[current if current in sections else "other"].append(line.rstrip())
        index += 1
    return sections


def parse_doc_fields(lines: list[str]) -> list[dict[str, str]]:
    """Parse indented Google-style field lines.

    Args:
        lines: Lines from a section body (e.g. the body of an ``Args:`` block).

    Returns:
        One dict per field with ``name``, ``type``, and ``description`` keys.
    """

    fields: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _looks_like_field(line):
            if current is not None:
                fields.append(current)
            current = _parse_doc_field(line)
        elif current is not None:
            sep = "\n" if current["description"] else ""
            current["description"] = f'{current["description"]}{sep}{line}'
        else:
            current = {"name": "", "type": "", "description": line}
    if current is not None:
        fields.append(current)
    return fields


def _plain_doc_block(docstring: str, resolver: Resolver | None = None) -> str:
    """Render a free-form docstring as prose with optional literal blocks."""

    parts = _render_prose_lines(docstring.splitlines(), resolver)
    return f'<div class="docstring plain-docstring">{"".join(parts)}</div>'


def _has_structured_sections(docstring: str) -> bool:
    """Return whether a docstring contains renderable Google-style sections."""

    headings = {"args:", "arguments:", "parameters:", "attributes:", "returns:", "yields:", "raises:"}
    return any(line.strip().lower() in headings | {"example", "examples"} for line in docstring.splitlines())


def _structured_doc_block(
    docstring: str,
    resolver: Resolver | None = None,
    param_annotations: dict[str, str] | None = None,
    return_annotation: str = "",
) -> str:
    """Render Google-style docstring sections as semantic HTML."""

    sections = split_docstring_sections(docstring)
    parts: list[str] = ['<div class="docstring structured-docstring">']
    if sections["summary"]:
        parts.append(_render_summary(sections["summary"], resolver))
    if sections["examples"]:
        parts.append(_render_examples_section(sections["examples"], resolver))
    if sections["args"]:
        parts.append(_render_field_section("Arguments", sections["args"], resolver, param_annotations))
    if sections["attributes"]:
        parts.append(_render_field_section("Attributes", sections["attributes"], resolver))
    if sections["returns"]:
        parts.append(_render_field_section("Returns", sections["returns"], resolver, return_annotation=return_annotation))
    if sections["yields"]:
        parts.append(_render_field_section("Yields", sections["yields"], resolver))
    if sections["raises"]:
        parts.append(_render_field_section("Raises", sections["raises"], resolver))
    if sections["other"]:
        extra = "\n".join(sections["other"]).strip()
        parts.append(f'<pre class="doc-extra">{escape(extra)}</pre>')
    parts.append("</div>")
    return "\n".join(part for part in parts if part)


def _render_summary(lines: list[str], resolver: Resolver | None = None) -> str:
    """Render summary lines before the first structured section."""

    return "".join(_render_prose_lines(lines, resolver))


_UL_ITEM = re.compile(r"^\s*[-*+]\s+(.+)$")
_OL_ITEM = re.compile(r"^\s*\d+[.)]\s+(.+)$")


def _render_description(text: str, resolver: Resolver | None) -> str:
    """Render Markdown in a structured field description."""

    return render_markdown(text, resolver)


def _render_prose_lines(lines: list[str], resolver: Resolver | None = None) -> list[str]:
    """Render Markdown prose while preserving literal and display-math blocks."""

    parts: list[str] = []
    markdown_lines: list[str] = []
    literal: list[str] = []
    math_block: list[str] = []
    in_fence = False
    list_active = False

    def flush_markdown() -> None:
        if markdown_lines:
            text = "\n".join(markdown_lines).strip("\n")
            if text.strip():
                parts.append(render_markdown(text, resolver))
            markdown_lines.clear()

    def flush_literal() -> None:
        if literal:
            text = "\n".join(line.rstrip() for line in literal).strip("\n")
            if text.strip():
                parts.append(f'<pre class="doc-literal">{escape(text)}</pre>')
            literal.clear()

    def flush_math() -> None:
        if math_block:
            text = "\n".join(line.strip() for line in math_block).strip()
            if text:
                parts.append(f'<div class="math-block">{escape(text)}</div>')
            math_block.clear()

    for line in lines:
        stripped = line.strip()
        if math_block:
            math_block.append(line)
            if stripped in {"\\]", "$$"}:
                flush_math()
            continue
        if in_fence:
            markdown_lines.append(line)
            if line.startswith("```"):
                in_fence = False
            continue
        if not line.strip():
            flush_literal()
            markdown_lines.append("")
            list_active = False
            continue
        if stripped in {"\\[", "$$"}:
            flush_markdown()
            flush_literal()
            math_block.append(line)
            continue
        if line.startswith("```"):
            flush_literal()
            markdown_lines.append(line)
            in_fence = True
            list_active = False
            continue
        ul = _UL_ITEM.match(line)
        ol = _OL_ITEM.match(line)
        if ul or ol:
            flush_literal()
            markdown_lines.append(line)
            list_active = True
            continue
        if list_active and line.startswith((" ", "\t")):
            markdown_lines.append(line)
            continue
        if line.startswith((" ", "\t")):
            flush_markdown()
            literal.append(line)
            continue
        flush_literal()
        list_active = False
        markdown_lines.append(line)
    flush_markdown()
    flush_literal()
    flush_math()
    return parts


def _render_field_section(
    title: str,
    lines: list[str],
    resolver: Resolver | None = None,
    param_annotations: dict[str, str] | None = None,
    return_annotation: str = "",
) -> str:
    """Render a structured docstring field section."""

    is_return = title in {"Returns", "Yields"}
    fields = _parse_return_fields(lines) if is_return else parse_doc_fields(lines)
    if title == "Arguments":
        fields = [field for field in fields if not field["name"].startswith("*")]
        if param_annotations:
            for field in fields:
                if not field["type"] and field["name"] in param_annotations:
                    field["type"] = param_annotations[field["name"]]
    if title == "Returns" and return_annotation:
        if not fields:
            fields = [{"name": "", "type": return_annotation, "description": ""}]
        elif not fields[0]["type"]:
            fields[0]["type"] = return_annotation
    if not fields:
        return ""
    type_class = "doc-return-type" if is_return else "doc-field-type"
    rows = "\n".join(_render_doc_field(field, resolver, type_class) for field in fields)
    return f"""
    <section class="doc-section">
      <h3>{escape(title)}</h3>
      <dl class="doc-fields">{rows}</dl>
    </section>
    """


def _render_examples_section(lines: list[str], resolver: Resolver | None = None) -> str:
    """Render example docstring lines with doctest code blocks."""

    chunks: list[str] = []
    prose: list[str] = []
    code: list[str] = []

    def flush_prose() -> None:
        if prose:
            chunks.append(_render_summary(prose, resolver))
            prose.clear()

    def flush_code() -> None:
        if code:
            code_text = "\n".join(code).strip()
            chunks.append(f'<pre class="example-code"><code>{escape(code_text)}</code></pre>')
            code.clear()

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_prose()
            flush_code()
            continue
        if stripped.startswith((">>>", "...")):
            flush_prose()
            code.append(stripped)
        elif code and (raw_line.startswith(" ") or raw_line.startswith("\t")):
            code.append(line)
        else:
            flush_code()
            prose.append(stripped)
    flush_prose()
    flush_code()
    if not chunks:
        return ""
    return f"""
    <section class="doc-section">
      <h3>Examples</h3>
      {"".join(chunks)}
    </section>
    """


def _parse_return_fields(lines: list[str]) -> list[dict[str, str]]:
    """Parse return or yield section lines as typed values."""

    fields: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    field_indent: int | None = None
    for raw_line in lines:
        if not raw_line.strip():
            continue
        line = raw_line.strip()
        indent = len(raw_line) - len(raw_line.lstrip())
        candidate = _parse_return_field(line)
        starts_field = bool(candidate["type"]) and (
            current is None or field_indent is None or indent <= field_indent
        )
        if starts_field:
            if current is not None:
                fields.append(current)
            current = candidate
            field_indent = indent
            continue
        if current is None:
            current = candidate
            field_indent = indent
            continue
        sep = "\n" if current["description"] else ""
        current["description"] = f'{current["description"]}{sep}{line}'
    if current is not None:
        fields.append(current)
    return fields


def _parse_return_field(line: str) -> dict[str, str]:
    """Parse one return field, accepting composite Python type expressions."""

    split = _split_field_line(line)
    if split is None:
        return {"name": "", "type": "", "description": line}
    head, description = split
    name = ""
    type_name = head
    if head.endswith(")") and "(" in head:
        name_part, _, type_part = head.partition("(")
        possible_name = name_part.strip()
        if re.fullmatch(r"\*{0,2}[A-Za-z_]\w*", possible_name):
            name = possible_name
            type_name = type_part[:-1].strip()
            return {"name": name, "type": type_name, "description": description}
    try:
        ast.parse(head, mode="eval")
    except SyntaxError:
        return {"name": "", "type": "", "description": line}
    return {"name": name, "type": type_name, "description": description}


def _split_field_line(line: str) -> tuple[str, str] | None:
    """Split at the first colon outside brackets and quoted strings."""

    brackets: list[str] = []
    quote = ""
    escaped = False
    pairs = {")": "(", "]": "[", "}": "{"}
    for index, char in enumerate(line):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            continue
        if char in {'"', "'"}:
            quote = char
        elif char in "([{":
            brackets.append(char)
        elif char in pairs:
            if brackets and brackets[-1] == pairs[char]:
                brackets.pop()
        elif char == ":" and not brackets:
            head = line[:index].strip()
            if head:
                return head, line[index + 1:].strip()
            return None
    return None


def _looks_like_field(line: str) -> bool:
    """Return whether a line looks like a docstring field.

    Args:
        line: A stripped section line; field starts begin with an identifier
            (optionally followed by ``(type)``) and a colon.

    Returns:
        ``True`` when the line begins a new field, ``False`` when it should
        be treated as a continuation of the previous field's description.
    """

    return bool(_FIELD_HEAD.match(line))


def _parse_doc_field(line: str) -> dict[str, str]:
    """Parse one ``name (type): description`` docstring field."""

    head, _, description = line.partition(":")
    head = head.strip()
    type_name = ""
    name = ""
    if head.endswith(")") and "(" in head:
        name_part, _, type_part = head.rpartition("(")
        name = name_part.strip()
        type_name = type_part[:-1].strip()
    elif "." in head and " " not in head:
        # A dotted head (``torch.nn.Module``) is never a valid parameter name,
        # so treat it as a bare type — relevant for ``Returns:`` blocks.
        type_name = head
    elif " " not in head and head:
        name = head
    else:
        type_name = head
    return {"name": name, "type": type_name, "description": description.strip()}


def _render_doc_field(
    field: dict[str, str],
    resolver: Resolver | None = None,
    type_class: str = "doc-field-type",
) -> str:
    """Render one parsed docstring field."""

    name = field["name"]
    type_name = field["type"]
    description = field["description"]
    name_html = f'<span class="doc-field-name">{escape(name)}</span>' if name else ""
    type_html = f'<span class="{type_class}">{highlight_python(type_name)}</span>' if type_name else ""
    description_html = _render_description(description, resolver)
    return f"""
      <div class="doc-field">
        <dt>{name_html}{type_html}</dt>
        <dd>{description_html}</dd>
      </div>
    """
