"""Minimal markdown-to-HTML renderer for README and docstring prose.

Supports a deliberate subset of CommonMark plus GFM tables — ATX headings,
paragraphs, fenced code blocks, unordered and ordered lists, blockquotes,
horizontal rules, pipe-style tables, inline code, links, **bold** and
*italic*. Anything outside this subset is escaped and passed through as
text, so output is always safe HTML.
"""

from __future__ import annotations

import html
import re
from collections.abc import Callable
from urllib.parse import urlsplit


Resolver = Callable[[str], str | None]


def render_markdown(text: str, resolver: Resolver | None = None) -> str:
    """Render markdown ``text`` to an HTML fragment.

    Args:
        text: Markdown source to convert.
        resolver: Optional symbol resolver for inline code cross-references.

    Returns:
        An HTML string containing one element per parsed block, joined by
        newlines.
    """

    blocks = _parse_blocks(text.splitlines())
    return "\n".join(_render_block(block, resolver) for block in blocks)


def _parse_blocks(lines: list[str]) -> list[tuple]:
    """Group ``lines`` into a flat list of block tuples for rendering."""

    blocks: list[tuple] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.lstrip().startswith("```"):
            lang = line.lstrip()[3:].strip()
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            blocks.append(("code", lang, "\n".join(code_lines)))
            continue
        heading_match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if heading_match:
            level = len(heading_match.group(1))
            blocks.append(("heading", level, heading_match.group(2)))
            i += 1
            continue
        if re.match(r"^(\*{3,}|-{3,}|_{3,})\s*$", line):
            blocks.append(("hr",))
            i += 1
            continue
        if line.startswith(">"):
            quote_lines: list[str] = []
            while i < len(lines) and lines[i].startswith(">"):
                quote_lines.append(lines[i].lstrip(">").lstrip())
                i += 1
            blocks.append(("blockquote", " ".join(quote_lines)))
            continue
        if re.match(r"^\s*[-*+]\s+", line):
            items, i = _collect_list(lines, i, r"^\s*[-*+]\s+(.+)$")
            blocks.append(("ul", items))
            continue
        if re.match(r"^\s*\d+[.)]\s+", line):
            items, i = _collect_list(lines, i, r"^\s*\d+[.)]\s+(.+)$")
            blocks.append(("ol", items))
            continue
        table = _try_parse_table(lines, i)
        if table is not None:
            block, i = table
            blocks.append(block)
            continue
        para_lines: list[str] = []
        while i < len(lines) and lines[i].strip() and not _starts_block(lines[i]):
            para_lines.append(lines[i].strip())
            i += 1
        if para_lines:
            blocks.append(("paragraph", " ".join(para_lines)))
    return blocks


def _collect_list(lines: list[str], start: int, item_pattern: str) -> tuple[list[str], int]:
    """Collect contiguous list items matching ``item_pattern`` starting at ``start``."""

    items: list[str] = []
    i = start
    while i < len(lines):
        match = re.match(item_pattern, lines[i])
        if match:
            items.append(match.group(1))
            i += 1
        elif lines[i].strip() and lines[i].startswith((" ", "\t")) and items:
            items[-1] += " " + lines[i].strip()
            i += 1
        else:
            break
    return items, i


_TABLE_ALIGN = re.compile(r"^\s*:?-{3,}:?\s*$")


def _try_parse_table(lines: list[str], start: int) -> tuple[tuple, int] | None:
    """Parse a GFM pipe table starting at ``lines[start]`` if one is present.

    Args:
        lines: All input lines.
        start: Index where the candidate header row begins.

    Returns:
        A ``(block, next_index)`` pair when a valid table is parsed, or
        ``None`` when the candidate is not a table.
    """

    if start + 1 >= len(lines):
        return None
    header_line = lines[start]
    sep_line = lines[start + 1]
    if "|" not in header_line or "|" not in sep_line:
        return None
    header_cells = _split_table_row(header_line)
    sep_cells = _split_table_row(sep_line)
    if not header_cells or len(sep_cells) != len(header_cells):
        return None
    aligns: list[str] = []
    for cell in sep_cells:
        if not _TABLE_ALIGN.match(cell):
            return None
        trimmed = cell.strip()
        left = trimmed.startswith(":")
        right = trimmed.endswith(":")
        if left and right:
            aligns.append("center")
        elif right:
            aligns.append("right")
        elif left:
            aligns.append("left")
        else:
            aligns.append("")

    rows: list[list[str]] = []
    i = start + 2
    while i < len(lines) and lines[i].strip() and "|" in lines[i]:
        cells = _split_table_row(lines[i])
        if len(cells) < len(header_cells):
            cells = cells + [""] * (len(header_cells) - len(cells))
        elif len(cells) > len(header_cells):
            cells = cells[: len(header_cells)]
        rows.append(cells)
        i += 1
    return ("table", header_cells, aligns, rows), i


