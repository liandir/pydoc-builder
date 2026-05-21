"""Dataclasses used to pass parsed documentation between modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ApiObject:
    """Documented Python object extracted from the syntax tree."""

    kind: str
    name: str
    qualname: str
    anchor: str
    bases: list[str]
    params: list[str]
    returns: str
    docstring: str
    source: str
    lineno: int
    children: list["ApiObject"] = field(default_factory=list)


@dataclass(slots=True)
class ModuleDoc:
    """Rendered documentation payload for one Python module or script."""

    source_path: Path
    source_rel: Path
    module_name: str
    page_path: Path
    docstring: str
    objects: list[ApiObject]
    full_source: str
