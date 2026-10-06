# Deterministic diagnostics for tolerated FMG import anomalies.

from __future__ import annotations
from collections import Counter
from typing import Any
from .spaces import MESH_REF_SPECS, resolve_mesh_ref

def build_mesh_diagnostics(data: dict[str, Any]) -> dict[str, Any]:
    pack = data["pack"]
    grid = data.get("grid") or {}
    limits = {
        "pack.cells": len(pack["cells"]),
        "pack.vertices": len(pack.get("vertices", [])),
        "grid.cells": len(grid.get("cells", [])),
        "grid.vertices": len(grid.get("vertices", [])),
    }
    sentinels: Counter[str] = Counter()
    out_of_range: Counter[str] = Counter()
    examples: list[dict[str, Any]] = []

    def check(path: str, values: list[Any], spec) -> None:
        for position, value in enumerate(values):
            try:
                resolved = resolve_mesh_ref(value, spec, limits=limits)
            except IndexError:
                out_of_range[path] += 1
                if len(examples) < 10:
                    examples.append({"path": path, "position": position, "value": value})
            except TypeError:
                if len(examples) < 10:
                    examples.append({"path": path, "position": position, "value": value, "kind": "invalid-type"})
            else:
                if resolved is None:
                    sentinels[path] += 1

    cells = pack["cells"]
    check("pack.cells.c", [v for cell in cells for v in cell.get("c", [])], MESH_REF_SPECS[0])
    check("pack.cells.v", [v for cell in cells for v in cell.get("v", [])], MESH_REF_SPECS[1])
    vertices = pack.get("vertices", [])
    check("pack.vertices.v", [v for vertex in vertices for v in vertex.get("v", [])], MESH_REF_SPECS[2])
    check("pack.vertices.c", [v for vertex in vertices for v in vertex.get("c", [])], MESH_REF_SPECS[3])
    return {
        "sentinels_minus_one": dict(sorted(sentinels.items())),
        "out_of_range": dict(sorted(out_of_range.items())),
        "out_of_range_examples": examples,
    }
