# pydoc-builder

Static HTML documentation builder for Python projects. Parses sources with
`ast` and writes a self-contained docs site — no project imports, no runtime
dependencies, only the Python standard library.

## Install

From git, into an isolated tool environment:

```bash
uv tool install git+https://github.com/<you>/pydoc-builder
```

As a project dev dependency:

```bash
uv add --dev git+https://github.com/<you>/pydoc-builder
```

Or locally from a checkout:

```bash
uv tool install /path/to/pydoc-builder
```

Requires Python 3.10+.

## Usage

From the root of your project:

```bash
pydoc-builder
```

The tool auto-discovers what to document. Open `docs/index.html` afterwards.

### Auto-discovery

The project root is scanned for:

- **Main code-base candidates** — any subdirectory that either is a Python
  package (has `__init__.py` at its root) or contains a package anywhere in
  its subtree. A wrapper like `src/` qualifies, and so does a top-level
  package like `mypkg/`.
- **Supplemental directories** — subdirectories that contain `.py` files but
  no `__init__.py` anywhere (for example `tests/`, `scripts/`, `examples/`).
- **Rogue files** — loose `.py` files directly in the project root.

Hidden directories and the usual cruft (`__pycache__`, `node_modules`,
`venv`, `dist`, `build`, `.tox`, `.mypy_cache`, ...) are skipped.

If exactly one main candidate exists, it is used. If more than one is found,
you are prompted to pick which one is your project's main code base; the
others are demoted to supplemental. Pass `--package <name>` to skip the
prompt non-interactively.

If no candidate is found, the build fails — your project needs at least one
directory with an `__init__.py` somewhere inside it.

### How packages are rendered

For every directory that contains an `__init__.py`, the package's page
shows:

1. A collapsed `<details>` dropdown with the raw `__init__.py` source.
2. The `__init__.py` docstring as the main page description.
3. Cards for subpackages, child directories, and submodules. The
   `__init__.py` file itself does **not** appear as a card.
4. Any classes or functions defined directly in `__init__.py`, fully
   rendered like on a module page.

No separate `__init__.html` is written — the package directory's
`index.html` is the canonical landing page.

### Options

```
--project-root PATH    Project root to scan (default: cwd)
--docs-dir PATH        Output directory (default: <project-root>/docs)
--package NAME         Main code-base directory name when multiple candidates
                       exist (skips the interactive prompt)
--title TEXT           Site title (default: "Project Documentation")
--eyebrow TEXT         Small label rendered above the title
--subtitle TEXT        Paragraph rendered below the title
--command TEXT         Command displayed on the site index (default: pydoc-builder)
--no-check-args        Skip the Google-style Args coverage check
```

### Example

```bash
pydoc-builder \
  --title "My Project" \
  --eyebrow "Internal" \
  --package src \
  --command "uv run pydoc-builder"
```

## What it generates

- `docs/index.html` — site entry point with a hero, "Main Package(s)", and
  optional "Supplemental" section
- `docs/api/index.html` — API reference index
- `docs/api/<package>/index.html` — one package page per `__init__.py`
  directory, with the `__init__.py` source dropdown, docstring, and child
  listings
- `docs/api/<path>.html` — one page per non-`__init__` module
- `docs/.nojekyll` — for GitHub Pages

## Conventions

Docstrings are rendered as Google-style sections when any of the following
headings are present: `Args:`, `Arguments:`, `Parameters:`, `Returns:`,
`Yields:`, `Raises:`, `Example`/`Examples`. Other docstrings render as prose
with indented blocks preserved as literal code.

By default, every public callable (name not starting with `_`) must document
each of its parameters in an `Args:` section, or the build fails with an
`AssertionError`. Disable with `--no-check-args`.

## Programmatic use

```python
from pathlib import Path
from pydoc_builder import BuildConfig, build

build(BuildConfig(
    project_root=Path.cwd(),
    docs_dir=Path("docs"),
    main_root=Path("src"),
    supplemental_roots=(Path("tests"),),
    extra_files=(Path("setup.py"),),
    title="My Project",
))
```

## Package layout

```
src/pydoc_builder/
  cli.py           argparse, auto-discovery, prompt → BuildConfig → build()
  discovery.py     scan project root → ProjectLayout
  config.py        BuildConfig dataclass
  builder.py       orchestrator
  parsing.py       AST → ModuleDoc
  validation.py    Args coverage check
  docstrings.py    Google-style section parsing and rendering
  highlighting.py  tokenize-based Python syntax highlighter
  rendering.py     API object rendering, class index, source dropdown
  navigation.py    sidebars, TOC, source tree
  pages.py         site index, API index, directory and module pages
  layout.py        shared HTML / CSS / MathJax shell
  models.py        ApiObject, ModuleDoc
  utils.py         escape, rel_link, anchor, card, entry helpers
```
