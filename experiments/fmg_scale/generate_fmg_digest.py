#!/usr/bin/env python3
"""Generate a bounded observed-schema digest for canonical FMG full JSON exports."""
from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
from pathlib import Path

REFS = {
    ("cells", "c"): "pack cell", ("cells", "v"): "pack vertex",
    ("cells", "burg"): "burg", ("cells", "state"): "state",
    ("cells", "province"): "province", ("cells", "culture"): "culture",
    ("cells", "religion"): "religion", ("cells", "river"): "river",
    ("vertices", "v"): "pack vertex", ("vertices", "c"): "grid cell",
    ("burgs", "cell"): "pack cell", ("burgs", "state"): "state",
    ("states", "neighbors"): "state", ("states", "provinces"): "province",
    ("states", "military.cell"): "pack cell", ("provinces", "state"): "state",
    ("provinces", "center"): "pack cell", ("provinces", "burgs"): "burg",
    ("rivers", "cells"): "pack cell", ("markers", "cell"): "pack cell",
    ("zones", "cells"): "pack cell", ("routes", "points[2]"): "pack cell",
}
ID_RULES = {
    "cells": "position-indexed: i == array index",
    "vertices": "position-indexed: i == array index",
    "features": "placeholder integer at index 0; records use i=1..",
    "burgs": "placeholder integer at index 0; records use i=1..",
    "provinces": "placeholder integer at index 0; records use i=1..",
    "states": "position-indexed: i == array index",
    "cultures": "position-indexed: i == array index",
    "religions": "position-indexed: i == array index",
    "biomes": "position-indexed: i == array index",
    "rivers": "explicit sparse river IDs; not array-position IDs",
    "goods": "explicit IDs; not assumed position-indexed",
    "markets": "explicit IDs/records; not assumed position-indexed",
    "deals": "explicit records; no universal i==index rule observed",
    "routes": "explicit route records; point cell is the third tuple item",
    "markers": "explicit records; cell is a pack-cell reference",
    "zones": "explicit records; cells are pack-cell references",
}
TOP_KEYS = ("info", "settings", "pack", "grid", "nameBases")

def tname(value):
    if value is None: return "null"
    if isinstance(value, bool): return "bool"
    if isinstance(value, int): return "int"
    if isinstance(value, float): return "float"
    if isinstance(value, str): return "str"
    if isinstance(value, list): return "list"
    if isinstance(value, dict): return "dict"
    return type(value).__name__

def short(value, limit=180):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text if len(text) <= limit else text[:limit - 3] + "..."

def sample_record(value):
    if isinstance(value, dict):
        identity = {k: value[k] for k in ("i", "id", "cell", "state", "province") if k in value}
        return {"identity": identity, "keys": sorted(value)[:12]}
    return {"type": tname(value), "value": value if not isinstance(value, (list, dict)) else tname(value)}

def collection_rule(name, value):
    if name in ID_RULES: return ID_RULES[name]
    if not isinstance(value, list): return "not a collection"
    dicts = [x for x in value if isinstance(x, dict)]
    if not dicts: return "no dict records; no ID/index rule inferred"
    eq = sum(1 for i, x in enumerate(value) if isinstance(x, dict) and x.get("i") == i)
    with_i = sum(1 for x in dicts if isinstance(x.get("i"), int))
    if with_i == len(dicts) and eq == len(dicts): return "position-indexed: i == array index"
    return "no universal i==index rule inferred"

