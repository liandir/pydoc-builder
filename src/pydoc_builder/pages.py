"""Write the top-level pages: site index, API index, directories, modules."""

from __future__ import annotations

import shutil
from pathlib import Path

from .config import BuildConfig
from .docstrings import doc_block
from .layout import page
from .models import ModuleDoc
from .navigation import global_sidebar, module_sidebar, package_sidebar
from .rendering import class_index, package_source_dropdown, render_object
from .utils import (
    all_directories,
    card,
    directory_index_path,
    escape,
    extra_file_modules,
    find_init_module,
    main_entries,
    module_count,
    rel_link,
    summary,
    supplemental_entries,
)


def prepare_docs_dir(config: BuildConfig) -> None:
    """Create a clean API output directory while preserving hand-written docs."""

    api_dir = config.api_dir
    if api_dir.exists():
        shutil.rmtree(api_dir)
    api_dir.mkdir(parents=True, exist_ok=True)


def write_site_index(config: BuildConfig, modules: list[ModuleDoc]) -> None:
    """Write the GitHub Pages entry point."""

    site_index = config.docs_dir / "index.html"
    eyebrow_html = f'<p class="eyebrow">{escape(config.eyebrow)}</p>' if config.eyebrow else ""
    body = f"""
    {global_sidebar(config, site_index, modules)}
    <main class="content">
      <section class="hero">
        {eyebrow_html}
        <h1>{escape(config.title)}</h1>
        <p>{escape(config.subtitle)}</p>
        <p><code>{escape(config.build_command)}</code></p>
      </section>
      {_main_packages_section(config, modules, site_index)}
      {_supplemental_section(config, modules, site_index)}
    </main>
    """
    site_index.write_text(page(config.title, body, layout="split"), encoding="utf-8")


def write_api_index(config: BuildConfig, modules: list[ModuleDoc]) -> None:
    """Write an API-only index page."""

    api_index = config.api_dir / "index.html"
    body = f"""
    {global_sidebar(config, api_index, modules)}
    <main class="content">
      <p class="eyebrow">Repository API</p>
      <h1>API Reference</h1>
      <p class="muted">Browse by package. Supplemental directories and loose files are listed below the main code base.</p>
      {_main_packages_section(config, modules, api_index)}
      {_supplemental_section(config, modules, api_index)}
    </main>
    """
    api_index.write_text(page("API Reference", body, layout="split"), encoding="utf-8")


def write_directory_pages(config: BuildConfig, modules: list[ModuleDoc]) -> None:
    """Write recursive directory index pages for the API reference."""

    dirs = all_directories(modules)
    for directory in dirs:
        _write_directory_page(config, directory, modules, dirs)


def write_module_pages(config: BuildConfig, modules: list[ModuleDoc]) -> None:
    """Write one API page per parsed module, excluding ``__init__.py`` files.

    ``__init__.py`` content lives on the containing directory's package page.
    """

    classes = class_index(modules)
    for module in modules:
        if module.source_rel.name == "__init__.py":
            continue
        _write_module_page(config, module, modules, classes)


def _main_packages_section(
    config: BuildConfig, modules: list[ModuleDoc], from_path: Path
) -> str:
    """Render the site/API index section listing the project's main packages."""

    entries = main_entries(config)
    if not entries:
        return ""
    rows = "\n".join(
        card(
            rel_link(from_path, directory_index_path(config, entry)),
            entry.name,
            f"{module_count(modules, entry)} modules",
        )
        for entry in entries
    )
    heading = "Main Package" if len(entries) == 1 else "Main Packages"
    return f"""
      <section>
        <h2>{escape(heading)}</h2>
        <ul class="module-list detailed">{rows}</ul>
      </section>
    """


def _supplemental_section(
    config: BuildConfig, modules: list[ModuleDoc], from_path: Path
) -> str:
    """Render the section listing supplemental directories and rogue files."""

    dir_cards = [
        card(
            rel_link(from_path, directory_index_path(config, directory)),
            f"{directory.as_posix()}/",
            f"{module_count(modules, directory)} modules",
        )
        for directory in supplemental_entries(config)
    ]
    file_cards = [
        card(
            rel_link(from_path, module.page_path),
            module.source_rel.name,
            summary(module.docstring),
        )
        for module in extra_file_modules(config, modules)
    ]
    if not dir_cards and not file_cards:
        return ""
    rows = "\n".join(dir_cards + file_cards)
    return f"""
      <section>
        <h2>Supplemental</h2>
        <ul class="module-list detailed">{rows}</ul>
      </section>
    """


def _write_directory_page(
    config: BuildConfig,
    directory: Path,
    modules: list[ModuleDoc],
    dirs: set[Path],
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
    if directory.parent != Path("."):
        parent_link = (
            f"<a class='back' href='{rel_link(current_path, directory_index_path(config, directory.parent))}'>"
            f"Parent Directory</a>"
        )
    else:
        parent_link = (
            f"<a class='back' href='{rel_link(current_path, config.api_dir / 'index.html')}'>API Index</a>"
        )

    if init_module is not None:
        classes = class_index(modules)
        init_source = package_source_dropdown(init_module.source_rel.name, init_module.full_source)
        init_docs = doc_block(init_module.docstring)
        init_objects = "\n".join(
            render_object(obj, init_module, classes) for obj in init_module.objects
        )
        heading_label = init_module.module_name
        eyebrow = f"{directory.as_posix()}/"
    else:
        init_source = ""
        init_docs = ""
        init_objects = ""
        heading_label = f"{directory.as_posix()}/"
        eyebrow = f"{directory.as_posix()}/"

    body = f"""
    {package_sidebar(config, current_path, directory, init_module, modules)}
    <main class="content">
      <p class="eyebrow">{escape(eyebrow)}</p>
      <h1>{escape(heading_label)}</h1>
      <div class="crumbs">
        <a href="{rel_link(current_path, config.docs_dir / 'index.html')}">Project Docs</a>
        <span>/</span>
        <a href="{rel_link(current_path, config.api_dir / 'index.html')}">API Reference</a>
      </div>
      {parent_link}
      {init_source}
      {init_docs}
      {init_objects}
      <section class="directory-section">
        <h2>Subpackages and Directories</h2>
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
    current_path.write_text(page(title, body, layout="split"), encoding="utf-8")


def _write_module_page(
    config: BuildConfig,
    module: ModuleDoc,
    modules: list[ModuleDoc],
    classes: dict,
) -> None:
    """Write one module API page."""

    module.page_path.parent.mkdir(parents=True, exist_ok=True)
    objects = "\n".join(render_object(obj, module, classes) for obj in module.objects)
    body = f"""
    {module_sidebar(config, module, modules)}
    <main class="content">
      <p class="eyebrow">{escape(module.source_rel.as_posix())}</p>
      <h1>{escape(module.module_name)}</h1>
      {doc_block(module.docstring)}
      {objects or '<p class="muted">No public classes or functions found.</p>'}
    </main>
    """
    module.page_path.write_text(page(module.module_name, body, layout="split"), encoding="utf-8")
