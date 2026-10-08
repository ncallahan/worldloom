"""Enforce the source-only Radon cyclomatic-complexity ratchet."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from complexity_measurement import measure_functions


def _load_baseline(path: Path) -> dict[str, Any]:
    baseline = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(baseline, dict) or not isinstance(baseline.get("threshold"), int):
        raise ValueError("baseline must contain an integer threshold")
    if not isinstance(baseline.get("functions"), dict):
        raise ValueError("baseline must contain a functions object")
    for key, value in baseline["functions"].items():
        if not isinstance(key, str) or not isinstance(value, int) or value <= baseline["threshold"]:
            raise ValueError(f"invalid baseline entry: {key!r}: {value!r}")
    return baseline


def _key(item: dict[str, Any]) -> str:
    return f"{item['file']}::{item['qualified_name']}"


def evaluate(root: Path, baseline_path: Path) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    baseline = _load_baseline(baseline_path)
    threshold = baseline["threshold"]
    measured = measure_functions(root)
    by_key = {_key(item): item for item in measured}
    entries = baseline["functions"]
    violations: list[str] = []
    rows: list[dict[str, Any]] = []

    for item in measured:
        key = _key(item)
        cc = item["complexity"]
        allowed = entries.get(key, threshold)
        rows.append({**item, "key": key, "allowed": allowed})
        if key in entries:
            if cc > allowed:
                violations.append(f"Rule 2: {key} ({item['file']}, CC {cc}, allowed CC {allowed}) — reduce complexity.")
            elif cc < allowed:
                violations.append(f"Rule 3: {key} ({item['file']}, CC {cc}, allowed CC {allowed}) — lower the baseline entry to {cc}; remove it if CC <= {threshold}.")
        elif cc > threshold:
            violations.append(f"Rule 1: {key} ({item['file']}, CC {cc}, allowed CC {threshold}) — reduce complexity, or request explicit owner approval in the PR description to add a baseline entry.")

    for key, allowed in entries.items():
        if key not in by_key:
            violations.append(f"Rule 4: {key} (function missing, measured CC unavailable, allowed CC {allowed}) — remove or re-key the entry; moved/renamed functions count as new functions unless re-keyed in this PR.")

    return rows, sorted(violations), baseline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=Path("scripts/complexity_baseline.json"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--write-candidate", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    baseline_path = args.baseline if args.baseline.is_absolute() else root / args.baseline
    rows, violations, baseline = evaluate(root, baseline_path)
    threshold = baseline["threshold"]
    candidate = {
        "threshold": threshold,
        "functions": {
            row["key"]: row["complexity"]
            for row in rows if row["complexity"] > threshold
        },
    }
    if args.write_candidate:
        args.write_candidate.parent.mkdir(parents=True, exist_ok=True)
        args.write_candidate.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Function complexity ratchet")
    for row in rows:
        if row["key"] in baseline["functions"]:
            print(f"BASELINED {row['key']}: current CC {row['complexity']}, allowed CC {row['allowed']}")
    if violations:
        print("VIOLATIONS")
        for violation in violations:
            print(f"- {violation}")
        return 1
    print("No complexity ratchet violations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
