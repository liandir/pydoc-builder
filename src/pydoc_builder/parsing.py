"""Parse Python source files into documentable objects via ``ast``."""

from __future__ import annotations

import ast
from pathlib import Path

from .config import BuildConfig
from .discovery import IGNORED_DIR_NAMES, is_package
from .models import ApiObject, ModuleDoc
from .utils import anchor


def parse_modules(config: BuildConfig) -> list[ModuleDoc]:
    """Parse every Python source file referenced by ``config``.

    Args:
        config: Build configuration listing the main root, supplemental roots,
            and extra rogue files to parse.

    Returns:
        One ``ModuleDoc`` per discovered ``.py`` file, in discovery order.
    """

    main_name_base = config.main_root.parent if is_package(config.main_root) else config.main_root

    modules: list[ModuleDoc] = []
    for path in _iter_py_files(config.main_root):
        modules.append(_parse_module(path, config, main_name_base))
    for root in config.supplemental_roots:
        for path in _iter_py_files(root):
            modules.append(_parse_module(path, config, config.project_root))
    for path in sorted(config.extra_files):
        modules.append(_parse_module(path, config, config.project_root))
    return modules


def iter_objects(objects: list[ApiObject]) -> list[ApiObject]:
    """Return a flattened list of documented objects.

    Args:
        objects: Top-level API objects whose nested children should be walked
            recursively.

    Returns:
        A depth-first flattening of ``objects`` including every nested child.
    """

    flattened: list[ApiObject] = []
    for obj in objects:
        flattened.append(obj)
        flattened.extend(iter_objects(obj.children))
    return flattened


def _iter_py_files(root: Path) -> list[Path]:
    """Return ``.py`` files under ``root`` while skipping ignored subtrees."""

    found: list[Path] = []
    for py_file in sorted(root.rglob("*.py")):
        rel = py_file.relative_to(root).parts
        if any(part.startswith(".") or part in IGNORED_DIR_NAMES for part in rel):
            continue
        found.append(py_file)
    return found


def _parse_module(path: Path, config: BuildConfig, name_base: Path) -> ModuleDoc:
    """Parse one source file and collect its public docstrings."""

    source_text = path.read_text(encoding="utf-8")
    tree = ast.parse(source_text, filename=str(path))
    source_rel = path.relative_to(config.project_root)
    module_rel = path.relative_to(name_base) if path.is_relative_to(name_base) else source_rel
    module_name = ".".join(module_rel.with_suffix("").parts)
    if module_name.endswith(".__init__"):
        module_name = module_name[: -len(".__init__")]
    elif module_name == "__init__":
        module_name = name_base.name
    page_path = config.api_dir / source_rel.with_suffix(".html")
    return ModuleDoc(
        source_path=path,
        source_rel=source_rel,
        module_name=module_name,
        page_path=page_path,
        docstring=ast.get_docstring(tree) or "",
        objects=[_parse_object(node, source_text) for node in tree.body if _is_documentable(node)],
        full_source=source_text,
    )


def _parse_object(node: ast.AST, source_text: str, parent: str = "") -> ApiObject:
    """Parse a class or function node into a serializable documentation object."""

    assert isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
    children: list[ApiObject] = []
    qualname = f"{parent}.{node.name}" if parent else node.name
    if isinstance(node, ast.ClassDef):
        kind = "class"
        bases = [ast.unparse(base) for base in [*node.bases, *[kw.value for kw in node.keywords]]]
        params: list[str] = []
        returns = ""
        children = [
            _parse_object(child, source_text, qualname)
            for child in node.body
            if _is_documentable(child)
        ]
    else:
        kind = ("async " if isinstance(node, ast.AsyncFunctionDef) else "") + ("method" if parent else "function")
        bases = []
        params = _documentable_arg_names(node.args)
        returns = "" if _is_property(node) else (
            ast.unparse(node.returns) if node.returns is not None else ""
        )

    return ApiObject(
        kind=kind,
        name=node.name,
        qualname=qualname,
        anchor=anchor(qualname),
        bases=bases,
        params=params,
        returns=returns,
        docstring=ast.get_docstring(node) or "",
        source=ast.get_source_segment(source_text, node) or "",
        lineno=node.lineno,
        children=children,
    )


def _is_property(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return whether a function node is decorated as a ``@property``.

    Args:
        node: Function or async function AST node.
    """

    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "property":
            return True
    return False


def _is_documentable(node: ast.AST) -> bool:
    """Return whether a node should appear in API documentation."""

    return isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)


def _documentable_arg_names(args: ast.arguments) -> list[str]:
    """Return parameter names that must be documented."""

    names = [arg.arg for arg in [*args.posonlyargs, *args.args] if arg.arg not in {"self", "cls"}]
    if args.vararg is not None:
        names.append(f"*{args.vararg.arg}")
    names.extend(arg.arg for arg in args.kwonlyargs)
    if args.kwarg is not None:
        names.append(f"**{args.kwarg.arg}")
    return names
