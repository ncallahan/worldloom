#!/usr/bin/env python3
"""Bounded inspector for Azgaar FMG full JSON exports.

Never prints raw records. All sample output is capped at five entries and
summaries contain counts, hashes, keys, types, and bounded examples.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter, defaultdict
from pathlib import Path

def tname(v):
    if v is None: return "null"
    if isinstance(v, bool): return "bool"
    if isinstance(v, int): return "int"
    if isinstance(v, float): return "float"
    if isinstance(v, str): return "str"
    if isinstance(v, list): return "list"
    if isinstance(v, dict): return "dict"
    return type(v).__name__

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def bounded(v, n=5):
    if isinstance(v, list):
        return v[:n]
    if isinstance(v, dict):
        return {k: v[k] for k in list(v)[:n]}
    return v

def collection_summary(name, value):
    if not isinstance(value, list):
        print(f"{name}: type={tname(value)}")
        return
    dicts = [x for x in value if isinstance(x, dict)]
    ints = [i for i, x in enumerate(value) if isinstance(x, int) and not isinstance(x, bool)]
    nulls = [i for i, x in enumerate(value) if x is None]
    ids = [x.get("i") for x in dicts if isinstance(x.get("i"), int)]
    eq = sum(1 for i, x in enumerate(value) if isinstance(x, dict) and x.get("i") == i)
    print(f"{name}: count={len(value)} dict={len(dicts)} i_eq_index={eq} "
          f"bare_int_positions={ints[:5]} null_positions={nulls[:5]}")
    if ids:
        print(f"  i_range=[{min(ids)},{max(ids)}] unique_i={len(set(ids))}")
    keys = Counter()
    types = defaultdict(set)
    for x in dicts:
        for k, v in x.items():
            keys[k] += 1
            types[k].add(tname(v))
    print("  keys=" + ", ".join(
        f"{k}:{keys[k]}/{len(dicts)}:{'/'.join(sorted(types[k]))}"
        for k in sorted(keys)
    ))

def check_refs(data):
    pack = data["pack"]
    pc, pv = len(pack["cells"]), len(pack["vertices"])
    checks = []
    def add(label, values, limit):
        vals = [v for v in values if isinstance(v, int)]
        bad = [v for v in vals if v < 0 or v >= limit]
        checks.append((label, len(vals), len(bad), bounded(bad)))
    cells = pack["cells"]
    add("cells.c", (z for x in cells for z in x.get("c", [])), pc)
    add("cells.v", (z for x in cells for z in x.get("v", [])), pv)
    for field, coll in (("burg", "burgs"), ("state", "states"),
                        ("province", "provinces"), ("culture", "cultures"),
                        ("religion", "religions")):
        add(f"cells.{field}", (x.get(field) for x in cells), len(pack[coll]))
    add("burgs.cell", (x.get("cell") for x in pack["burgs"] if isinstance(x, dict)), pc)
    add("burgs.state", (x.get("state") for x in pack["burgs"] if isinstance(x, dict)),
        len(pack["states"]))
    add("states.neighbors", (z for x in pack["states"] if isinstance(x, dict)
                             for z in x.get("neighbors", [])), len(pack["states"]))
    add("states.provinces", (z for x in pack["states"] if isinstance(x, dict)
                             for z in x.get("provinces", [])), len(pack["provinces"]))
    add("rivers.cells", (z for x in pack["rivers"] if isinstance(x, dict)
                         for z in x.get("cells", [])), pc)
    add("markers.cell", (x.get("cell") for x in pack["markers"] if isinstance(x, dict)), pc)
    add("zones.cells", (z for x in pack["zones"] if isinstance(x, dict)
                        for z in x.get("cells", [])), pc)
    add("vertices.c", (z for x in pack["vertices"] if isinstance(x, dict)
                       for z in x.get("c", [])), pc)
    for label,total,bad,examples in checks:
        print(f"{label}: refs={total} oob={bad} examples={examples}")
    route_cells = [pt[2] for r in pack["routes"] if isinstance(r, dict)
                   for pt in r.get("points", []) if isinstance(pt, list) and len(pt) >= 3
                   and isinstance(pt[2], int)]
    print(f"routes.points.cell: refs={len(route_cells)} "
          f"oob={sum(x < 0 or x >= pc for x in route_cells)} "
          f"examples={[x for x in route_cells if x < 0 or x >= pc][:5]}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--collection")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--check", choices=["refs"])
    args = ap.parse_args()
    if args.sample < 0 or args.sample > 5:
        ap.error("--sample must be between 0 and 5")
    data = load(args.path)
    print(f"file={args.path.name} bytes={args.path.stat().st_size} sha256={sha256(args.path)}")
    if args.summary:
        info = data.get("info", {})
        print("info=" + json.dumps({k: info.get(k) for k in
              ("version","mapName","width","height","seed","mapId")}, sort_keys=True))
        print("top_keys=" + ",".join(data.keys()))
        for k, v in data.get("pack", {}).items():
            collection_summary("pack."+k, v)
        for k, v in data.get("grid", {}).items():
            if isinstance(v, list):
                collection_summary("grid."+k, v)
            else:
                print(f"grid.{k}: type={tname(v)}")
    if args.collection:
        cur = data
        for part in args.collection.split("."):
            cur = cur[part]
        collection_summary(args.collection, cur)
        if args.sample:
            if isinstance(cur, list):
                for i, item in enumerate(cur[:args.sample]):
                    if isinstance(item, dict):
                        print(f"sample[{i}]: keys={','.join(sorted(item))}")
                    else:
                        print(f"sample[{i}]: type={tname(item)} value={bounded(item)}")
            else:
                print("sample: type=" + tname(cur) + " keys=" +
                      (",".join(sorted(cur)) if isinstance(cur, dict) else ""))
    if args.check == "refs":
        check_refs(data)

if __name__ == "__main__":
    main()
