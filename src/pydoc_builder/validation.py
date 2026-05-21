"""Check that public callables document their arguments and return values."""

from __future__ import annotations

from .config import BuildConfig
from .docstrings import parse_doc_fields, split_docstring_sections
from .models import ApiObject, ModuleDoc
from .parsing import iter_objects


def assert_documented_callables(config: BuildConfig, modules: list[ModuleDoc]) -> None:
    """Assert every public callable in the main code base documents itself.

    Two coverage rules are enforced:

    * every parameter named in the signature appears in the ``Args:`` section;
    * any callable annotated with a non-``None`` return type has a ``Returns:``
      or ``Yields:`` section.

    Modules outside the main code base (supplemental directories and rogue
    project-root files) are not held to these rules: if any of their public
    callables have missing entries, the module is simply reported as skipped
    rather than aborting the build.

    Args:
        config: Resolved build configuration.
        modules: Parsed module documentation payloads to validate.

    Underscore-prefixed callables (including dunders) are skipped — they are
    internal helpers and not held to the same coverage rules.
    """

    main_root = config.main_root.resolve()
    failures: list[str] = []
    skipped: list[ModuleDoc] = []
    for module in modules:
        module_failures = _module_failures(module)
        if not module_failures:
            continue
        if module.source_path.resolve().is_relative_to(main_root):
            failures.extend(module_failures)
        else:
            skipped.append(module)

    for module in skipped:
        print(f"skipped doc check for {module.source_rel} (outside main code base)")
    if failures:
        raise AssertionError("Undocumented callable signatures:\n" + "\n".join(failures))


def _module_failures(module: ModuleDoc) -> list[str]:
    """Return doc-coverage failure messages for one module.

    Args:
        module: Parsed module to inspect.
    """

    failures: list[str] = []
    for obj in iter_objects(module.objects):
        if obj.name.startswith("_"):
            continue
        missing_args = _missing_arg_docs(obj)
        if missing_args:
            failures.append(
                f"{module.source_rel}:{obj.lineno} {obj.qualname} missing Args entries: "
                f"{', '.join(missing_args)}"
            )
        if _missing_returns_doc(obj):
            failures.append(
                f"{module.source_rel}:{obj.lineno} {obj.qualname} missing Returns section "
                f"(annotated -> {obj.returns})"
            )
    return failures


def _missing_arg_docs(obj: ApiObject) -> list[str]:
    """Return parameter names that are not documented in ``obj``'s docstring.

    Args:
        obj: API object whose ``Args:`` section is checked.
    """

    if not obj.params:
        return []
    documented = _documented_arg_names(obj.docstring)
    return [param for param in obj.params if param not in documented]


def _missing_returns_doc(obj: ApiObject) -> bool:
    """Return whether ``obj`` is annotated with a return type but lacks a Returns section.

    Args:
        obj: API object whose return annotation and docstring are checked.
    """

    if not obj.returns or obj.returns.strip() in {"None", "NoReturn", "typing.NoReturn"}:
        return False
    sections = split_docstring_sections(obj.docstring)
    return not sections["returns"] and not sections["yields"]


def _documented_arg_names(docstring: str) -> set[str]:
    """Return argument names documented in a structured docstring.

    Args:
        docstring: Raw docstring text whose ``Args:`` section is parsed.
    """

    sections = split_docstring_sections(docstring)
    return {field["name"] for field in parse_doc_fields(sections["args"]) if field["name"]}
