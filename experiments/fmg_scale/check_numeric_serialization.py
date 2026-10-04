#!/usr/bin/env python3
"""Bounded check for integral-valued JSON floats in canonical FMG exports."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def walk(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)
    elif isinstance(value, float):
        yield value

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    args = ap.parse_args()
    for path in args.paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        floats = [x for x in walk(data)]
        integral = sum(x.is_integer() for x in floats)
        print(f"{path.name}: floats={len(floats)} integral-valued-floats={integral}")

if __name__ == "__main__":
    main()
