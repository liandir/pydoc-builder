"""Pure helpers used across the rendering pipeline."""

from __future__ import annotations

import html
import os
import re
from collections.abc import Callable
from pathlib import Path

from .config import BuildConfig
from .discovery import is_package
from .models import ModuleDoc


def escape(value: object) -> str:
    """HTML-escape a value for text and attribute contexts.

    Args:
        value: Any value; converted to ``str`` before escaping.

    Returns:
        The escaped string, safe to interpolate into either text or
        double-quoted attribute contexts.
    """

    return html.escape(str(value), quote=True)


def rel_link(from_path: Path, to_path: Path) -> str:
    """Return a POSIX relative link between two documentation files.

    Args:
        from_path: The page the link is rendered on (its directory is the
            link's reference point).
        to_path: The target the link should resolve to.

    Returns:
        A POSIX-style relative path suitable for use in an ``href``.
    """

    start = from_path.parent if from_path.suffix else from_path
    return Path(os.path.relpath(to_path, start=start)).as_posix()


def anchor(value: str) -> str:
    """Return a stable HTML anchor id for an API object.

    Args:
        value: Qualified name (or any identifier) to slugify into an anchor.

    Returns:
        A lowercase, hyphenated anchor id prefixed with ``api-``.
    """

    return "api-" + "".join(ch if ch.isalnum() else "-" for ch in value).strip("-").lower()


def summary(docstring: str) -> str:
    """Return the first sentence or line from a docstring.

    Args:
        docstring: Raw docstring text. Empty input yields a placeholder.

    Returns:
        The first sentence terminated with a period, or a placeholder string
        when ``docstring`` is empty.
    """

    stripped = " ".join(docstring.split())
    if not stripped:
        return "No module docstring."
    sentence, _, _ = stripped.partition(". ")
    return sentence + ("." if not sentence.endswith(".") else "")


def card(href: str, title: str, detail: str = "") -> str:
    """Render a fully-clickable module-list card with a title and optional detail.

    Args:
        href: Destination URL for the card link.
        title: Main label shown in the card.
        detail: Optional secondary text shown beneath the title.

    Returns:
        An ``<li class="card">`` HTML fragment.
    """

    detail_html = f'<span class="card-detail">{escape(detail)}</span>' if detail else ""
    return (
        f'<li class="card"><a href="{escape(href)}">'
        f'<span class="card-title">{escape(title)}</span>{detail_html}'
        '</a></li>'
    )


def inline_markup(
    text: str,
    resolver: Callable[[str], str | None] | None = None,
) -> str:
    """Render inline code spans, autolinked URLs and symbol xrefs.

    Both ````double```` and ```single``` backtick runs become
    ``<code>`` spans; double-backticks are processed first so a stray
    backtick inside them is preserved as a literal.

    Args:
        text: HTML-escaped text containing optional backtick code runs and
            bare ``http(s)://`` URLs.
        resolver: Optional callback that turns a backticked token into an
            href (e.g. ``#api-foo`` or ``../other.html#api-bar``). Tokens
            that resolve are wrapped in ``<a class="api-xref">``.

    Returns:
        The rendered HTML string.
    """

    parts = text.split("``")
    rendered: list[str] = []
    for index, part in enumerate(parts):
        if index % 2:
            rendered.append(_code_span(part, resolver))
        else:
            rendered.append(_process_outside(part, resolver))
    return "".join(rendered)


_SINGLE_BACKTICK = re.compile(r"`([^`]+)`")


def _process_outside(text: str, resolver: Callable[[str], str | None] | None) -> str:
    """Render single-backtick code spans and autolink URLs in the rest."""

    pieces: list[str] = []
    cursor = 0
    for match in _SINGLE_BACKTICK.finditer(text):
        pieces.append(_autolink_urls(text[cursor:match.start()]))
        pieces.append(_code_span(match.group(1), resolver))
        cursor = match.end()
    pieces.append(_autolink_urls(text[cursor:]))
    return "".join(pieces)


def _code_span(content: str, resolver: Callable[[str], str | None] | None) -> str:
    """Wrap ``content`` in ``<code>`` (and an xref ``<a>`` when ``resolver`` matches)."""

    href = resolver(content) if resolver else None
    if href:
        return f'<a class="api-xref" href="{escape(href)}"><code>{content}</code></a>'
    return f"<code>{content}</code>"