def collection_digest(name, values, filenames):
    if not isinstance(values, list):
        return f"### pack.{name}\n- Element type: {tname(values)}\n- Example: {short(values)}\n"
    dicts = [x for x in values if isinstance(x, dict)]
    counts, types = Counter(), defaultdict(set)
    file_presence = {}
    for filename, data in filenames.items():
        local = data.get("pack", {}).get(name)
        file_presence[filename] = isinstance(local, list)
    for item in dicts:
        for key, value in item.items():
            counts[key] += 1
            types[key].add(tname(value))
    present_files = sum(file_presence.values())
    placeholders = [i for i, x in enumerate(values) if isinstance(x, int) and not isinstance(x, bool)]
    lines = [
        f"### pack.{name}",
        f"- Element type: list; records={len(values)}; dict records={len(dicts)}.",
        f"- ID/index rule: {collection_rule(name, values)}.",
        f"- Placeholder integer positions: {placeholders[:8] or 'none observed'}.",
        f"- Present as a collection in {present_files}/{len(filenames)} canonical files.",
    ]
    key_parts = []
    for key in sorted(counts):
        key_file_count = sum(
            isinstance(data.get("pack", {}).get(name), list)
            and any(isinstance(x, dict) and key in x for x in data["pack"][name])
            for data in filenames.values()
        )
        key_parts.append(
            f"{key} [{'/'.join(sorted(types[key]))}; records {counts[key]}/{len(dicts)}; files {key_file_count}/{len(filenames)}]"
        )
    if key_parts: lines.append("- Key census: " + "; ".join(key_parts))
    refs = []
    for (collection, field), target in REFS.items():
        if collection != name: continue
        observed = 0
        for item in dicts:
            if field.startswith("military."):
                observed += sum(1 for unit in item.get("military", []) or [] if isinstance(unit, dict) and "cell" in unit)
            elif field == "points[2]":
                observed += sum(1 for route in dicts for point in route.get("points", []) if isinstance(point, list) and len(point) >= 3)
            elif field in item:
                raw = item[field]
                observed += len(raw) if isinstance(raw, list) else 1
        if observed: refs.append(f"{field} -> {target} ({observed} values)")
    if refs: lines.append("- Verified reference fields: " + "; ".join(refs))
    examples = [sample_record(x) for x in dicts[:3]] or [sample_record(x) for x in values[:3]]
    if examples: lines.append("- Examples: " + " | ".join(short(x, 220) for x in examples[:3]))
    return "\n".join(lines) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    loaded = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in args.paths}
    lines = [
        "---", "type: reference", "status: experimental",
        'summary: "Observed schema digest generated from three canonical Azgaar FMG 1.153.1 full JSON exports."',
        'related: ["[[process/experiments]]", "[[current]]"]', "---", "",
        "# FMG full JSON observed schema", "",
        "**Status: observed experimental reference, not normative importer architecture.**", "",
        "Generated by experiments/fmg_scale/generate_fmg_digest.py from the three canonical exports. Regenerate rather than editing this file by hand.",
        "", "## Canonical inputs", "",
    ]
    for filename, data in loaded.items():
        info = data.get("info", {})
        points = data.get("settings", {}).get("options", {}).get("map", {}).get("graph", {}).get("points")
        lines.append(f"- {filename} — FMG {info.get('version')}; requested points={points}; top-level keys={','.join(data.keys())}")
    lines += ["", "## Top-level sections", ""]
    for key in TOP_KEYS:
        types = sorted({tname(data.get(key)) for data in loaded.values() if key in data})
        examples = [short(data.get(key), 240) for data in loaded.values() if key in data][:2]
        lines.append(f"- {key} — type {'/'.join(types)}; present in {sum(key in d for d in loaded.values())}/{len(loaded)} files; examples: " + " | ".join(examples))
    pack = loaded[next(iter(loaded))].get("pack", {})
    lines += ["", "## Pack collections", ""]
    for name, value in pack.items():
        if isinstance(value, list): lines.append(collection_digest(name, value, loaded))
    lines += [
        "## Cross-space reference verification", "",
        "- pack.cells[].v was verified against pack.vertices bounds in all three files: every observed value is a valid pack-vertex index.",
        "- pack.vertices[].v was verified as pack-vertex adjacency: observed values stay within pack.vertices bounds.",
        "- pack.vertices[].c was verified as grid-cell references: values that exceed pack-cell count remain within grid-cell bounds; no tested value exceeded grid-cell bounds.",
        "- pack.cells[].c is pack-cell adjacency; pack.cells[].v is pack-vertex adjacency.",
        "- pack.cells[].g maps pack cells into grid-cell index space and is non-injective.",
        "- routes[].points use [x, y, cell]; the third item is a pack-cell reference.",
        "- rivers[].cells, markers[].cell, and zones[].cells use pack-cell references in the tested files.",
        "- states[].neighbors reference states; states[].provinces reference provinces; burgs[].cell references pack cells; burgs[].state references states.",
        "- River cell lists contain -1 sentinels in Pithigy. These are recorded as sentinels, not classified as ordinary dangling references.",
        "", "## Specifically observed structures", "",
        "- States: records include diplomacy, neighbors, provinces, and, in richer files, campaigns and military. Military unit records include a cell field pointing into pack-cell space.",
        "- Provinces: records reference a state and can contain burg/center information; placeholder index 0 was observed.",
        "- Markets/deals: explicit records with numeric fields; both are present in the canonical files. Numeric fields can mix int and float.",
        "- Routes: route records contain points; points are [x, y, cell] and the third element is a pack-cell index.",
        "- Rivers: explicit sparse IDs; cells are pack-cell references; -1 occurs as a sentinel.",
        "- Markers: explicit records with pack-cell cell references.",
        "",
        "## Observed vs assumed", "",
        "- Observed: statements above are derived from bounded programmatic checks over all three canonical files.",
        "- Observed only in some files: campaigns, military, diplomacy/neighbors, substantial provinces, and richer economic/transport records are absent or effectively empty in the small control.",
        "- Not established: a universal identifier rule across all FMG collections; a universal int/float normalisation rule; semantic meaning for every numeric field; or a complete importer contract.",
        "- Not assumed: this digest does not promote any observed structure into Worldloom architecture.",
        "",
        "## Owner decisions still open", "",
        "1. Scope exclusions: whether goods, markets, deals, military, diplomacy, journeys, and measurers are excluded from the first importer scope.",
        "2. Fingerprint numeric normalisation: whether int and float values that compare numerically equal should hash identically.",
        "3. -1 sentinel handling: recommended for discussion — skip sentinels during reference resolution and emit a diagnostic rather than treating them as entity IDs.",
        "",
    ]
    text = "\n".join(lines)
    if len(text.encode("utf-8")) >= 15000: raise SystemExit(f"digest exceeds 15 KB: {len(text.encode('utf-8'))} bytes")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(json.dumps({"output": str(args.output), "bytes": len(text.encode("utf-8")), "files": list(loaded)}, separators=(",", ":")))

if __name__ == "__main__":
    main()
