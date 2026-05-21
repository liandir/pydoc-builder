"""Write the documentation pages: home, directory indexes, and per-module pages."""

from __future__ import annotations

import shutil

from .config import BuildConfig
from .docstrings import doc_block
from .layout import page
from .markdown import render_markdown
from .models import ModuleDoc
from .navigation import sidebar
from .rendering import class_index, heading_with_source, render_object, xref_resolver
from .utils import (
    all_directories,
    card,
    directory_index_path,
    escape,
    extra_file_modules,
    find_init_module,
    main_package_dir,
    module_count,
    rel_link,
    summary,
    supplemental_entries,
)


def prepare_docs_dir(config: BuildConfig) -> None:
    """Create a clean API output directory while preserving hand-written docs.

    Args:
        config: Build configuration whose ``api_dir`` should be reset.
    """

    api_dir = config.api_dir
    if api_dir.exists():
        shutil.rmtree(api_dir)
    api_dir.mkdir(parents=True, exist_ok=True)


def write_site_index(config: BuildConfig, modules: list[ModuleDoc]) -> None:
    """Write the project home page at ``docs/index.html``.

    The home shows a project title, a single card linking to the main package
    documentation, and a Supplemental Material section with cards for each
    supplemental directory and rogue file.

    Args:
        config: Build configuration providing project metadata and paths.
        modules: All parsed modules used to populate the home page links.
    """

    site_index = config.docs_dir / "index.html"
    main_dir = main_package_dir(config)
    main_card = card(
        rel_link(site_index, directory_index_path(config, main_dir)),
        f"{main_dir.name}/",
        f"{module_count(modules, main_dir)} modules",
    )

    supp_cards = [
        card(
            rel_link(site_index, directory_index_path(config, directory)),
            f"{directory.as_posix()}/",
            f"{module_count(modules, directory)} modules",
        )
        for directory in supplemental_entries(config)
    ] + [
        card(
            rel_link(site_index, module.page_path),
            module.source_rel.name,
            summary(module.docstring),
        )
        for module in extra_file_modules(config, modules)
    ]
    supp_section = ""
    if supp_cards:
        supp_section = f"""
      <section>
        <h2>Supplemental Material</h2>
        <ul class="module-list detailed">{"".join(supp_cards)}</ul>
      </section>
        """

    title = config.project_root.name
    readme_section = _readme_section(config)
    hero = "" if readme_section else f'<div class="home-hero"><h1>{escape(title)}</h1></div>'
    body = f"""
    {sidebar(config, site_index, modules, current_rel=main_dir, is_module_page=False, mark_current=False)}
    <main class="content">
      {hero}
      {readme_section}
      <section>
        <h2>Main Package Documentation</h2>
        <ul class="module-list detailed">{main_card}</ul>
      </section>
      {supp_section}
    </main>
    """
    site_index.write_text(page(title, body, layout="split", default_theme=config.default_theme), encoding="utf-8")


def _readme_section(config: BuildConfig) -> str:
    """Render the project's README as an HTML section if one is present."""

    for name in ("README.md", "readme.md", "Readme.md"):
        path = config.project_root / name
        if path.is_file():
            return f'<section class="readme">{render_markdown(path.read_text(encoding="utf-8"))}</section>'
    return ""


def write_directory_pages(config: BuildConfig, modules: list[ModuleDoc]) -> None:
    """Write directory index pages for every documented source directory.

    Directories above the main package (e.g. a ``src/`` wrapper) are skipped
    since they aren't reachable from the sidebar navigation tree.

    Args:
        config: Build configuration providing the docs output directory.
        modules: All parsed modules; their parents define the directories that
            receive an index page.
    """

    dirs = all_directories(modules)
    valid_roots = [main_package_dir(config), *supplemental_entries(config)]
    for directory in dirs:
        if not any(_is_under(directory, root) for root in valid_roots):
            continue
        _write_directory_page(config, directory, modules, dirs)


