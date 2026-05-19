"""Sidebars, tables of contents, and source-tree navigation."""

from __future__ import annotations

from pathlib import Path

from .config import BuildConfig
from .models import ApiObject, ModuleDoc
from .utils import (
    directory_index_path,
    escape,
    extra_file_modules,
    main_entries,
    rel_link,
    supplemental_entries,
)


def global_sidebar(
    config: BuildConfig,
    page_path: Path,
    modules: list[ModuleDoc],
    *,
    current_directory: Path | None = None,
) -> str:
    """Render the navigation sidebar used by non-module pages."""

    package_links = "".join(
        f'<li><a href="{rel_link(page_path, directory_index_path(config, directory))}">'
        f'{escape(directory.name)}</a></li>'
        for directory in main_entries(config)
    )
    supplemental_dir_links = "".join(
        f'<li><a href="{rel_link(page_path, directory_index_path(config, directory))}">'
        f'{escape(directory.as_posix())}/</a></li>'
        for directory in supplemental_entries(config)
    )
    supplemental_file_links = "".join(
        f'<li><a href="{rel_link(page_path, module.page_path)}">'
        f'{escape(module.source_rel.name)}</a></li>'
        for module in extra_file_modules(config, modules)
    )
    supplemental_html = ""
    if supplemental_dir_links or supplemental_file_links:
        supplemental_html = f"""
      <div class="side-section">
        <h2>Supplemental</h2>
        <ul class="toc-list">{supplemental_dir_links}{supplemental_file_links}</ul>
      </div>
        """
    current = ""
    if current_directory is not None:
        current = f"""
      <div class="side-section">
        <h2>Current Branch</h2>
        {_directory_sidebar_tree(config, page_path, current_directory)}
      </div>
        """
    return f"""
    <nav class="side">
      <div class="side-section">
        <a class="back" href="{rel_link(page_path, config.docs_dir / 'index.html')}">Project Home</a>
      </div>
      <div class="side-section">
        <h2>Packages</h2>
        <ul class="toc-list">{package_links or '<li><span class="muted">No packages.</span></li>'}</ul>
      </div>
      {supplemental_html}
      {current}
    </nav>
    """


def module_sidebar(config: BuildConfig, module: ModuleDoc, modules: list[ModuleDoc]) -> str:
    """Render navigation and table of contents for a module page."""

    return f"""
    <nav class="side">
      <div class="side-section">
        <a class="back" href="{rel_link(module.page_path, config.docs_dir / 'index.html')}">Project Home</a>
      </div>
      <div class="side-section">
        <h2>Source</h2>
        {_source_tree(config, module, modules)}
      </div>
      <div class="side-section">
        <h2>On This Page</h2>
        {_module_toc(module.objects)}
      </div>
    </nav>
    """


def package_sidebar(
    config: BuildConfig,
    page_path: Path,
    directory: Path,
    init_module: ModuleDoc | None,
    modules: list[ModuleDoc],
) -> str:
    """Render the sidebar used by package pages.

    Identical to :func:`global_sidebar` but adds an "On This Page" section
    listing the ``__init__.py`` API objects when present.
    """

    base = global_sidebar(config, page_path, modules, current_directory=directory)
    if init_module is None or not init_module.objects:
        return base
    toc = f"""
      <div class="side-section">
        <h2>On This Page</h2>
        {_module_toc(init_module.objects)}
      </div>
    """
    return base.replace("</nav>", f"{toc}</nav>", 1)


def _directory_sidebar_tree(config: BuildConfig, page_path: Path, directory: Path) -> str:
    """Render parent-directory links for a directory page."""

    items: list[str] = []
    current = Path(directory.parts[0])
    while current != Path("."):
        label = f"{current.as_posix()}/"
        if current == directory:
            items.append(f'<li><span class="current-source">{escape(label)}</span></li>')
            break
        items.append(
            f'<li><a href="{rel_link(page_path, directory_index_path(config, current))}">{escape(label)}</a></li>'
        )
        child_index = len(current.parts)
        if child_index >= len(directory.parts):
            break
        current = current / directory.parts[child_index]
    return f'<ul class="source-tree">{"".join(items)}</ul>'


def _source_tree(config: BuildConfig, module: ModuleDoc, modules: list[ModuleDoc]) -> str:
    """Render source path navigation for the current module."""

    items: list[str] = []
    current = Path(module.source_rel.parts[0])
    while current != module.source_rel.parent and current != Path("."):
        items.append(
            f'<li><a href="{rel_link(module.page_path, directory_index_path(config, current))}">'
            f'{escape(current.as_posix())}/</a></li>'
        )
        child_index = len(current.parts)
        if child_index >= len(module.source_rel.parts) - 1:
            break
        current = current / module.source_rel.parts[child_index]
    if module.source_rel.parent != Path("."):
        items.append(
            f'<li><a href="{rel_link(module.page_path, directory_index_path(config, module.source_rel.parent))}">'
            f'{escape(module.source_rel.parent.as_posix())}/</a></li>'
        )
    siblings = sorted(
        (
            other
            for other in modules
            if other.source_rel.parent == module.source_rel.parent
            and other.source_rel.name != "__init__.py"
        ),
        key=lambda other: other.source_rel.name,
    )
    sibling_items = []
    for sibling in siblings:
        if sibling.source_rel == module.source_rel:
            sibling_items.append(f'<li><span class="current-source">{escape(sibling.source_rel.name)}</span></li>')
        else:
            sibling_items.append(
                f'<li><a href="{rel_link(module.page_path, sibling.page_path)}">'
                f'{escape(sibling.source_rel.name)}</a></li>'
            )
    if sibling_items:
        items.append(f'<li><ul class="source-siblings">{"".join(sibling_items)}</ul></li>')
    return f'<ul class="source-tree">{"".join(items)}</ul>'


def _module_toc(objects: list[ApiObject]) -> str:
    """Render a module table of contents with classes, functions, and methods."""

    if not objects:
        return '<p class="muted">No public objects.</p>'
    return f'<ul class="toc-list">{"".join(_toc_item(obj) for obj in objects)}</ul>'


def _toc_item(obj: ApiObject) -> str:
    """Render one table-of-contents item."""

    children = f'<ul>{"".join(_toc_item(child) for child in obj.children)}</ul>' if obj.children else ""
    return (
        '<li>'
        f'<a href="#{escape(obj.anchor)}"><span class="toc-kind">{escape(obj.kind)}</span>'
        f'<span class="toc-name">{escape(obj.name)}</span></a>'
        f'{children}'
        '</li>'
    )
