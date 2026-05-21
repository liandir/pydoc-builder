"""Report docstring-coverage and type-mismatch warnings for public callables."""

from __future__ import annotations

import sys

from .config import BuildConfig
from .docstrings import parse_doc_fields, split_docstring_sections
from .models import ApiObject, ModuleDoc
from .parsing import iter_objects


def report_docstring_warnings(config: BuildConfig, modules: list[ModuleDoc]) -> None:
    """Print docstring-coverage and type-consistency warnings.

    Three checks are run against every public callable in the main code base:

    * every signature parameter appears in the ``Args:`` section;
    * any callable annotated with a non-``None`` return type has a
      ``Returns:`` or ``Yields:`` section;
    * each parameter has at least one type source (signature annotation or
      a ``(type)`` in the docstring), and the two sources agree when both
      are present.

    Modules outside the main code base (supplemental directories and rogue
    project-root files) are skipped quietly.

    Args:
        config: Resolved build configuration.
        modules: Parsed module documentation payloads to inspect.
    """

    if config.suppress_warnings:
        return

    main_root = config.main_root.resolve()
    warnings: list[str] = []
    for module in modules:
        if not module.source_path.resolve().is_relative_to(main_root):
            continue
        warnings.extend(_module_warnings(module))

    for line in warnings:
        print(f"warning: {line}", file=sys.stderr)


def _module_warnings(module: ModuleDoc) -> list[str]:
    """Return coverage and type warnings for one module."""

    out: list[str] = []
    for obj in iter_objects(module.objects):
        if obj.name.startswith("_"):
            continue
        location = f"{module.source_rel}:{obj.lineno} {obj.qualname}"
        for missing in _missing_arg_docs(obj):
            out.append(f"{location} undocumented argument: {missing}")
        if _missing_returns_doc(obj):
            out.append(f"{location} missing Returns section (annotated -> {obj.returns})")
        out.extend(f"{location} {detail}" for detail in _type_warnings(obj))
    return out


def _missing_arg_docs(obj: ApiObject) -> list[str]:
    """Return parameter names that are not documented in ``obj``'s docstring.

    Variadic parameters (``*args`` and ``**kwargs``) are exempt: their meaning
    is conveyed by the heading marker, not by a per-arg description.

    Args:
        obj: API object whose ``Args:`` section is checked.
    """

    if not obj.params:
        return []
    documented = _documented_arg_fields(obj.docstring)
    return [
        param for param in obj.params
        if param not in documented and not param.startswith("*")
    ]


def _missing_returns_doc(obj: ApiObject) -> bool:
    """Return whether ``obj`` is annotated with a return type but lacks a Returns section.

    Args:
        obj: API object whose return annotation and docstring are checked.
    """

    if not obj.returns or obj.returns.strip() in {"None", "NoReturn", "typing.NoReturn"}:
        return False
    sections = split_docstring_sections(obj.docstring)
    return not sections["returns"] and not sections["yields"]


def _type_warnings(obj: ApiObject) -> list[str]:
    """Return per-arg warnings about missing or disagreeing type information."""

    if not obj.params:
        return []
    doc_fields = _documented_arg_fields(obj.docstring)
    warnings: list[str] = []
    for param in obj.params:
        if param.startswith("*"):
            continue
        annotated = obj.param_annotations.get(param, "")
        documented_entry = doc_fields.get(param)
        if documented_entry is None:
            continue
        documented = documented_entry.strip()
        if not annotated and not documented:
            warnings.append(f"argument {param!r} has no type (signature or docstring)")
        elif annotated and documented and annotated.strip() != documented:
            warnings.append(
                f"argument {param!r} type mismatch: annotation {annotated!r} "
                f"vs docstring {documented!r}"
            )
    return warnings


def _documented_arg_fields(docstring: str) -> dict[str, str]:
    """Return a ``name -> documented type`` mapping from a structured docstring."""

    sections = split_docstring_sections(docstring)
    return {
        field["name"]: field["type"]
        for field in parse_doc_fields(sections["args"])
        if field["name"]
    }
