"""Parse and render Google-style and free-form docstrings."""

from __future__ import annotations

import re
from collections.abc import Callable

from .utils import escape, inline_markup

Resolver = Callable[[str], str | None]


_FIELD_HEAD = re.compile(r"^\*{0,2}[A-Za-z_]\w*(\s*\([^)]*\))?\s*:")


def doc_block(
    docstring: str,
    resolver: Resolver | None = None,
    param_annotations: dict[str, str] | None = None,
) -> str:
    """Render a docstring with structured sections when available.

    Args:
        docstring: Raw docstring text extracted from a module or API object.
        resolver: Optional symbol resolver for inline ``code`` cross-references.
        param_annotations: Optional ``name -> annotation`` map used to backfill
            argument types that the docstring author omitted.

    Returns:
        HTML fragment for the rendered docstring, or a muted placeholder
        when ``docstring`` is empty.
    """

    if not docstring:
        return '<p class="muted">No docstring.</p>'
    if _has_structured_sections(docstring):
        return _structured_doc_block(docstring, resolver, param_annotations)
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
        parts.append(_render_field_section("Returns", sections["returns"], resolver))
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
    """Render a field description, falling back to prose rendering for lists."""

    lines = text.splitlines()
    has_list = any(_UL_ITEM.match(line) or _OL_ITEM.match(line) for line in lines)
    if has_list:
        return "".join(_render_prose_lines(lines, resolver))
    flat = " ".join(line.strip() for line in lines).strip()
    return inline_markup(escape(flat), resolver)


def _render_prose_lines(lines: list[str], resolver: Resolver | None = None) -> list[str]:
    """Render prose lines while preserving lists, literal blocks, and math."""

    parts: list[str] = []
    paragraph: list[str] = []
    literal: list[str] = []
    math_block: list[str] = []
    list_items: list[str] = []
    list_kind: str | None = None

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(line.strip() for line in paragraph).strip()
            if text:
                parts.append(f"<p>{inline_markup(escape(text), resolver)}</p>")
            paragraph.clear()

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

    def flush_list() -> None:
        nonlocal list_kind
        if list_items:
            tag = list_kind or "ul"
            rows = "".join(
                f"<li>{inline_markup(escape(item), resolver)}</li>"
                for item in list_items
            )
            parts.append(f"<{tag}>{rows}</{tag}>")
            list_items.clear()
        list_kind = None

    for line in lines:
        stripped = line.strip()
        if math_block:
            math_block.append(line)
            if stripped in {"\\]", "$$"}:
                flush_math()
            continue
        if not line.strip():
            flush_paragraph()
            flush_literal()
            flush_list()
            continue
        if stripped in {"\\[", "$$"}:
            flush_paragraph()
            flush_literal()
            flush_list()
            math_block.append(line)
            continue
        ul = _UL_ITEM.match(line)
        ol = _OL_ITEM.match(line)
        if ul or ol:
            flush_paragraph()
            flush_literal()
            kind = "ul" if ul else "ol"
            if list_kind is not None and list_kind != kind:
                flush_list()
            list_kind = kind
            list_items.append((ul or ol).group(1).strip())
            continue
        if list_items and line.startswith((" ", "\t")):
            list_items[-1] = f"{list_items[-1]} {stripped}"
            continue
        if list_items:
            flush_list()
        if line.startswith((" ", "\t")):
            flush_paragraph()
            literal.append(line)
            continue
        flush_literal()
        paragraph.append(line)
    flush_paragraph()
    flush_literal()
    flush_list()
    flush_math()
    return parts


def _render_field_section(
    title: str,
    lines: list[str],
    resolver: Resolver | None = None,
    param_annotations: dict[str, str] | None = None,
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

    fields = parse_doc_fields(lines)
    for field in fields:
        if field["name"] and not field["type"]:
            field["type"] = field["name"]
            field["name"] = ""
    return fields


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
    name = head
    if head.endswith(")") and "(" in head:
        name, _, type_part = head.rpartition("(")
        name = name.strip()
        type_name = type_part[:-1].strip()
    elif " " not in head and head:
        name = head
    else:
        name = ""
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
    type_html = f'<span class="{type_class}">{escape(type_name)}</span>' if type_name else ""
    description_html = _render_description(description, resolver)
    return f"""
      <div class="doc-field">
        <dt>{name_html}{type_html}</dt>
        <dd>{description_html}</dd>
      </div>
    """
