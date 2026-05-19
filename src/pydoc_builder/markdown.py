"""Minimal markdown-to-HTML renderer for README files.

Supports a deliberate subset of CommonMark — ATX headings, paragraphs, fenced
code blocks, unordered and ordered lists, blockquotes, horizontal rules,
inline code, links, **bold** and *italic*. Anything outside this subset is
escaped and passed through as text, so output is always safe HTML.
"""

from __future__ import annotations

import html
import re


def render_markdown(text: str) -> str:
    """Render markdown ``text`` to an HTML fragment."""

    blocks = _parse_blocks(text.splitlines())
    return "\n".join(_render_block(block) for block in blocks)


def _parse_blocks(lines: list[str]) -> list[tuple]:
    """Group ``lines`` into a flat list of block tuples for rendering."""

    blocks: list[tuple] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            lang = line[3:].strip()
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not lines[i].startswith("```"):
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
        if re.match(r"^\s*\d+\.\s+", line):
            items, i = _collect_list(lines, i, r"^\s*\d+\.\s+(.+)$")
            blocks.append(("ol", items))
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


def _starts_block(line: str) -> bool:
    """Return whether ``line`` starts a non-paragraph block."""

    return (
        line.startswith("```")
        or bool(re.match(r"^#{1,6}\s+", line))
        or bool(re.match(r"^(\*{3,}|-{3,}|_{3,})\s*$", line))
        or line.startswith(">")
        or bool(re.match(r"^\s*[-*+]\s+", line))
        or bool(re.match(r"^\s*\d+\.\s+", line))
    )


def _render_block(block: tuple) -> str:
    """Render one parsed block tuple to HTML."""

    kind = block[0]
    if kind == "heading":
        level, text = block[1], block[2]
        return f"<h{level}>{_inline(text)}</h{level}>"
    if kind == "paragraph":
        return f"<p>{_inline(block[1])}</p>"
    if kind == "code":
        lang, code = block[1], block[2]
        cls = f' class="language-{html.escape(lang)}"' if lang else ""
        return f"<pre><code{cls}>{html.escape(code)}</code></pre>"
    if kind == "hr":
        return "<hr>"
    if kind == "blockquote":
        return f"<blockquote>{_inline(block[1])}</blockquote>"
    if kind in ("ul", "ol"):
        items = "".join(f"<li>{_inline(item)}</li>" for item in block[1])
        return f"<{kind}>{items}</{kind}>"
    return ""


_CODE = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BOLD = re.compile(r"\*\*([^*]+?)\*\*")
_ITALIC = re.compile(r"(?<![\*\w])\*([^*\s][^*]*?)\*(?![\*\w])")


def _inline(text: str) -> str:
    """Apply inline transforms (code, links, bold, italic) to a text run."""

    stash: list[str] = []

    def stash_code(match: re.Match[str]) -> str:
        stash.append(html.escape(match.group(1)))
        return f"\x00{len(stash) - 1}\x00"

    text = _CODE.sub(stash_code, text)
    text = html.escape(text)
    text = _LINK.sub(
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>',
        text,
    )
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)
    for i, code in enumerate(stash):
        text = text.replace(f"\x00{i}\x00", f"<code>{code}</code>", 1)
    return text
