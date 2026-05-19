"""Pure helpers used across the rendering pipeline."""

from __future__ import annotations

import html
import os
from pathlib import Path

from .config import BuildConfig
from .discovery import is_package
from .models import ModuleDoc


def escape(value: object) -> str:
    """HTML-escape a value for text and attribute contexts."""

    return html.escape(str(value), quote=True)


def rel_link(from_path: Path, to_path: Path) -> str:
    """Return a POSIX relative link between two documentation files."""

    start = from_path.parent if from_path.suffix else from_path
    return Path(os.path.relpath(to_path, start=start)).as_posix()


def anchor(value: str) -> str:
    """Return a stable HTML anchor id for an API object."""

    return "api-" + "".join(ch if ch.isalnum() else "-" for ch in value).strip("-").lower()


def summary(docstring: str) -> str:
    """Return the first sentence or line from a docstring."""

    stripped = " ".join(docstring.split())
    if not stripped:
        return "No module docstring."
    sentence, _, _ = stripped.partition(". ")
    return sentence + ("." if not sentence.endswith(".") else "")


def card(href: str, title: str, detail: str = "") -> str:
    """Render a fully-clickable module-list card with a title and optional detail."""

    detail_html = f'<span class="card-detail">{escape(detail)}</span>' if detail else ""
    return (
        f'<li class="card"><a href="{escape(href)}">'
        f'<span class="card-title">{escape(title)}</span>{detail_html}'
        '</a></li>'
    )


def inline_code(text: str) -> str:
    """Render double-backtick inline code spans in already-escaped text."""

    parts = text.split("``")
    if len(parts) == 1:
        return text
    rendered: list[str] = []
    for index, part in enumerate(parts):
        if index % 2:
            rendered.append(f"<code>{part}</code>")
        else:
            rendered.append(part)
    return "".join(rendered)


def directory_index_path(config: BuildConfig, directory: Path) -> Path:
    """Return the generated API index path for a source directory."""

    return config.api_dir / directory / "index.html"


def all_directories(modules: list[ModuleDoc]) -> set[Path]:
    """Return every source directory that needs a directory index page."""

    dirs: set[Path] = set()
    for module in modules:
        current = module.source_rel.parent
        while current != Path("."):
            dirs.add(current)
            current = current.parent
    return dirs


def main_entries(config: BuildConfig) -> list[Path]:
    """Return the project-rel directories that represent the main packages.

    If ``main_root`` is itself a package, the single returned entry is the
    main package. If ``main_root`` is a wrapper (no ``__init__.py`` at its
    root, e.g. ``src/``), its immediate child packages are returned instead.
    """

    if is_package(config.main_root):
        return [config.main_root.relative_to(config.project_root)]
    return [
        (config.main_root / child.name).relative_to(config.project_root)
        for child in sorted(config.main_root.iterdir())
        if child.is_dir() and is_package(child)
    ]


def supplemental_entries(config: BuildConfig) -> list[Path]:
    """Return project-rel directories rendered as supplemental material."""

    return [root.relative_to(config.project_root) for root in config.supplemental_roots]


def extra_file_modules(config: BuildConfig, modules: list[ModuleDoc]) -> list[ModuleDoc]:
    """Return the parsed ``ModuleDoc`` objects for configured rogue files."""

    extra = {path.resolve() for path in config.extra_files}
    return [module for module in modules if module.source_path.resolve() in extra]


def module_count(modules: list[ModuleDoc], directory: Path) -> int:
    """Count modules contained recursively under a source directory."""

    directory_parts = directory.parts
    return sum(
        module.source_rel.parts[: len(directory_parts)] == directory_parts
        for module in modules
    )


def find_init_module(directory: Path, modules: list[ModuleDoc]) -> ModuleDoc | None:
    """Return the ``__init__.py`` module under ``directory`` if it exists."""

    for module in modules:
        if module.source_rel.parent == directory and module.source_rel.name == "__init__.py":
            return module
    return None
