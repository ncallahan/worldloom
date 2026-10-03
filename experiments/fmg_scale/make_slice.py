#!/usr/bin/env python3
"""Generate small, self-consistent FMG slices around a burg."""
from __future__ import annotations
import argparse, copy, json
from collections import deque
from pathlib import Path
from typing import Any

from inspect_fmg import check_refs

CORE_CELL_FIELDS = ("burg", "state", "province", "culture", "religion")
COLLECTIONS_WITH_PLACEHOLDER = ("features", "burgs", "provinces")

def _records(values):
    return [(i, x) for i, x in enumerate(values) if isinstance(x, dict)]

def _bfs_cells(cells, start, hops):
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        current, distance = queue.popleft()
        if distance >= hops:
            continue
        for neighbor in cells[current].get("c", []):
            if isinstance(neighbor, int) and 0 <= neighbor < len(cells) and neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, distance + 1))
    return seen

def _first_cell(values, allowed=None):
    for value in values:
        if isinstance(value, int) and value >= 0 and (allowed is None or value in allowed):
            return value
    return None

def _add_cell_from_collection(cell_set, collection, field="cell"):
    for item in collection:
        if not isinstance(item, dict):
            continue
        value = item.get(field)
        if isinstance(value, int) and value >= 0:
            cell_set.add(value)
            return item
    return None

def _remap_list(values, mapping):
    return [mapping[x] for x in values if isinstance(x, int) and x in mapping]

def _compact_records(values, keep_ids, id_base=0):
    out = [id_base - 1 if id_base else 0]
    mapping = {}
    next_id = id_base
    for old_id, item in _records(values):
        if old_id not in keep_ids:
            continue
        clone = copy.deepcopy(item)
        if isinstance(clone.get("i"), int):
            mapping[clone["i"]] = next_id
            clone["i"] = next_id
        out.append(clone)
        next_id += 1
    return out, mapping

def _rewrite_scalar_id(value, mapping, default=None):
    if isinstance(value, int) and value in mapping:
        return mapping[value]
    return default if value is not None else value

