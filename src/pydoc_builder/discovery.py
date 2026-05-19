"""Auto-discover the project's main package container and supplemental Python sources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


IGNORED_DIR_NAMES = frozenset({
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "venv",
    "env",
    ".venv",
    ".env",
    ".tox",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "htmlcov",
})


@dataclass(slots=True)
class ProjectLayout:
    """Result of scanning the project root for Python sources.

    Attributes:
        main_candidates: Project-root subdirectories that either are a package
            themselves (``__init__.py`` at their root) or contain at least one
            descendant package. One of these is selected as the main code base.
        supplemental_dirs: Project-root subdirectories that contain ``.py``
            files but no ``__init__.py`` anywhere — treated as supplemental.
        rogue_files: Loose ``.py`` files directly in the project root.
    """

    main_candidates: list[Path]
    supplemental_dirs: list[Path]
    rogue_files: list[Path]


def discover_layout(project_root: Path, *, exclude: frozenset[Path] = frozenset()) -> ProjectLayout:
    """Scan ``project_root`` immediate children and classify them."""

    candidates: list[Path] = []
    supplemental: list[Path] = []
    rogue: list[Path] = []

    for entry in sorted(project_root.iterdir()):
        if entry.resolve() in exclude:
            continue
        if entry.is_dir():
            if entry.name.startswith(".") or entry.name in IGNORED_DIR_NAMES:
                continue
            if _contains_package(entry):
                candidates.append(entry)
            elif _contains_python(entry):
                supplemental.append(entry)
        elif entry.is_file() and entry.suffix == ".py" and entry.name != "__init__.py":
            rogue.append(entry)

    return ProjectLayout(
        main_candidates=candidates,
        supplemental_dirs=supplemental,
        rogue_files=rogue,
    )


def is_package(directory: Path) -> bool:
    """Return whether ``directory`` is a Python package (has ``__init__.py``)."""

    return (directory / "__init__.py").is_file()


def _contains_package(directory: Path) -> bool:
    """Return True if ``directory`` or any non-ignored descendant has ``__init__.py``."""

    if is_package(directory):
        return True
    for init in directory.rglob("__init__.py"):
        rel = init.relative_to(directory).parts
        if any(part.startswith(".") or part in IGNORED_DIR_NAMES for part in rel):
            continue
        return True
    return False


def _contains_python(directory: Path) -> bool:
    """Return True if ``directory`` has any ``.py`` file in a non-ignored subtree."""

    for py_file in directory.rglob("*.py"):
        rel = py_file.relative_to(directory).parts
        if any(part.startswith(".") or part in IGNORED_DIR_NAMES for part in rel):
            continue
        return True
    return False
