"""Check that public callables document their arguments."""

from __future__ import annotations

from .config import BuildConfig
from .docstrings import parse_doc_fields, split_docstring_sections
from .models import ApiObject, ModuleDoc
from .parsing import iter_objects


def assert_documented_arguments(config: BuildConfig, modules: list[ModuleDoc]) -> None:
    """Assert every public callable in the main code base documents its arguments.

    Modules outside the main code base (supplemental directories and rogue
    project-root files) are not held to the same coverage rule: if any of
    their public callables have undocumented arguments, the module is simply
    reported as skipped rather than aborting the build.

    Args:
        config: Resolved build configuration.
        modules: Parsed module documentation payloads to validate.

    Underscore-prefixed callables (including dunders) are skipped — they are
    internal helpers and not held to the same Args-section coverage rule.
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
        print(f"skipped arg-doc check for {module.source_rel} (outside main code base)")
    if failures:
        raise AssertionError("Undocumented callable arguments:\n" + "\n".join(failures))


def _module_failures(module: ModuleDoc) -> list[str]:
    """Return missing-Args failure messages for one module."""

    failures: list[str] = []
    for obj in iter_objects(module.objects):
        if obj.name.startswith("_"):
            continue
        if not obj.params:
            continue
        missing = _missing_arg_docs(obj)
        if missing:
            failures.append(
                f"{module.source_rel}:{obj.lineno} {obj.qualname} missing Args entries: "
                f"{', '.join(missing)}"
            )
    return failures


def _missing_arg_docs(obj: ApiObject) -> list[str]:
    """Return parameter names that are not documented in ``obj``'s docstring."""

    documented = _documented_arg_names(obj.docstring)
    return [param for param in obj.params if param not in documented]


def _documented_arg_names(docstring: str) -> set[str]:
    """Return argument names documented in a structured docstring."""

    sections = split_docstring_sections(docstring)
    return {field["name"] for field in parse_doc_fields(sections["args"]) if field["name"]}