def make_slice(data: dict[str, Any], burg_id: int, hops: int) -> dict[str, Any]:
    pack = data["pack"]
    cells = pack["cells"]
    burg = next((x for x in pack["burgs"] if isinstance(x, dict) and x.get("i") == burg_id), None)
    if burg is None:
        raise ValueError(f"burg id {burg_id} not found")
    if hops < 0:
        raise ValueError("hop count must be non-negative")

    cell_ids = _bfs_cells(cells, burg["cell"], hops)

    # Force one route, river, and marker into the slice when possible.
    route = next((r for r in pack.get("routes", []) if isinstance(r, dict) and r.get("points")), None)
    if route:
        cell = next((p[2] for p in route["points"] if isinstance(p, list) and len(p) >= 3 and isinstance(p[2], int)), None)
        if isinstance(cell, int) and 0 <= cell < len(cells):
            cell_ids.add(cell)
    river = next((r for r in pack.get("rivers", []) if isinstance(r, dict) and r.get("cells")), None)
    if river:
        cell = _first_cell(river["cells"])
        if cell is not None and cell < len(cells):
            cell_ids.add(cell)
    marker = next((m for m in pack.get("markers", []) if isinstance(m, dict) and isinstance(m.get("cell"), int)), None)
    if marker and 0 <= marker["cell"] < len(cells):
        cell_ids.add(marker["cell"])

    # Include all pack vertices touched by retained cells and the directly
    # referenced grid cells/vertices. Do not traverse the connected grid graph:
    # adjacency outside the retained set is filtered, keeping the fixture small.
    vertex_ids = {
        v for old in cell_ids
        for v in cells[old].get("v", [])
        if isinstance(v, int)
    }
    grid_cells = data.get("grid", {}).get("cells", [])
    grid_vertices = data.get("grid", {}).get("vertices", [])
    grid_ids = {
        cells[old].get("g") for old in cell_ids
        if isinstance(cells[old].get("g"), int)
    }
    grid_vertex_ids = set()
    for vid in vertex_ids:
        if 0 <= vid < len(pack["vertices"]):
            grid_ids.update(
                v for v in pack["vertices"][vid].get("c", [])
                if isinstance(v, int)
            )
            grid_vertex_ids.update(
                v for v in pack["vertices"][vid].get("v", [])
                if isinstance(v, int)
            )
    grid_ids = {x for x in grid_ids if 0 <= x < len(grid_cells)}
    for gid in list(grid_ids):
        grid_vertex_ids.update(
            v for v in grid_cells[gid].get("v", [])
            if isinstance(v, int)
        )
    grid_vertex_ids = {x for x in grid_vertex_ids if 0 <= x < len(grid_vertices)}


    # References from retained cells determine which burgs and provinces are needed.
    burg_ids = {cells[c].get("burg") for c in cell_ids if isinstance(cells[c].get("burg"), int) and cells[c].get("burg") > 0}
    burg_ids.add(burg_id)
    state_ids = {cells[c].get("state") for c in cell_ids if isinstance(cells[c].get("state"), int) and cells[c].get("state") >= 0}
    state_ids.update(b.get("state") for b in pack["burgs"] if isinstance(b, dict) and b.get("i") in burg_ids and isinstance(b.get("state"), int))

    # Retain the selected state and all of its original neighbors. Keeping all
    # states is still small and preserves diplomacy semantics without inventing
    # a new diplomacy indexing convention.
    states = pack.get("states", [])
    for sid in list(state_ids):
        if isinstance(sid, int) and 0 <= sid < len(states) and isinstance(states[sid], dict):
            state_ids.update(n for n in states[sid].get("neighbors", []) if isinstance(n, int) and 0 <= n < len(states))
    province_ids = {cells[c].get("province") for c in cell_ids if isinstance(cells[c].get("province"), int) and cells[c].get("province") > 0}

    # Add one province for the selected burg if available.
    burg_by_id = {x.get("i"): x for x in pack["burgs"] if isinstance(x, dict) and isinstance(x.get("i"), int)}
    if burg_id in burg_by_id and isinstance(burg_by_id[burg_id].get("province"), int):
        province_ids.add(burg_by_id[burg_id]["province"])

    cell_map = {old: new for new, old in enumerate(sorted(cell_ids))}
    vertex_map = {old: new for new, old in enumerate(sorted(vertex_ids))}
    grid_map = {old: new for new, old in enumerate(sorted(grid_ids))}
    grid_vertex_map = {old: new for new, old in enumerate(sorted(grid_vertex_ids))}

    # Burg IDs retain FMG's placeholder-at-zero / one-based convention.
    kept_burgs = sorted(x for x in burg_ids if isinstance(x, int) and x > 0)
    burg_map = {old: new for new, old in enumerate(kept_burgs, start=1)}

    # Province IDs use the same placeholder/one-based convention.
    kept_provinces = sorted(x for x in province_ids if isinstance(x, int) and x > 0)
    province_map = {old: new for new, old in enumerate(kept_provinces, start=1)}

    out = copy.deepcopy(data)
    if "nameBases" in out:
        out["nameBases"] = {}
    out["pack"]["cells"] = []
    for old in sorted(cell_ids):
        item = copy.deepcopy(cells[old])
        item["i"] = cell_map[old]
        item["c"] = _remap_list(item.get("c", []), cell_map)
        item["v"] = _remap_list(item.get("v", []), vertex_map)
        if isinstance(item.get("g"), int):
            item["g"] = grid_map[item["g"]]
        for field, mapping in (("burg", burg_map), ("province", province_map)):
            if field in item:
                item[field] = mapping.get(item[field], 0)
        # State/culture/religion IDs remain stable because those collections
        # are retained in full.
        if "river" in item and river and item["river"] != river.get("i"):
            item.pop("river")
        if "routes" in item and route:
            item["routes"] = [route.get("i")] if route.get("i") in item.get("routes", []) else []
        out["pack"]["cells"].append(item)

    out["pack"]["vertices"] = []
    for old in sorted(vertex_ids):
        item = copy.deepcopy(pack["vertices"][old])
        item["i"] = vertex_map[old]
        item["v"] = _remap_list(item.get("v", []), grid_vertex_map)
        item["c"] = _remap_list(item.get("c", []), grid_map)
        out["pack"]["vertices"].append(item)

    out["pack"]["burgs"] = [0]
    for old in kept_burgs:
        item = copy.deepcopy(burg_by_id[old])
        item["i"] = burg_map[old]
        item["cell"] = cell_map[item["cell"]]
        if isinstance(item.get("province"), int):
            item["province"] = province_map.get(item["province"], 0)
        out["pack"]["burgs"].append(item)

    out["pack"]["provinces"] = [0]
    provinces = {x.get("i"): x for x in pack.get("provinces", []) if isinstance(x, dict) and isinstance(x.get("i"), int)}
    for old in kept_provinces:
        item = copy.deepcopy(provinces[old])
        item["i"] = province_map[old]
        if isinstance(item.get("state"), int):
            item["state"] = item["state"]
        if isinstance(item.get("center"), int):
            item["center"] = cell_map.get(item["center"], next(iter(cell_map.values())))
        if isinstance(item.get("burgs"), list):
            item["burgs"] = [burg_map[x] for x in item["burgs"] if x in burg_map]
        out["pack"]["provinces"].append(item)

    # Keep all states so diplomacy and neighbor lists remain semantically indexed.
    out["pack"]["states"] = copy.deepcopy(states)
    for item in out["pack"]["states"]:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("provinces"), list):
            item["provinces"] = [province_map[x] for x in item["provinces"] if x in province_map]
        if isinstance(item.get("military"), list):
            item["military"] = [u for u in item["military"] if isinstance(u, dict) and u.get("cell") in cell_map]

    # Scope-excluded high-volume collections are represented as empty collections
    # in the slice; their inclusion is an owner decision, not silently preserved.
    for name in ("markets", "deals", "journeys", "measurers"):
        if name in pack and isinstance(pack[name], list):
            out["pack"][name] = []

    # Keep small reference collections intact; filter spatial collections.
    for name in ("features", "biomes", "cultures", "religions", "goods"):
        if name in pack:
            out["pack"][name] = copy.deepcopy(pack[name])

    if river:
        out["pack"]["rivers"] = [copy.deepcopy(river)]
        out["pack"]["rivers"][0]["cells"] = [cell_map[x] for x in river.get("cells", []) if x in cell_map or x == -1]
    else:
        out["pack"]["rivers"] = []

    if route:
        out["pack"]["routes"] = [copy.deepcopy(route)]
        out["pack"]["routes"][0]["points"] = [
            [p[0], p[1], cell_map[p[2]]]
            for p in route.get("points", [])
            if isinstance(p, list) and len(p) >= 3 and p[2] in cell_map
        ]
    else:
        out["pack"]["routes"] = []

    if marker:
        m = copy.deepcopy(marker)
        m["cell"] = cell_map[m["cell"]]
        out["pack"]["markers"] = [m]
    else:
        out["pack"]["markers"] = []

    out["pack"]["zones"] = [
        dict(z, cells=[cell_map[x] for x in z.get("cells", []) if x in cell_map])
        for z in pack.get("zones", [])
        if isinstance(z, dict) and any(x in cell_map for x in z.get("cells", []))
    ]

    grid = out["grid"]
    grid["cells"] = []
    for old in sorted(grid_ids):
        item = copy.deepcopy(data["grid"]["cells"][old])
        item["i"] = grid_map[old]
        if isinstance(item.get("v"), list):
            item["v"] = _remap_list(item["v"], grid_vertex_map)
        if isinstance(item.get("c"), list):
            item["c"] = _remap_list(item["c"], grid_map)
        grid["cells"].append(item)

    grid["vertices"] = []
    for old in sorted(grid_vertex_ids):
        item = copy.deepcopy(grid_vertices[old])
        item["i"] = grid_vertex_map[old]
        if isinstance(item.get("v"), list):
            item["v"] = _remap_list(item["v"], grid_vertex_map)
        if isinstance(item.get("c"), list):
            item["c"] = _remap_list(item["c"], grid_map)
        grid["vertices"].append(item)

    out["_worldloom_slice"] = {
        "source_burg_id": burg_id,
        "hop_count": hops,
        "cell_map": {str(k): v for k, v in sorted(cell_map.items())},
        "vertex_map": {str(k): v for k, v in sorted(vertex_map.items())},
        "grid_cell_map": {str(k): v for k, v in sorted(grid_map.items())},
        "grid_vertex_map": {str(k): v for k, v in sorted(grid_vertex_map.items())},
        "burg_map": {str(k): v for k, v in sorted(burg_map.items())},
        "province_map": {str(k): v for k, v in sorted(province_map.items())},
        "excluded_collections": ["markets", "deals", "journeys", "measurers"],
        "excluded_top_level": ["nameBases"],
        "notes": ["Mappings are diagnostic provenance for this derived experiment fixture, not importer identifiers."],
    }
    return out

