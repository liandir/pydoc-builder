"""Render individual API objects (classes, functions, methods) to HTML."""

from __future__ import annotations

from .docstrings import doc_block
from .highlighting import highlight_python
from .models import ApiObject, ModuleDoc
from .parsing import iter_objects
from .utils import escape, rel_link


def render_object(
    obj: ApiObject,
    module: ModuleDoc,
    class_index: dict[str, tuple[ModuleDoc, ApiObject]],
) -> str:
    """Render an extracted class or function.

    Args:
        obj: The API object (class, function, or method) to render.
        module: The module ``obj`` belongs to; used to compute cross-links.
        class_index: Lookup of unique class names to ``(module, object)`` used
            to link base classes back to their definitions.

    Returns:
        The ``<article>`` HTML fragment for ``obj`` and its nested children.
    """

    children = "\n".join(render_object(child, module, class_index) for child in obj.children)
    heading = _object_heading(obj, module, class_index)
    return f"""
    <article class="api-object" id="{escape(obj.anchor)}">
      <div class="object-meta">{escape(obj.kind)} · line {obj.lineno}</div>
      {heading_with_source(heading, obj.source, obj.lineno)}
      {doc_block(obj.docstring)}
      {children}
    </article>
    """


def heading_with_source(heading_html: str, source: str, start_lineno: int = 1) -> str:
    """Wrap a heading in a <details> that reveals its source on click.

    The body uses a two-column layout: a non-selectable line-number gutter and
    the highlighted source. Keeping the gutter in its own ``<pre>`` means it
    aligns line-for-line with the code without leaking into copy/paste.

    Args:
        heading_html: Pre-rendered HTML for the heading shown in the summary.
        source: Python source displayed when the ``<details>`` is expanded.
        start_lineno: First line number used to label the gutter, matching
            the object's location in the original file.

    Returns:
        A ``<details>`` HTML fragment, or ``heading_html`` unchanged when
        ``source`` is empty.
    """

    if not source.strip():
        return heading_html
    line_count = source.count("\n") + (0 if source.endswith("\n") else 1)
    gutter = "\n".join(str(i) for i in range(start_lineno, start_lineno + max(line_count, 1)))
    return (
        '<details class="source-block">'
        '<summary>'
        f'<div class="summary-heading">{heading_html}</div>'
        '<span class="source-toggle">Source<span class="source-caret">▸</span></span>'
        '</summary>'
        '<div class="source-pane">'
        f'<pre class="source-gutter" aria-hidden="true">{gutter}</pre>'
        f'<pre class="source-code"><code>{highlight_python(source)}</code></pre>'
        '</div>'
        '</details>'
    )


def class_index(modules: list[ModuleDoc]) -> dict[str, tuple[ModuleDoc, ApiObject]]:
    """Return a unique-name index of documented classes.

    Args:
        modules: All parsed modules to scan for top-level and nested classes.

    Returns:
        A mapping from class name to ``(module, object)``. Names that occur
        in more than one place are omitted to avoid ambiguous base-class links.
    """

    candidates: dict[str, list[tuple[ModuleDoc, ApiObject]]] = {}
    for module in modules:
        for obj in iter_objects(module.objects):
            if obj.kind == "class":
                candidates.setdefault(obj.name, []).append((module, obj))
    return {name: values[0] for name, values in candidates.items() if len(values) == 1}


def _object_heading(
    obj: ApiObject,
    module: ModuleDoc,
    class_index: dict[str, tuple[ModuleDoc, ApiObject]],
) -> str:
    """Render an API object heading, including class inheritance."""

    if obj.kind != "class" or not obj.bases:
        return f"<h2>{escape(obj.name)}</h2>"
    bases = ", ".join(_base_link(base, module, class_index) for base in obj.bases)
    return f'<h2>{escape(obj.name)} <span class="inherits">inherits {bases}</span></h2>'


def _base_link(
    base: str,
    module: ModuleDoc,
    class_index: dict[str, tuple[ModuleDoc, ApiObject]],
) -> str:
    """Render a superclass name, linking to internal docs when available."""

    base_name = base.rsplit(".", 1)[-1]
    target = class_index.get(base_name)
    if target is None:
        return f'<span class="superclass">{escape(base)}</span>'
    target_module, target_obj = target
    href = f"{rel_link(module.page_path, target_module.page_path)}#{target_obj.anchor}"
    return f'<a class="superclass" href="{escape(href)}">{escape(base)}</a>'
