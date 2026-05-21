"""Command-line entry point for the ``pydoc-builder`` script."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .builder import build
from .config import BuildConfig
from .discovery import ProjectLayout, discover_layout


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and build the documentation site.

    Args:
        argv: Optional list of command-line arguments. ``None`` (the default)
            uses ``sys.argv[1:]``.

    Returns:
        Process exit code: ``0`` on success, ``1`` if validation failed.
    """

    parser = _build_parser()
    args = parser.parse_args(argv)

    project_root = args.project_root.resolve()
    docs_dir = (args.docs_dir if args.docs_dir.is_absolute() else project_root / args.docs_dir).resolve()

    layout = discover_layout(project_root, exclude=frozenset({docs_dir}))
    if not layout.main_candidates:
        parser.error(
            f"no Python package found under {project_root}. "
            "Expected at least one directory that contains an __init__.py "
            "(either at its root or in a subdirectory)."
        )

    main_root = _choose_main_root(layout, args.package)
    supplemental_roots = tuple(
        candidate for candidate in layout.main_candidates if candidate != main_root
    ) + tuple(layout.supplemental_dirs)

    config = BuildConfig(
        project_root=project_root,
        docs_dir=docs_dir,
        main_root=main_root,
        supplemental_roots=supplemental_roots,
        extra_files=tuple(layout.rogue_files),
        check_arg_docs=args.check_args,
    )

    try:
        build(config)
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for the CLI."""

    parser = argparse.ArgumentParser(
        prog="pydoc-builder",
        description="Build a static HTML documentation site from Python docstrings.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root to scan (default: current directory).",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=Path("docs"),
        help="Output directory for generated documentation (default: <project-root>/docs).",
    )
    parser.add_argument(
        "--package",
        default=None,
        help=(
            "Name of the main code-base directory when multiple candidates exist. "
            "If omitted and more than one candidate is found, you will be prompted."
        ),
    )
    parser.add_argument(
        "--no-check-args",
        dest="check_args",
        action="store_false",
        help="Skip the Google-style Args and Returns coverage check for public callables.",
    )
    parser.set_defaults(check_args=True)
    return parser


def _choose_main_root(layout: ProjectLayout, explicit_name: str | None) -> Path:
    """Pick the main code-base directory from the discovered candidates."""

    candidates = layout.main_candidates
    if explicit_name is not None:
        for candidate in candidates:
            if candidate.name == explicit_name:
                return candidate
        names = ", ".join(c.name for c in candidates)
        raise SystemExit(f"--package {explicit_name!r} not found among candidates: {names}")
    if len(candidates) == 1:
        return candidates[0]
    if not sys.stdin.isatty():
        names = ", ".join(c.name for c in candidates)
        raise SystemExit(
            f"multiple package containers found ({names}); "
            "re-run with --package <name> to pick one non-interactively."
        )
    print("Multiple candidate package containers found in the project root:")
    for index, candidate in enumerate(candidates, start=1):
        print(f"  {index}. {candidate.name}/")
    while True:
        raw = input(f"Choose the main code base [1-{len(candidates)}]: ").strip()
        if not raw:
            return candidates[0]
        try:
            choice = int(raw)
        except ValueError:
            print("Please enter a number.")
            continue
        if 1 <= choice <= len(candidates):
            return candidates[choice - 1]
        print(f"Please enter a number between 1 and {len(candidates)}.")


if __name__ == "__main__":
    sys.exit(main())
