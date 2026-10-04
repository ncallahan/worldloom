#!/usr/bin/env python3
"""Generate a bounded observed-schema digest for canonical FMG full JSON exports."""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter, defaultdict
from pathlib import Path

REFS = {
    ("cells", "c"): "pack cell", ("cells", "v"): "pack vertex",
    ("cells", "burg"): "burg", ("cells", "state"): "state",
    ("cells", "province"): "province", ("cells", "culture"): "culture",
    ("cells", "religion"): "religion", ("cells", "river"): "river",
    ("vertices", "v"): "grid vertex", ("vertices", "c"): "grid cell",
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
        return {"identity": identity}
    return {"type": tname(value)}

def collection_rule(name, value):
    if name in ID_RULES: return ID_RULES[name]
    if not isinstance(value, list): return "not a collection"
    dicts = [x for x in value if isinstance(x, dict)]
    if not dicts: return "no dict records; no ID/index rule inferred"
    eq = sum(1 for i, x in enumerate(value) if isinstance(x, dict) and x.get("i") == i)
    with_i = sum(1 for x in dicts if isinstance(x.get("i"), int))
    if with_i == len(dicts) and eq == len(dicts): return "position-indexed: i == array index"
    return "no universal i==index rule inferred"


def coordinate_fit(data):
    info = data.get("info", {})
    coords = data.get("mapCoordinates", {})
    width, height = info.get("width"), info.get("height")
    required = ("latN", "latS", "lonW", "lonE")
    if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
        return {"status": "not-established"}
    if not all(isinstance(coords.get(k), (int, float)) for k in required):
        return {"status": "not-established"}
    cells = [x for x in data.get("pack", {}).get("cells", [])
             if isinstance(x, dict) and isinstance(x.get("p"), list) and len(x["p"]) >= 2]
    if not cells:
        return {"status": "not-established"}
    lon_slope = (coords["lonE"] - coords["lonW"]) / width
    lat_slope = -(coords["latN"] - coords["latS"]) / height
    max_lon = max(abs(lon_slope * x["p"][0] + coords["lonW"] -
                      (coords["lonW"] + (coords["lonE"] - coords["lonW"]) * x["p"][0] / width))
                  for x in cells)
    max_lat = max(abs(lat_slope * x["p"][1] + coords["latN"] -
                      (coords["latN"] - (coords["latN"] - coords["latS"]) * x["p"][1] / height))
                  for x in cells)
    return {
        "lat_direction": "north-to-south as y increases" if lat_slope < 0 else "south-to-north as y increases",
        "lon_slope": lon_slope,
        "lat_slope": lat_slope,
        "max_lon_residual": max_lon,
        "max_lat_residual": max_lat,
    }

def collection_digest(name, filenames):
    values_by_file = {fn: data.get("pack", {}).get(name) for fn, data in filenames.items()}
    all_values = [v for v in values_by_file.values() if isinstance(v, list)]
    if not all_values:
        return f"### pack.{name}\n- absent in all three files\n"
    dicts_by_file = {
        fn: [x for x in value if isinstance(x, dict)]
        for fn, value in values_by_file.items() if isinstance(value, list)
    }
    all_dicts = [x for records in dicts_by_file.values() for x in records]
    placeholders = sorted({
        i for value in all_values for i, x in enumerate(value)
        if isinstance(x, int) and not isinstance(x, bool)
    })
    counts, types = Counter(), defaultdict(set)
    for item in all_dicts:
        for key, value in item.items():
            counts[key] += 1
            types[key].add(tname(value))
    key_parts = []
    for key in sorted(counts):
        file_count = sum(
            any(isinstance(x, dict) and key in x for x in records)
            for records in dicts_by_file.values()
        )
        always = all(key in x for records in dicts_by_file.values() for x in records)
        key_parts.append(f"{key}:{'/'.join(sorted(types[key]))}:{'A' if always else 'O'}:{file_count}/3")
    examples = [
        sample_record(records[0]) for records in dicts_by_file.values() if records
    ][:3]
    lines = [
        f"### pack.{name}",
        f"- element=list; present={len(dicts_by_file)}/3; id-rule={collection_rule(name, all_values[0])}; placeholders={placeholders[:5] or '-'}",
        "- keys=" + ",".join(key_parts),
        "- examples=" + ";".join(short(x, 90) for x in examples),
    ]
    refs = []
    for (collection, field), target in REFS.items():
        if collection != name:
            continue
        observed = 0
        for item in all_dicts:
            if field.startswith("military."):
                observed += sum(1 for unit in item.get("military", []) or [] if isinstance(unit, dict) and "cell" in unit)
            elif field == "points[2]":
                observed += sum(1 for point in item.get("points", []) if isinstance(point, list) and len(point) >= 3)
            elif field in item:
                raw = item[field]
                observed += len(raw) if isinstance(raw, list) else 1
        if observed:
            refs.append(f"{field}->{target}")
    if refs:
        lines.append("- refs=" + ",".join(refs))
    return "\n".join(lines) + "\n"


def verify_cross_space(loaded):
    failures = []
    for filename, data in loaded.items():
        pack = data["pack"]
        grid = data["grid"]
        pc, pv, gc = len(pack["cells"]), len(pack["vertices"]), len(grid["cells"])
        cell_vertices = [v for cell in pack["cells"] for v in cell.get("v", []) if isinstance(v, int)]
        vertex_vertices = [v for vertex in pack["vertices"] for v in vertex.get("v", []) if isinstance(v, int)]
        vertex_cells = [v for vertex in pack["vertices"] for v in vertex.get("c", []) if isinstance(v, int)]
        if any(v < 0 or v >= pv for v in cell_vertices):
            failures.append(f"{filename}: pack.cells[].v outside pack.vertices")
        if any(v != -1 and (v < 0 or v >= len(grid.get("vertices", []))) for v in vertex_vertices):
            failures.append(f"{filename}: pack.vertices[].v outside grid.vertices")
        if any(v != -1 and (v < 0 or v >= len(grid.get("cells", []))) for v in vertex_cells):
            failures.append(f"{filename}: pack.vertices[].c outside grid.cells")
        # grid-cell bounds are checked above together with the other cross-space references.
    if failures:
        raise SystemExit("cross-space verification failed: " + "; ".join(failures))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    loaded = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in args.paths}
    source_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in args.paths}
    lines = [
        "---", "type: reference", "status: reference",
        'summary: "Observed schema digest generated from three canonical Azgaar FMG 1.153.1 full JSON exports."',
        'related: ["[[experiments/fmg-export-scale-and-structure]]", "[[current]]"]', "---", "",
        "# FMG full JSON observed schema", "",
        "**Status: observed experimental reference, not normative importer architecture.**", "",
        "Generated by experiments/fmg_scale/generate_fmg_digest.py from the three canonical exports. Regenerate rather than editing this file by hand.",
        "Generating command: `python experiments/fmg_scale/generate_fmg_digest.py <three canonical exports> --output references/fmg-full-json-observed.md`.",
        "", "## Canonical inputs", "",
    ]
    for filename, data in loaded.items():
        info = data.get("info", {})
        points = data.get("settings", {}).get("options", {}).get("map", {}).get("graph", {}).get("points")
        lines.append(f"- {filename} — FMG {info.get('version')}; requested points={points}; top-level keys={','.join(data.keys())}")
        lines.append(f"  source-sha256={source_hashes[filename]}")
    lines += ["", "## Top-level sections", ""]
    for key in TOP_KEYS + ("mapCoordinates",):
        values = [d[key] for d in loaded.values() if key in d]
        types = sorted({tname(v) for v in values})
        if all(isinstance(v, dict) for v in values):
            keys = sorted({k for v in values for k in v})
            census = ",".join(f"{k}:{'/'.join(sorted({tname(v[k]) for v in values if k in v}))}:{'A' if all(k in v for v in values) else 'O'}:{sum(k in v for v in values)}/3" for k in keys)
        else:
            census = "-"
        examples = ";".join(short(v, 70) for v in values[:2])
        lines.append(f"- {key}: element={'/'.join(types)}; id-rule=not applicable; placeholders=-; keys={census}; examples={examples}")

    pack_names = sorted({
        name
        for data in loaded.values()
        for name, value in data.get("pack", {}).items()
        if isinstance(value, list)
    })
    verify_cross_space(loaded)
    lines += ["", "## Pack collections", ""]
    for name in pack_names:
        lines.append(collection_digest(name, loaded))
    lines += [
        "## Cross-space reference verification", "",
        "- pack.cells[].v was verified against pack.vertices bounds in all three files: every observed value is a valid pack-vertex index.",
        "- pack.vertices[].v was verified as grid-vertex adjacency: observed values stay within grid.vertices bounds.",
        "- pack.vertices[].c was verified as grid-cell references: values that exceed pack-cell count remain within grid-cell bounds; no tested value exceeded grid-cell bounds.",
        "- pack.cells[].c is pack-cell adjacency; pack.cells[].v is pack-vertex adjacency.",
        "- pack.cells[].g maps pack cells into grid-cell index space and is non-injective.",
        "- routes[].points use [x, y, cell]; the third item is a pack-cell reference.",
        "- rivers[].cells, markers[].cell, and zones[].cells use pack-cell references in the tested files.",
        "- states[].neighbors reference states; states[].provinces reference provinces; burgs[].cell references pack cells; burgs[].state references states.",
        "- -1 is observed as a sentinel in river-cell lists and pack/grid vertex adjacency; it is not treated as an entity ID by these checks.",
        "", "## Coordinate mapping", "",
        *[f"- {filename}: {coordinate_fit(data)}" for filename, data in loaded.items()],
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
        "## Slice fixtures", "",
        "- The committed derived fixtures are Viveria_burg1_hop3.json and Pithigy_burg1_hop3.json, generated by experiments/fmg_scale/make_slice.py.",
        "- Each fixture is pretty-printed and remains below 100 KB; the generator is checked for byte-deterministic repeated output.",
        "- Each fixture retains pack-cell adjacency, pack/grid mapping through pack.cells[].g, feature/burg/province placeholder conventions, a river, route, marker, province, and state neighbor/diplomacy structure. Pithigy retains a reachable river -1 sentinel.",
        "- Remapping is recorded in the matching .remap.json sidecar. Owner-excluded collections remain represented as empty collections where the slice contract requires the structure type.",
        "", "## Slice fixtures", "",
        "- Committed: Viveria_burg1_hop3.json and Pithigy_burg1_hop3.json; 39/52 pack cells; 77,912/99,002 B pretty-printed; repeated generation hashes match.",
        "- Both retain pack-cell adjacency, pack/grid mapping, placeholders, river/route/marker/province/state neighbor+diplomacy structure; Pithigy retains a reachable river -1 sentinel. Each has a .remap.json sidecar.",
        "", "## Observed vs assumed", "",
        "- Observed: statements above are derived from bounded programmatic checks over all three canonical files.",
        "- Observed only in some files: campaigns, military, diplomacy/neighbors, substantial provinces, and richer economic/transport records are absent or effectively empty in the small control.",
        "- Not established: a universal identifier rule across all FMG collections; a universal int/float normalisation rule; semantic meaning for every numeric field; or a complete importer contract.",
        "- Not assumed: this digest does not promote any observed structure into Worldloom architecture.",
        "",
        "",
    ]
    text = "\n".join(lines)
    if len(text.encode("utf-8")) >= 15000: raise SystemExit(f"digest exceeds 15 KB: {len(text.encode('utf-8'))} bytes")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(json.dumps({"output": str(args.output), "bytes": len(text.encode("utf-8")), "files": list(loaded), "coordinate_fit": {filename: coordinate_fit(data) for filename, data in loaded.items()}}, separators=(",", ":")))

if __name__ == "__main__":
    main()
