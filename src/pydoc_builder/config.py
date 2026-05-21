"""Build-time configuration for the documentation builder."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class BuildConfig:
    """Inputs and output settings for one documentation build.

    Attributes:
        project_root: Resolved project root that all paths are relative to.
        docs_dir: Output directory for the generated documentation site.
        main_root: The chosen container directory that holds the project's
            main code base. May either be a package itself (it has its own
            ``__init__.py``) or a wrapper (e.g. ``src/``) that contains one
            or more package subdirectories.
        supplemental_roots: Additional directories that should still be
            documented but presented separately from the main code base.
        extra_files: Loose ``.py`` files (typically in the project root) that
            should be documented individually.
        check_arg_docs: When true, the builder reports docstring-coverage
            issues; the build itself never aborts on these.
        suppress_warnings: When true, all coverage warnings are silenced.
        autofill_types: When true, missing docstring argument types are
            backfilled from the function signature's annotations.
        default_theme: Theme used by the rendered pages when the visitor has
            no saved preference (``"light"`` or ``"dark"``).
    """

    project_root: Path
    docs_dir: Path
    main_root: Path
    supplemental_roots: tuple[Path, ...] = field(default_factory=tuple)
    extra_files: tuple[Path, ...] = field(default_factory=tuple)
    check_arg_docs: bool = True
    suppress_warnings: bool = False
    autofill_types: bool = True
    default_theme: str = "light"

    @property
    def api_dir(self) -> Path:
        """Return the directory that holds generated API pages."""

        return self.docs_dir / "api"