def write_module_pages(config: BuildConfig, modules: list[ModuleDoc]) -> None:
    """Write one API page per parsed module, excluding ``__init__.py`` files.

    ``__init__.py`` content lives on the containing directory's package page.

    Args:
        config: Build configuration providing the docs output directory.
        modules: All parsed modules; each non-``__init__`` module yields one
            API page.
    """

    classes = class_index(modules)
    for module in modules:
        if module.source_rel.name == "__init__.py":
            continue
        _write_module_page(config, module, modules, classes)


def _is_under(path, ancestor) -> bool:
    """Return whether ``path`` equals ``ancestor`` or is a descendant of it."""

    return path.parts[: len(ancestor.parts)] == ancestor.parts


def _write_directory_page(
    config: BuildConfig,
    directory,
    modules: list[ModuleDoc],
    dirs: set,
) -> None:
    """Write a directory index. When ``__init__.py`` is present, render its content."""

    init_module = find_init_module(directory, modules)

    child_dirs = sorted(
        child for child in dirs if child.parent == directory and child != directory
    )
    child_modules = sorted(
        (
            module
            for module in modules
            if module.source_rel.parent == directory
            and module.source_rel.name != "__init__.py"
        ),
        key=lambda module: module.source_rel.name,
    )
    current_path = directory_index_path(config, directory)

    child_dir_links = "\n".join(
        card(
            rel_link(current_path, directory_index_path(config, child)),
            f"{child.name}/",
            f"{module_count(modules, child)} modules",
        )
        for child in child_dirs
    )
    module_links = "\n".join(
        card(
            rel_link(current_path, module.page_path),
            module.source_rel.name,
            summary(module.docstring),
        )
        for module in child_modules
    )
    eyebrow = f"{directory.as_posix()}/"
    if init_module is not None:
        classes = class_index(modules)
        resolver = xref_resolver(init_module, modules)
        heading_label = init_module.module_name
        heading_html = heading_with_source(
            f"<h1>{escape(heading_label)}</h1>",
            init_module.full_source,
        )
        init_docs = doc_block(init_module.docstring, resolver)
        init_objects = "\n".join(
            render_object(obj, init_module, classes, resolver, config.autofill_types) for obj in init_module.objects
        )
        toc_objects = init_module.objects
    else:
        heading_html = f"<h1>{escape(directory.as_posix())}/</h1>"
        init_docs = ""
        init_objects = ""
        toc_objects = None

    body = f"""
    {sidebar(config, current_path, modules, current_rel=directory, is_module_page=False, toc_objects=toc_objects)}
    <main class="content">
      <p class="eyebrow">{escape(eyebrow)}</p>
      {heading_html}
      {init_docs}
      {init_objects}
      <section class="directory-section">
        <h2>Subpackages</h2>
        <ul class="module-list detailed">{child_dir_links or '<li><span>None.</span></li>'}</ul>
      </section>
      <section class="directory-section">
        <h2>Modules</h2>
        <ul class="module-list detailed">{module_links or '<li><span>None.</span></li>'}</ul>
      </section>
    </main>
    """
    current_path.parent.mkdir(parents=True, exist_ok=True)
    title = init_module.module_name if init_module is not None else f"{directory.as_posix()}/"
    current_path.write_text(page(title, body, layout="split", default_theme=config.default_theme), encoding="utf-8")


def _write_module_page(
    config: BuildConfig,
    module: ModuleDoc,
    modules: list[ModuleDoc],
    classes: dict,
) -> None:
    """Write one module API page."""

    module.page_path.parent.mkdir(parents=True, exist_ok=True)
    resolver = xref_resolver(module, modules)
    objects = "\n".join(render_object(obj, module, classes, resolver, config.autofill_types) for obj in module.objects)
    body = f"""
    {sidebar(config, module.page_path, modules, current_rel=module.source_rel, is_module_page=True, toc_objects=module.objects)}
    <main class="content">
      <p class="eyebrow">{escape(module.source_rel.as_posix())}</p>
      <h1>{escape(module.module_name)}</h1>
      {doc_block(module.docstring, resolver)}
      {objects or '<p class="muted">No public classes or functions found.</p>'}
    </main>
    """
    module.page_path.write_text(page(module.module_name, body, layout="split", default_theme=config.default_theme), encoding="utf-8")
