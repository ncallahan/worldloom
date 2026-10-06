# Explicit FMG index spaces and reference resolution.

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class RefSpec:
    source_path: str
    target_space: str
    sentinel: int | None = -1

@dataclass(frozen=True)
class ResolvedMeshRef:
    space: str
    index: int

def resolve_mesh_ref(value: Any, spec: RefSpec, *, limits: dict[str, int]) -> ResolvedMeshRef | None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{spec.source_path} reference must be an integer")
    if spec.sentinel is not None and value == spec.sentinel:
        return None
    limit = limits.get(spec.target_space)
    if limit is None:
        raise KeyError(f"Unknown target space: {spec.target_space}")
    if value < 0 or value >= limit:
        raise IndexError(f"{spec.source_path} reference {value} is outside {spec.target_space} [0, {limit})")
    return ResolvedMeshRef(spec.target_space, value)

MESH_REF_SPECS = (
    RefSpec("pack.cells.c", "pack.cells"),
    RefSpec("pack.cells.v", "pack.vertices"),
    RefSpec("pack.vertices.v", "grid.vertices"),
    RefSpec("pack.vertices.c", "grid.cells"),
)
