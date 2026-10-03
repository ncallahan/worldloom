#!/usr/bin/env python3
"""Bounded measurements for Azgaar FMG full JSON exports.

Usage:
  python experiments/fmg_scale/measure_fmg.py file.json [file2.json ...]

The script never prints raw records. It reports bounded counts, byte totals,
reference-integrity summaries, shape/type variance, and deterministic section
hashes. If the installed Worldloom package is importable, it also measures the
existing WorldState operations requested by H8.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def compact_bytes(value) -> int:
    return len(json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode())


def collection_summary(value):
    if not isinstance(value, list):
        return {"type": type(value).__name__}
    dicts = [x for x in value if isinstance(x, dict)]
    bare = [i for i, x in enumerate(value) if isinstance(x, int) and not isinstance(x, bool)]
    nulls = [i for i, x in enumerate(value) if x is None]
    ids = [x.get("i") for x in dicts if isinstance(x.get("i"), int)]
    types = defaultdict(Counter)
    keys = Counter()
    for x in dicts:
        for k, v in x.items():
            keys[k] += 1
            types[k][type(v).__name__] += 1
    return {
        "count": len(value),
        "dicts": len(dicts),
        "bare_int_positions": bare[:5],
        "bare_int_count": len(bare),
        "null_positions": nulls[:5],
        "null_count": len(nulls),
        "id_min": min(ids) if ids else None,
        "id_max": max(ids) if ids else None,
        "i_eq_index": sum(1 for i, x in enumerate(value)
                          if isinstance(x, dict) and x.get("i") == i),
        "keys": dict(keys),
        "mixed_types": {k: dict(v) for k, v in types.items() if len(v) > 1},
    }


def check_refs(data):
    pack = data["pack"]
    pc, pv = len(pack["cells"]), len(pack["vertices"])
    checks = {}

    def add(label, values, limit):
        vals = [v for v in values if isinstance(v, int) and not isinstance(v, bool)]
        bad = [v for v in vals if v < 0 or v >= limit]
        checks[label] = {"refs": len(vals), "oob": len(bad), "examples": bad[:5]}

    cells = pack["cells"]
    add("cells.c", (v for x in cells for v in x.get("c", [])), pc)
    add("cells.v", (v for x in cells for v in x.get("v", [])), pv)
    for field, coll in (("burg", "burgs"), ("state", "states"),
                        ("province", "provinces"), ("culture", "cultures"),
                        ("religion", "religions")):
        add("cells." + field, (x.get(field) for x in cells), len(pack[coll]))
    add("burgs.cell", (x.get("cell") for x in pack["burgs"] if isinstance(x, dict)), pc)
    add("burgs.state", (x.get("state") for x in pack["burgs"] if isinstance(x, dict)), len(pack["states"]))
    add("states.neighbors", (v for x in pack["states"] if isinstance(x, dict)
                             for v in x.get("neighbors", [])), len(pack["states"]))
    add("states.provinces", (v for x in pack["states"] if isinstance(x, dict)
                             for v in x.get("provinces", [])), len(pack["provinces"]))
    add("rivers.cells", (v for x in pack["rivers"] if isinstance(x, dict)
                         for v in x.get("cells", [])), pc)
    add("markers.cell", (x.get("cell") for x in pack["markers"] if isinstance(x, dict)), pc)
    add("zones.cells", (v for x in pack["zones"] if isinstance(x, dict)
                        for v in x.get("cells", [])), pc)
    route_cells = [p[2] for r in pack["routes"] if isinstance(r, dict)
                   for p in r.get("points", []) if isinstance(p, list) and len(p) >= 3
                   and isinstance(p[2], int)]
    add("routes.points.cell", route_cells, pc)
    vertices_c = (v for x in pack["vertices"] if isinstance(x, dict) for v in x.get("c", []))
    add("vertices.c.vs_pack_cells", vertices_c, pc)
    vertices_c = (v for x in pack["vertices"] if isinstance(x, dict) for v in x.get("c", []))
    add("vertices.c.vs_grid_cells", vertices_c, len(data.get("grid", {}).get("cells", [])))
    return checks


def h8(data, path):
    try:
        from worldloom.core.state import WorldState
    except Exception as exc:
        return {"status": "unavailable", "reason": type(exc).__name__ + ": " + str(exc)}
    results = {}

    def run(label, fn):
        tracemalloc.start()
        start = time.perf_counter()
        fn()
        seconds = time.perf_counter() - start
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        results[label] = {"seconds": round(seconds, 6), "peak_tracemalloc_bytes": peak}

    import tracemalloc
    run("load", lambda: json.load(path.open(encoding="utf-8")))
    state = WorldState()
    run("set_field:pack.cells", lambda: state.set_field("pack.cells", data["pack"]["cells"]))
    run("set_field:pack.vertices", lambda: state.set_field("pack.vertices", data["pack"]["vertices"]))
    run("set_field:grid.cells", lambda: state.set_field("grid.cells", data["grid"]["cells"]))
    snapshot = None
    run("snapshot", lambda: state.snapshot())
    snapshot = state.snapshot()
    run("restore", lambda: state.restore(snapshot))
    run("json.dumps", lambda: json.dumps(data, separators=(",", ":"), ensure_ascii=True))
    return {"status": "measured", "results": results}


def measure(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    size = path.stat().st_size
    info = data.get("info", {})
    graph = data.get("settings", {}).get("options", {}).get("map", {}).get("graph", {})
    pack, grid = data["pack"], data.get("grid", {})
    g = Counter(x.get("g") for x in pack["cells"] if isinstance(x, dict) and isinstance(x.get("g"), int))
    sections = {}
    for key in ("info", "settings", "pack", "grid", "nameBases"):
        if key in data:
            sections[key] = compact_bytes(data[key])
    return {
        "bytes": size,
        "sha256": sha256(path),
        "info": {k: info.get(k) for k in ("version", "mapName", "width", "height", "seed", "mapId")},
        "requested_points": graph.get("points"),
        "pack_cells": len(pack["cells"]),
        "pack_vertices": len(pack["vertices"]),
        "grid_cells": len(grid.get("cells", [])),
        "grid_vertices": len(grid.get("vertices", [])),
        "grid_bytes": compact_bytes(grid),
        "grid_fraction": compact_bytes(grid) / size,
        "pack_grid_fraction": len(pack["cells"]) / len(grid["cells"]),
        "pack_requested_fraction": len(pack["cells"]) / graph["points"] if graph.get("points") else None,
        "g_unique": len(g),
        "g_duplicate_indices": sum(1 for n in g.values() if n > 1),
        "g_max_multiplicity": max(g.values()) if g else 0,
        "grid_without_pack": len(grid["cells"]) - len(g),
        "sections_bytes": sections,
        "collections": {k: collection_summary(v) for k, v in pack.items() if isinstance(v, list)},
        "refs": check_refs(data),
        "section_hashes": {
            k: hashlib.sha256(json.dumps(pack[k], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            for k in ("cells", "vertices") if k in pack
        },
        "h8": h8(data, path),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = {
        "environment": {
            "python": platform.python_version(),
            "os": platform.platform(),
            "cpu": platform.processor(),
            "machine": platform.machine(),
            "max_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "files": {p.name: measure(p) for p in args.paths},
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "output": str(args.output),
            "files": list(result["files"]),
            "sizes": {k: v["bytes"] for k, v in result["files"].items()},
            "sha256": {k: v["sha256"] for k, v in result["files"].items()},
        }, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps({
            "files": list(result["files"]),
            "sizes": {k: v["bytes"] for k, v in result["files"].items()},
            "sha256": {k: v["sha256"] for k, v in result["files"].items()},
        }, sort_keys=True, separators=(",", ":")))

if __name__ == "__main__":
    main()