def _split_table_row(line: str) -> list[str]:
    """Split a pipe-delimited table row, ignoring escaped pipes.

    Args:
        line: One source line from a candidate table.

    Returns:
        The list of trimmed cell contents (outer pipes are stripped).
    """

    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    cells: list[str] = []
    buf: list[str] = []
    escape = False
    for ch in stripped:
        if escape:
            buf.append(ch)
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == "|":
            cells.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    cells.append("".join(buf).strip())
    return cells


def _starts_block(line: str) -> bool:
    """Return whether ``line`` starts a non-paragraph block."""

    return (
        line.lstrip().startswith("```")
        or bool(re.match(r"^#{1,6}\s+", line))
        or bool(re.match(r"^(\*{3,}|-{3,}|_{3,})\s*$", line))
        or line.startswith(">")
        or bool(re.match(r"^\s*[-*+]\s+", line))
        or bool(re.match(r"^\s*\d+[.)]\s+", line))
    )


def _render_block(block: tuple, resolver: Resolver | None = None) -> str:
    """Render one parsed block tuple to HTML."""

    kind = block[0]
    if kind == "heading":
        level, text = block[1], block[2]
        return f"<h{level}>{render_inline(text, resolver)}</h{level}>"
    if kind == "paragraph":
        return f"<p>{render_inline(block[1], resolver)}</p>"
    if kind == "code":
        lang, code = block[1], block[2]
        cls = f' class="language-{html.escape(lang)}"' if lang else ""
        icon = (
            '<svg class="copy-icon" viewBox="0 0 16 16" aria-hidden="true">'
            '<rect x="4.5" y="4.5" width="8" height="9" rx="1.25" fill="none" '
            'stroke="currentColor" stroke-width="1.3"/>'
            '<path d="M3.5 11V3.25A1.25 1.25 0 0 1 4.75 2H10" fill="none" '
            'stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>'
            "</svg>"
            '<svg class="check-icon" viewBox="0 0 16 16" aria-hidden="true">'
            '<path d="M3.5 8.5l3 3 6-6.5" fill="none" stroke="currentColor" '
            'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
            "</svg>"
        )
        return (
            '<div class="code-block">'
            '<button type="button" class="copy-btn" aria-label="Copy code" '
            f'onclick="__copyCode(this)">{icon}</button>'
            f"<pre><code{cls}>{html.escape(code)}</code></pre>"
            "</div>"
        )
    if kind == "hr":
        return "<hr>"
    if kind == "blockquote":
        return f"<blockquote>{render_inline(block[1], resolver)}</blockquote>"
    if kind in ("ul", "ol"):
        items = "".join(f"<li>{render_inline(item, resolver)}</li>" for item in block[1])
        return f"<{kind}>{items}</{kind}>"
    if kind == "table":
        headers, aligns, rows = block[1], block[2], block[3]
        head = "".join(
            f'<th{_align_attr(align)}>{render_inline(cell, resolver)}</th>'
            for cell, align in zip(headers, aligns)
        )
        body = "".join(
            "<tr>"
            + "".join(
                f'<td{_align_attr(align)}>{render_inline(cell, resolver)}</td>'
                for cell, align in zip(row, aligns)
            )
            + "</tr>"
            for row in rows
        )
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
    return ""


def _align_attr(align: str) -> str:
    """Return a ``style="text-align: …"`` attribute fragment for a column alignment.

    Args:
        align: One of ``""``, ``"left"``, ``"center"``, or ``"right"``.

    Returns:
        The attribute string (with leading space) or an empty string when no
        alignment is requested.
    """

    return f' style="text-align: {align}"' if align else ""