_URL_PATTERN = re.compile(r"https?://\S+")
_ENTITY_TAIL = re.compile(r"&(?:[A-Za-z]+|#\d+|#x[0-9A-Fa-f]+)$")


def _autolink_urls(text: str) -> str:
    """Wrap bare ``http(s)://`` URLs in escaped text with anchor tags."""

    def link(match: re.Match[str]) -> str:
        url = match.group(0)
        trailing = ""
        while url and url[-1] in ".,;:!?":
            trailing = url[-1] + trailing
            url = url[:-1]
        while url.endswith(")") and url.count("(") < url.count(")"):
            trailing = ")" + trailing
            url = url[:-1]
        # A stripped ';' may have closed an HTML entity inside the URL.
        if trailing.startswith(";") and _ENTITY_TAIL.search(url):
            url += ";"
            trailing = trailing[1:]
        if not url:
            return match.group(0)
        return (
            f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>'
            f"{trailing}"
        )

    return _URL_PATTERN.sub(link, text)


def directory_index_path(config: BuildConfig, directory: Path) -> Path:
    """Return the generated API index path for a source directory.

    Args:
        config: Build configuration providing the API output root.
        directory: Project-relative source directory.

    Returns:
        The absolute path of the directory's ``index.html``.
    """

    return config.api_dir / directory / "index.html"


def all_directories(modules: list[ModuleDoc]) -> set[Path]:
    """Return every source directory that needs a directory index page.

    Args:
        modules: All parsed modules; each parent directory up to the project
            root contributes to the result.

    Returns:
        A set of project-relative directory paths.
    """

    dirs: set[Path] = set()
    for module in modules:
        current = module.source_rel.parent
        while current != Path("."):
            dirs.add(current)
            current = current.parent
    return dirs


def main_package_dir(config: BuildConfig) -> Path:
    """Return the project-rel directory that holds the main modules.

    If ``main_root`` is itself a package, that is the main package directory.
    If ``main_root`` is a wrapper (e.g. ``src/``) containing a single child
    package, that child is the main package directory. Otherwise falls back
    to ``main_root`` itself.

    Args:
        config: Build configuration whose ``main_root`` is resolved.

    Returns:
        The project-relative path of the main package directory.
    """

    if is_package(config.main_root):
        return config.main_root.relative_to(config.project_root)
    packages = [
        (config.main_root / child.name).relative_to(config.project_root)
        for child in sorted(config.main_root.iterdir())
        if child.is_dir() and is_package(child)
    ]
    if len(packages) == 1:
        return packages[0]
    return config.main_root.relative_to(config.project_root)


def supplemental_entries(config: BuildConfig) -> list[Path]:
    """Return project-rel directories rendered as supplemental material.

    Args:
        config: Build configuration providing ``supplemental_roots``.

    Returns:
        The supplemental roots as project-relative paths.
    """

    return [root.relative_to(config.project_root) for root in config.supplemental_roots]


def extra_file_modules(config: BuildConfig, modules: list[ModuleDoc]) -> list[ModuleDoc]:
    """Return the parsed ``ModuleDoc`` objects for configured rogue files.

    Args:
        config: Build configuration listing the rogue ``extra_files``.
        modules: All parsed modules to filter against the rogue file set.

    Returns:
        The subset of ``modules`` whose source paths match ``extra_files``.
    """

    extra = {path.resolve() for path in config.extra_files}
    return [module for module in modules if module.source_path.resolve() in extra]


def module_count(modules: list[ModuleDoc], directory: Path) -> int:
    """Count modules contained recursively under a source directory.

    Args:
        modules: All parsed modules to check for descendants.
        directory: Project-relative directory whose subtree is counted.

    Returns:
        The number of modules whose source path lies under ``directory``.
    """

    directory_parts = directory.parts
    return sum(
        module.source_rel.parts[: len(directory_parts)] == directory_parts
        for module in modules
    )


def find_init_module(directory: Path, modules: list[ModuleDoc]) -> ModuleDoc | None:
    """Return the ``__init__.py`` module under ``directory`` if it exists.

    Args:
        directory: Project-relative directory to look in.
        modules: All parsed modules to search.

    Returns:
        The matching ``__init__.py`` module, or ``None`` if the directory
        has no ``__init__.py``.
    """

    for module in modules:
        if module.source_rel.parent == directory and module.source_rel.name == "__init__.py":
            return module
    return None
