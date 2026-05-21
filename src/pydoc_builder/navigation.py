"""Unified sidebar: project home, main package tree, supplemental, and on-page TOC."""

from __future__ import annotations

from pathlib import Path

from .config import BuildConfig
from .models import ApiObject, ModuleDoc
from .utils import (
    directory_index_path,
    escape,
    extra_file_modules,
    main_package_dir,
    rel_link,
    supplemental_entries,
)


def sidebar(
    config: BuildConfig,
    page_path: Path,
    modules: list[ModuleDoc],
    *,
    current_rel: Path | None = None,
    is_module_page: bool = False,
    mark_current: bool = True,
    toc_objects: list[ApiObject] | None = None,
) -> str:
    """Render the navigation sidebar shared by every documentation page.

    Args:
        config: Build configuration.
        page_path: Output path of the page being rendered.
        modules: All parsed modules.
        current_rel: Source-relative path of the current page (a module path or a
            directory). ``None`` for pages that aren't tied to a source location.
        is_module_page: True when rendering a single-module API page.
        mark_current: Whether the entry that matches ``current_rel`` should be
            rendered as a non-link "current" marker. The home page passes
            ``False`` so the tree expands without marking anything.
        toc_objects: Optional API objects rendered as "On This Page".
    """

    home_path = config.docs_dir / "index.html"
    project_home = (
        f'<a class="back" href="{rel_link(page_path, home_path)}">Project Home</a>'
    )
    main_dir = main_package_dir(config)
    main_tree = _section_tree(
        config, page_path, modules,
        section_root=main_dir,
        current_rel=current_rel,
        is_module_page=is_module_page,
        mark_current=mark_current,
        heading="Main Package Documentation",
    )
    supplemental_html = _supplemental_section(
        config, page_path, modules,
        current_rel=current_rel,
        is_module_page=is_module_page,
        mark_current=mark_current,
    )
    toc_html = _toc_section(toc_objects) if toc_objects else ""
    return f"""
    <nav class="side">
      <div class="side-section">{project_home}</div>
      {main_tree}
      {supplemental_html}
      {toc_html}
    </nav>
    """


def _section_tree(
    config: BuildConfig,
    page_path: Path,
    modules: list[ModuleDoc],
    *,
    section_root: Path,
    current_rel: Path | None,
    is_module_page: bool,
    mark_current: bool,
    heading: str,
) -> str:
    """Render a heading + tree rooted at ``section_root``.

    Expands along the path to the current page when the current page lies
    inside ``section_root``; otherwise renders just a link to the root.
    """

    target_dir = _target_dir(current_rel, is_module_page)
    in_section = target_dir is not None and _is_under(target_dir, section_root)
    if in_section:
        node_html = _render_node(
            config, page_path, modules,
            node=section_root,
            expand_to=target_dir,
            current_rel=current_rel,
            is_module_page=is_module_page,
            mark_current=mark_current,
        )
        tree_html = f'<ul class="source-tree"><li>{node_html}</li></ul>'
    else:
        tree_html = (
            f'<ul class="source-tree">'
            f'<li>{_dir_link(config, page_path, section_root)}</li>'
            f'</ul>'
        )
    return f"""
      <div class="side-section">
        <h2>{escape(heading)}</h2>
        {tree_html}
      </div>
    """


def _supplemental_section(
    config: BuildConfig,
    page_path: Path,
    modules: list[ModuleDoc],
    *,
    current_rel: Path | None,
    is_module_page: bool,
    mark_current: bool,
) -> str:
    """Render the Supplemental Material section: one entry per supp dir/rogue file."""

    target_dir = _target_dir(current_rel, is_module_page)
    entries: list[str] = []
    for supp_dir in supplemental_entries(config):
        if target_dir is not None and _is_under(target_dir, supp_dir):
            node_html = _render_node(
                config, page_path, modules,
                node=supp_dir,
                expand_to=target_dir,
                current_rel=current_rel,
                is_module_page=is_module_page,
                mark_current=mark_current,
            )
            entries.append(f'<ul class="source-tree"><li>{node_html}</li></ul>')
        else:
            entries.append(
                f'<ul class="source-tree">'
                f'<li>{_dir_link(config, page_path, supp_dir)}</li>'
                f'</ul>'
            )

    rogue = extra_file_modules(config, modules)
    if rogue:
        items: list[str] = []
        for module in rogue:
            if mark_current and current_rel == module.source_rel:
                items.append(
                    f'<li>{_py_icon()}<span class="current-source">{escape(module.source_rel.name)}</span></li>'
                )
            else:
                items.append(
                    f'<li>{_py_icon()}<a href="{rel_link(page_path, module.page_path)}">'
                    f'{escape(module.source_rel.name)}</a></li>'
                )
        entries.append(f'<ul class="source-tree">{"".join(items)}</ul>')

    if not entries:
        return ""
    return f"""
      <div class="side-section">
        <h2>Supplemental Material</h2>
        {"".join(entries)}
      </div>
    """


def _render_node(
    config: BuildConfig,
    page_path: Path,
    modules: list[ModuleDoc],
    *,
    node: Path,
    expand_to: Path,
    current_rel: Path | None,
    is_module_page: bool,
    mark_current: bool,
) -> str:
    """Render one tree node (label plus, when on the path to ``expand_to``, its children)."""

    is_target = node == expand_to
    is_current_page = (
        mark_current and is_target and not is_module_page and current_rel == node
    )
    label = f"{node.name}/"
    if is_current_page:
        label_html = f'<span class="current-source">{escape(label)}</span>'
    else:
        label_html = (
            f'<a href="{rel_link(page_path, directory_index_path(config, node))}">'
            f'{escape(label)}</a>'
        )

    if not _is_under(expand_to, node):
        return label_html

    children_html = _render_children(
        config, page_path, modules,
        node=node,
        expand_to=expand_to,
        current_rel=current_rel,
        is_module_page=is_module_page,
        mark_current=mark_current,
    )
    return f"{label_html}{children_html}"