_DOUBLE_CODE = re.compile(r"``([^\r\n]+?)``")
_SINGLE_CODE = re.compile(r"`([^`\r\n]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BOLD = re.compile(r"\*\*([^*]+?)\*\*")
_ITALIC = re.compile(r"(?<![\*\w])\*([^*\s][^*]*?)\*(?![\*\w])")


def render_inline(
    text: str,
    resolver: Resolver | None = None,
    *,
    allow_links: bool = True,
) -> str:
    """Render safe inline Markdown from an unescaped text run.

    Single and double backticks produce code spans. A resolved code token is
    linked to its API object. When ``allow_links`` is false, Markdown links
    are reduced to their visible labels and bare URLs remain plain text; this
    is useful inside summary cards that are already wrapped in an anchor.

    Args:
        text: Unescaped inline Markdown source.
        resolver: Optional symbol resolver for inline code cross-references.
        allow_links: Whether to emit anchors for Markdown links and bare URLs.

    Returns:
        A safe HTML fragment containing only inline elements.
    """

    code_stash: list[str] = []
    link_stash: list[str] = []

    def stash_code(match: re.Match[str]) -> str:
        content = match.group(1)
        content_html = html.escape(content)
        href = resolver(content) if resolver else None
        if href:
            rendered = (
                f'<a class="api-xref" href="{html.escape(href, quote=True)}">'
                f"<code>{content_html}</code></a>"
            )
        else:
            rendered = f"<code>{content_html}</code>"
        code_stash.append(rendered)
        return f"\x00C{len(code_stash) - 1}\x00"

    protected = _DOUBLE_CODE.sub(stash_code, text)
    protected = _SINGLE_CODE.sub(stash_code, protected)

    def stash_link(match: re.Match[str]) -> str:
        label, destination = match.group(1), match.group(2).strip()
        label_html = _format_inline_text(label, autolink=False)
        if allow_links and _is_safe_link(destination):
            rendered = (
                f'<a href="{html.escape(destination, quote=True)}">'
                f"{label_html}</a>"
            )
        elif allow_links:
            return match.group(0)
        else:
            rendered = label_html
        link_stash.append(rendered)
        return f"\x00L{len(link_stash) - 1}\x00"

    protected = _LINK.sub(stash_link, protected)
    rendered = _format_inline_text(protected, autolink=allow_links)
    for index, link_html in enumerate(link_stash):
        rendered = rendered.replace(f"\x00L{index}\x00", link_html)
    for index, code_html in enumerate(code_stash):
        rendered = rendered.replace(f"\x00C{index}\x00", code_html)
    return rendered


def _format_inline_text(text: str, *, autolink: bool) -> str:
    """Escape text and apply emphasis plus optional bare-URL linking."""

    rendered = html.escape(text)
    url_stash: list[str] = []
    if autolink:
        def stash_url(match: re.Match[str]) -> str:
            url_stash.append(_render_bare_url(match))
            return f"\x00U{len(url_stash) - 1}\x00"

        rendered = _URL_PATTERN.sub(stash_url, rendered)
    rendered = _BOLD.sub(r"<strong>\1</strong>", rendered)
    rendered = _ITALIC.sub(r"<em>\1</em>", rendered)
    for index, url_html in enumerate(url_stash):
        rendered = rendered.replace(f"\x00U{index}\x00", url_html)
    return rendered


_URL_PATTERN = re.compile(r"https?://[^\s*]+")
_ENTITY_TAIL = re.compile(r"&(?:[A-Za-z]+|#\d+|#x[0-9A-Fa-f]+)$")


def _render_bare_url(match: re.Match[str]) -> str:
    """Render one bare HTTP(S) URL matched in already-escaped text."""

    url = match.group(0)
    trailing = ""
    while url and url[-1] in ".,;:!?":
        trailing = url[-1] + trailing
        url = url[:-1]
    while url.endswith(")") and url.count("(") < url.count(")"):
        trailing = ")" + trailing
        url = url[:-1]
    if trailing.startswith(";") and _ENTITY_TAIL.search(url):
        url += ";"
        trailing = trailing[1:]
    if not url:
        return match.group(0)
    return (
        f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>'
        f"{trailing}"
    )


def _is_safe_link(destination: str) -> bool:
    """Return whether a Markdown link target is safe to place in ``href``."""

    if not destination or any(ord(ch) < 32 for ch in destination):
        return False
    scheme = urlsplit(destination).scheme.lower()
    return not scheme or scheme in {"http", "https", "mailto"}