def verify_slice(data):
    refs = check_refs(data)
    failures = {
        k: v for k, v in refs.items()
        if v["oob"] and k not in {"vertices.v.vs_pack_vertices", "vertices.c.vs_pack_cells"}
    }
    if failures:
        raise ValueError(f"reference-integrity failure: {failures}")
    return refs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("burg_id", type=int)
    ap.add_argument("hops", type=int)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    result = make_slice(data, args.burg_id, args.hops)
    refs = verify_slice(result)
    size_breakdown = {
        key: len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        for key, value in result.get("pack", {}).items()
    }
    size_breakdown["<top-level>"] = sum(
        len(json.dumps(result.get(key), ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        for key in result if key != "pack"
    )
    print(json.dumps({"size_breakdown": dict(sorted(size_breakdown.items(), key=lambda x: x[1], reverse=True)[:12])}, separators=(",", ":")))
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    size = len(text.encode("utf-8"))
    if size >= 100_000:
        raise SystemExit(f"slice exceeds 100 KB: {size} bytes; reduce hop count")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "bytes": size,
        "cells": len(result["pack"]["cells"]),
        "vertices": len(result["pack"]["vertices"]),
        "grid_cells": len(result["grid"]["cells"]),
        "burgs": len(result["pack"]["burgs"]) - 1,
        "provinces": len(result["pack"]["provinces"]) - 1,
        "states": len([x for x in result["pack"]["states"] if isinstance(x, dict)]),
        "refs_checked": len(refs),
        "all_refs_in_range": not any(v["oob"] for v in refs.values()),
    }, separators=(",", ":")))

if __name__ == "__main__":
    main()
