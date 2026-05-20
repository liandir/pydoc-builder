# pydoc-builder

Static HTML documentation builder for Python projects. Parses sources with
`ast` and writes a self-contained docs site — no project imports, no runtime
dependencies, only the Python standard library.

## Install

From git, into an isolated tool environment:

```bash
uv tool install git+https://github.com/liandir/pydoc-builder
```

As a project dev dependency:

```bash
uv add --dev git+https://github.com/liandir/pydoc-builder
```

Or locally from a checkout:

```bash
uv tool install /path/to/pydoc-builder
```

Requires Python 3.10+.

## Docstring conventions

pydoc-builder renders docstrings in one of two modes, chosen automatically per
docstring:

- **Structured (Google-style)** — used when the docstring contains any of the
  recognised section headings.
- **Plain prose** — used otherwise; paragraphs render as `<p>`, and any
  indented block becomes a literal `<pre>` code block.

### Google-style sections

A docstring is rendered as structured sections as soon as one of the following
headings appears on its own line (case-insensitive, trailing colon required
for the field sections):

| Heading                              | Rendered as       |
| ------------------------------------ | ----------------- |
| `Args:`, `Arguments:`, `Parameters:` | Arguments table   |
| `Returns:`                           | Returns table     |
| `Yields:`                            | Yields table      |
| `Raises:`                            | Raises table      |
| `Example`, `Examples`                | Examples section  |

Everything before the first heading is the summary and renders as prose.
Field entries inside `Args:` / `Returns:` / `Yields:` / `Raises:` follow the
Google form:

```
Args:
    name (type): description that may wrap onto
        the next indented line.
    other_name: description without a type.

Returns:
    type: description. (The "name" slot is treated as the type
        when only one token precedes the colon.)

Raises:
    ValueError: when the input is malformed.
```

Inside the `Examples` section, lines beginning with `>>>` or `...` are
grouped into a doctest-style code block; intervening prose renders as
paragraphs. Other indented blocks anywhere in the docstring are preserved
verbatim as literal code.

By default, every public callable (name not starting with `_`) must document
each of its parameters in an `Args:` section, or the build fails with an
`AssertionError`. Disable with `--no-check-args`.

### MathJax

Every generated page loads MathJax 3 (TeX → SVG) from a CDN, so LaTeX math in
docstrings is typeset client-side. Both inline and display delimiters are
configured:

- Inline: `$ ... $` or `\( ... \)`
- Display: `$$ ... $$` or `\[ ... \]`

Display math written on its own lines is wrapped in a `<div class="math-block">`
so it stays out of paragraph flow:

```
The Gaussian density is

\[
    f(x) = \frac{1}{\sigma \sqrt{2\pi}}
           \exp\!\left(-\tfrac{(x-\mu)^2}{2\sigma^2}\right)
\]

and integrates to one over $\mathbb{R}$.
```

Inline math like `$\mathbb{R}$` is left untouched inside the surrounding
`<p>` and rendered by MathJax in the browser. Because rendering happens
client-side, the docs page works offline only if the MathJax CDN script is
cached; otherwise math falls back to its raw TeX source.

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
--no-check-args        Skip the Google-style Args coverage check
```

### Example

```bash
pydoc-builder --package src
```

## What it generates

- `docs/index.html` — project home; renders the main package directory
  (its `__init__.py` source dropdown, docstring, and child listings)
- `docs/api/<package>/<subpackage>/index.html` — one page per subpackage
  `__init__.py`
- `docs/api/<path>.html` — one page per non-`__init__` module
- `docs/.nojekyll` — for GitHub Pages

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
  pages.py         home, directory and module pages
  layout.py        shared HTML / CSS / MathJax shell
  models.py        ApiObject, ModuleDoc
  utils.py         escape, rel_link, anchor, card, entry helpers
```
