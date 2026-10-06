# Deterministic diagnostics for tolerated FMG import anomalies.

from __future__ import annotations

from collections import Counter
from typing import Any

from .spaces import MESH_REF_SPECS, resolve_mesh_ref


def build_mesh_diagnostics(data: dict[str, Any]) -> dict[str, Any]:
    pack = data["pack"]
    missing_sections: list[str] = []
    invalid_structure: list[dict[str, Any]] = []

    if "vertices" not in pack:
        missing_sections.append("pack.vertices")
        vertices = []
    else:
        vertices = pack["vertices"]
        if not isinstance(vertices, list):
            invalid_structure.append({"path": "pack.vertices", "kind": "invalid-structure"})
            vertices = []

    grid = data.get("grid")
    grid_missing = grid is None
    if grid_missing:
        missing_sections.append("grid")
        grid = {}
    elif not isinstance(grid, dict):
        invalid_structure.append({"path": "grid", "kind": "invalid-structure"})
        grid = {}

    if not grid_missing:
        for path in ("cells", "vertices"):
            if path not in grid:
                missing_sections.append(f"grid.{path}")
            elif not isinstance(grid[path], list):
                invalid_structure.append({"path": f"grid.{path}", "kind": "invalid-structure"})

    cells = pack["cells"]
    if not isinstance(cells, list):
        raise ValueError("FMG source pack.cells must be a list")

    limits = {
        "pack.cells": len(cells),
        "pack.vertices": len(vertices),
        "grid.cells": len(grid.get("cells", [])) if isinstance(grid.get("cells", []), list) else 0,
        "grid.vertices": len(grid.get("vertices", [])) if isinstance(grid.get("vertices", []), list) else 0,
    }
    sentinels: Counter[str] = Counter()
    out_of_range: Counter[str] = Counter()
    examples: list[dict[str, Any]] = []

    def check(path: str, records: list[Any], key: str) -> None:
        spec = MESH_REF_SPECS[key]
        for position, record in enumerate(records):
            if not isinstance(record, dict):
                invalid_structure.append(
                    {"path": path, "position": position, "kind": "invalid-structure"}
                )
                continue
            values = record.get(key.rsplit(".", 1)[1])
            if values is None:
                continue
            if not isinstance(values, list):
                invalid_structure.append(
                    {"path": path, "position": position, "kind": "invalid-structure"}
                )
                continue
            for value_position, value in enumerate(values):
                try:
                    resolved = resolve_mesh_ref(value, spec, limits=limits)
                except IndexError:
                    out_of_range[path] += 1
                    if len(examples) < 10:
                        examples.append(
                            {
                                "path": path,
                                "position": position,
                                "value_position": value_position,
                                "value": value,
                            }
                        )
                except TypeError:
                    if len(examples) < 10:
                        examples.append(
                            {
                                "path": path,
                                "position": position,
                                "value_position": value_position,
                                "value": value,
                                "kind": "invalid-type",
                            }
                        )
                else:
                    if resolved is None:
                        sentinels[path] += 1

    check("pack.cells.c", cells, "pack.cells.c")
    if "pack.vertices" not in missing_sections and isinstance(vertices, list):
        check("pack.cells.v", cells, "pack.cells.v")
    if (
        "pack.vertices" not in missing_sections
        and isinstance(vertices, list)
        and "grid.vertices" not in missing_sections
        and "grid.cells" not in missing_sections
    ):
        check("pack.vertices.v", vertices, "pack.vertices.v")
        check("pack.vertices.c", vertices, "pack.vertices.c")

    return {
        "missing_sections": sorted(set(missing_sections)),
        "invalid_structure": invalid_structure[:10],
        "sentinels_minus_one": dict(sorted(sentinels.items())),
        "out_of_range": {
            path: out_of_range.get(path, 0)
            for path in sorted(MESH_REF_SPECS)
        },
        "out_of_range_examples": examples,
    }
