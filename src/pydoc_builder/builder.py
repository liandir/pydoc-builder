"""Top-level orchestrator: parse → validate → write the documentation site."""

from __future__ import annotations

from .config import BuildConfig
from .pages import (
    prepare_docs_dir,
    write_directory_pages,
    write_module_pages,
    write_site_index,
)
from .parsing import parse_modules
from .validation import assert_documented_arguments


def build(config: BuildConfig) -> int:
    """Generate the documentation site under ``config.docs_dir``.

    Args:
        config: Resolved build configuration.

    Returns:
        Number of API pages written.
    """

    modules = parse_modules(config)
    if config.check_arg_docs:
        assert_documented_arguments(config, modules)
    prepare_docs_dir(config)
    write_module_pages(config, modules)
    write_directory_pages(config, modules)
    write_site_index(config, modules)
    (config.docs_dir / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Wrote {len(modules)} API pages to {config.docs_dir}")
    return len(modules)