def _render_children(
    config: BuildConfig,
    page_path: Path,
    modules: list[ModuleDoc],
    *,
    node: Path,
    expand_to: Path,
    current_rel: Path | None,
    is_module_page: bool,
    mark_current: bool,
) -> str:
    """Render the subdirs + module files inside ``node`` as a nested ``<ul>``."""

    depth = len(node.parts)
    child_dirs: set[Path] = set()
    for module in modules:
        parts = module.source_rel.parts
        if parts[:depth] == node.parts and len(parts) > depth + 1:
            child_dirs.add(Path(*parts[: depth + 1]))

    items: list[str] = []
    for child_dir in sorted(child_dirs):
        items.append(
            "<li>"
            + _render_node(
                config, page_path, modules,
                node=child_dir,
                expand_to=expand_to,
                current_rel=current_rel,
                is_module_page=is_module_page,
                mark_current=mark_current,
            )
            + "</li>"
        )

    child_modules = sorted(
        (
            module
            for module in modules
            if module.source_rel.parent == node
            and module.source_rel.name != "__init__.py"
        ),
        key=lambda module: module.source_rel.name,
    )
    for module in child_modules:
        if mark_current and is_module_page and module.source_rel == current_rel:
            items.append(
                f'<li>{_py_icon()}<span class="current-source">{escape(module.source_rel.name)}</span></li>'
            )
        else:
            items.append(
                f'<li>{_py_icon()}<a href="{rel_link(page_path, module.page_path)}">'
                f'{escape(module.source_rel.name)}</a></li>'
            )

    if not items:
        return ""
    return f'<ul>{"".join(items)}</ul>'


def _toc_section(objects: list[ApiObject]) -> str:
    """Render the On-This-Page table-of-contents section."""

    return f"""
      <div class="side-section">
        <h2>On This Page</h2>
        <ul class="toc-list">{"".join(_toc_item(obj) for obj in objects)}</ul>
      </div>
    """


def _toc_item(obj: ApiObject) -> str:
    """Render one table-of-contents item."""

    children = (
        f'<ul>{"".join(_toc_item(child) for child in obj.children)}</ul>'
        if obj.children
        else ""
    )
    return (
        '<li>'
        f'<a href="#{escape(obj.anchor)}"><span class="toc-kind">{escape(obj.kind)}</span>'
        f'<span class="toc-name">{escape(obj.name)}</span></a>'
        f'{children}'
        '</li>'
    )


def _target_dir(current_rel: Path | None, is_module_page: bool) -> Path | None:
    """Return the directory the breadcrumb should expand toward."""

    if current_rel is None:
        return None
    return current_rel.parent if is_module_page else current_rel


def _is_under(path: Path, ancestor: Path) -> bool:
    """Return whether ``path`` equals ``ancestor`` or is a descendant of it."""

    return path.parts[: len(ancestor.parts)] == ancestor.parts


def _py_icon() -> str:
    """Inline SVG of the Python logo, sized to sit inline before a file name."""

    return (
        '<svg class="py-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 255" '
        'aria-hidden="true">'
        '<defs>'
        '<linearGradient id="pyA" x1="12.959%" y1="12.039%" x2="79.639%" y2="78.201%">'
        '<stop offset="0%" stop-color="#387EB8"/><stop offset="100%" stop-color="#366994"/>'
        '</linearGradient>'
        '<linearGradient id="pyB" x1="19.128%" y1="20.579%" x2="90.742%" y2="88.429%">'
        '<stop offset="0%" stop-color="#FFE052"/><stop offset="100%" stop-color="#FFC331"/>'
        '</linearGradient>'
        '</defs>'
        '<path fill="url(#pyA)" d="M126.916.072c-64.832 0-60.784 28.115-60.784 28.115l.072 29.128h61.868v8.745H41.631S.145 61.355.145 126.77c0 65.417 36.21 63.097 36.21 63.097h21.61v-30.358s-1.165-36.21 35.632-36.21h61.362s34.475.557 34.475-33.319V33.97S194.67.072 126.916.072zM92.802 19.66a11.12 11.12 0 0 1 11.13 11.13 11.12 11.12 0 0 1-11.13 11.13 11.12 11.12 0 0 1-11.13-11.13 11.12 11.12 0 0 1 11.13-11.13z"/>'
        '<path fill="url(#pyB)" d="M128.757 254.126c64.832 0 60.784-28.115 60.784-28.115l-.072-29.127H127.6v-8.745h86.441s41.486 4.705 41.486-60.71c0-65.416-36.21-63.096-36.21-63.096h-21.61v30.358s1.165 36.21-35.632 36.21h-61.362s-34.475-.557-34.475 33.319v56.012s-5.235 33.894 62.518 33.894zm34.114-19.586a11.12 11.12 0 0 1-11.13-11.13 11.12 11.12 0 0 1 11.13-11.131 11.12 11.12 0 0 1 11.13 11.13 11.12 11.12 0 0 1-11.13 11.13z"/>'
        '</svg>'
    )


def _dir_link(config: BuildConfig, page_path: Path, directory: Path) -> str:
    """Render a basename-labelled link to a directory page."""

    return (
        f'<a href="{rel_link(page_path, directory_index_path(config, directory))}">'
        f'{escape(directory.name)}/</a>'
    )
