"""Measurement-only analysis of raw Azgaar FMG exports.

No importer is used; all absent or malformed input is reported rather than fatal.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

POP_FIELDS = {
    "cells.pop": ("cells", "pop"),
    "burgs.population": ("burgs", "population"),
    "states.rural": ("states", "rural"),
    "states.urban": ("states", "urban"),
    "religions.rural": ("religions", "rural"),
    "religions.urban": ("religions", "urban"),
}
CANDIDATES = {
    "states.capital": ("states", "capital"),
    "states.center": ("states", "center"),
    "states.culture": ("states", "culture"),
    "burgs.culture": ("burgs", "culture"),
    "burgs.feature": ("burgs", "feature"),
    "burgs.capital": ("burgs", "capital"),
    "provinces.burg": ("provinces", "burg"),
    "provinces.center": ("provinces", "center"),
    "cultures.center": ("cultures", "center"),
    "religions.center": ("religions", "center"),
    "religions.culture": ("religions", "culture"),
    "rivers.parent": ("rivers", "parent"),
    "rivers.basin": ("rivers", "basin"),
    "rivers.mouth": ("rivers", "mouth"),
    "rivers.source": ("rivers", "source"),
    "routes.feature": ("routes", "feature"),
    "cells.f": ("cells", "f"),
    "cells.biome": ("cells", "biome"),
    "cells.r": ("cells", "r"),
}
HYPOTHESES = [
    "H-A: states[i].urban may agree with burg population sums grouped by burgs[b].state or by the state of the burg's cell.",
    "H-B: states[i].rural may agree with cell population sums grouped by cells[c].state.",
    "H-C: burg state and cell state, and cell burg and burg explicit i, may agree.",
    "H-D: cells holding a burg may have zero population; measure their count and their share of total cell population.",
    "H-E: state rural/urban totals may agree with cell-population and burg-population totals.",
    "Religion rural/urban fields may agree with cell-population and burg-population sums grouped by cells.religion.",
    "Candidate-reference hypotheses: states.capital -> burg; burgs.culture -> culture; provinces.burg -> burg; religions.culture -> culture; rivers.parent/basin -> river; rivers.mouth/source -> cell.",
]
def _records(data: dict, name: str) -> list:
    value = data.get(name, [])
    return value if isinstance(value, list) else []

def _dicts(data: dict, name: str) -> list[tuple[int, dict]]:
    return [(i, x) for i, x in enumerate(_records(data, name)) if isinstance(x, dict)]

def _num(value: Any) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False

def _numeric_values(data: dict, collection: str, field: str) -> tuple[list[float], int]:
    vals, malformed = [], 0
    records = _records(data, collection)
    for rec in records:
        if not isinstance(rec, dict):
            malformed += 1
        elif field not in rec:
            continue
        elif _num(rec[field]):
            vals.append(rec[field])
        else:
            malformed += 1
    return vals, malformed

def _stats(data: dict, collection: str, field: str) -> dict:
    vals, malformed = _numeric_values(data, collection, field)
    ints = sum(isinstance(v, int) and not isinstance(v, bool) for v in vals)
    return {"count": len(vals), "int_count": ints, "float_count": len(vals)-ints,
            "min": min(vals) if vals else None, "max": max(vals) if vals else None,
            "sum": sum(vals), "zero_count": sum(v == 0 for v in vals),
            "malformed_or_non_numeric": malformed}

def _close(a: Any, b: Any) -> dict:
    valid = _num(a) and _num(b)
    absolute = abs(a-b) if valid else None
    relative = absolute / max(abs(a), abs(b), 1.0) if valid else None
    return {"absolute_difference": absolute, "relative_difference": relative,
            "equal_exactly": bool(valid and a == b),
            "within_relative_1e-9": bool(valid and relative <= 1e-9)}

def _group_sum(records: list, key: str, value_key: str) -> dict:
    result = {}
    for rec in records:
        if not isinstance(rec, dict):
            continue
        group, value = rec.get(key), rec.get(value_key)
        if isinstance(group, int) and not isinstance(group, bool) and _num(value):
            result[group] = result.get(group, 0) + value
    return result

def _comparison_rows(states: list, field: str, sums: list[dict]) -> list[dict]:
    rows = []
    for i, state in enumerate(states):
        if not isinstance(state, dict):
            continue
        claimed = state.get(field)
        candidates = []
        for label, mapping in sums:
            total = mapping.get(i, 0)
            candidates.append({"method": label, "computed_sum": total, **_close(claimed, total)})
        rows.append({"state_index": i, "claimed_value": claimed, "comparisons": candidates})
    return rows

def _candidate_targets(data: dict) -> dict[str, set[int]]:
    targets = {}
    for coll, label, key in [
        ("burgs", "burg ids (explicit i)", "i"), ("states", "state indices", None),
        ("provinces", "province ids (explicit i)", "i"), ("cultures", "culture indices", None),
        ("religions", "religion indices", None), ("rivers", "river ids (explicit i)", "i"),
        ("cells", "pack-cell indices", None), ("features", "feature ids", "i"),
        ("biomes", "biome ids", "i"),
    ]:
        records = _records(data, coll) if coll in {"burgs","states","provinces","cultures","religions","rivers","cells"} else []
        if coll == "features":
            pack = data.get("pack")
            records = _records(pack, "features") if isinstance(pack, dict) else _records(data, "features")
        if coll == "biomes":
            pack = data.get("pack")
            records = _records(pack, "biomes") if isinstance(pack, dict) else _records(data, "biomes")
        vals = set()
        for idx, rec in enumerate(records):
            if key is None:
                vals.add(idx)
            elif isinstance(rec, dict) and isinstance(rec.get(key), int) and not isinstance(rec.get(key), bool):
                vals.add(rec[key])
        targets[label] = vals
    return targets

def _references(data: dict) -> dict:
    targets = _candidate_targets(data)
    result = {}
    for name, (collection, field) in CANDIDATES.items():
        records = _records(data, collection)
        vals = [rec.get(field) for rec in records if isinstance(rec, dict) and field in rec]
        types = {}
        for val in vals:
            typ = "null" if val is None else "bool" if isinstance(val, bool) else "int" if isinstance(val, int) else "float" if isinstance(val, float) else "string" if isinstance(val, str) else type(val).__name__
            types[typ] = types.get(typ, 0) + 1
        ints = [v for v in vals if isinstance(v, int) and not isinstance(v, bool)]
        target_fractions = {}
        eligible = [v for v in ints if v != -1]
        for space, members in targets.items():
            target_fractions[space] = (sum(v in members for v in eligible) / len(eligible)) if eligible else None
        best = max(((frac, space) for space, frac in target_fractions.items() if frac is not None), default=None)
        result[name] = {
            "record_count": len(records), "present_count": len(vals), "type_distribution": types,
            "min": min(ints) if ints else None, "max": max(ints) if ints else None,
            "minus_one_count": sum(v == -1 for v in ints), "zero_count": sum(v == 0 for v in ints),
            "missing_count": sum(not isinstance(rec, dict) or field not in rec for rec in records),
            "non_sentinel_integer_count": len(eligible), "target_fractions": target_fractions,
            "best_matching_space": {"space": best[1], "fraction": best[0]} if best else None,
        }
    return result

def measure_export(data: dict) -> dict:
    """Return deterministic, JSON-serialisable structural measurements."""
    if not isinstance(data, dict):
        data = {}
    pack = data.get("pack")
    if isinstance(pack, dict):
        merged = dict(data)
        for key, value in pack.items():
            merged.setdefault(key, value)
        data = merged
    settings = data.get("settings")
    settings_result = {}
    for key in ("populationRate", "urbanization", "urbanDensity"):
        value = settings.get(key) if isinstance(settings, dict) else None
        settings_result[key] = {"type": type(value).__name__ if (isinstance(settings, dict) and key in settings) else "missing",
                                "value": value if (isinstance(value, (str, int, bool)) or value is None or (isinstance(value, float) and math.isfinite(value))) else repr(value)}
    stats = {name: _stats(data, coll, field) for name, (coll, field) in POP_FIELDS.items()}
    cells, burgs, states, religions = (_records(data, x) for x in ("cells","burgs","states","religions"))
    valid_cells = [x for x in cells if isinstance(x, dict)]
    valid_burgs = [x for x in burgs if isinstance(x, dict)]
    state_urban_by_burg_state = _group_sum(burgs, "state", "population")
    burg_cell_state_records = []
    for burg in valid_burgs:
        cell_id = burg.get("cell")
        if isinstance(cell_id, int) and not isinstance(cell_id, bool) and 0 <= cell_id < len(cells) and isinstance(cells[cell_id], dict):
            burg_cell_state_records.append({"state": cells[cell_id].get("state"), "population": burg.get("population")})
    state_urban_by_cell_state = _group_sum(burg_cell_state_records, "state", "population")
    cell_rural_by_state = _group_sum(cells, "state", "pop")
    urban_comparisons = _comparison_rows(states, "urban", [
        ("burgs grouped by burg.state", state_urban_by_burg_state),
        ("burgs grouped by referenced cell.state", state_urban_by_cell_state)])
    rural_comparisons = _comparison_rows(states, "rural", [("cells grouped by cell.state", cell_rural_by_state)])
    for rows in (urban_comparisons, rural_comparisons):
        for row in rows:
            row["within_tolerance_count"] = sum(c["within_relative_1e-9"] for c in row["comparisons"])
    state_zero_cells = sum(isinstance(c, dict) and c.get("state") == 0 for c in cells)
    state_zero_burgs = sum(isinstance(b, dict) and b.get("state") == 0 for b in burgs)
    burg_cell_state = {"eligible": 0, "agreement": 0, "disagreement": 0, "invalid_cell_reference": 0}
    cell_burg = {"eligible": 0, "agreement": 0, "disagreement": 0, "invalid_burg_index": 0}
    burg_cells = set()
    for burg in valid_burgs:
        cell_id = burg.get("cell")
        if not isinstance(cell_id, int) or isinstance(cell_id, bool) or not 0 <= cell_id < len(cells) or not isinstance(cells[cell_id], dict):
            burg_cell_state["invalid_cell_reference"] += 1
            continue
        burg_cells.add(cell_id)
        cell = cells[cell_id]
        burg_cell_state["eligible"] += 1
        key_ok = isinstance(burg.get("state"), int) and not isinstance(burg.get("state"), bool) and isinstance(cell.get("state"), int) and not isinstance(cell.get("state"), bool)
        if key_ok and burg["state"] == cell["state"]:
            burg_cell_state["agreement"] += 1
        else:
            burg_cell_state["disagreement"] += 1
        idx = cell.get("burg")
        cell_burg["eligible"] += 1
        if isinstance(idx, int) and not isinstance(idx, bool) and idx == burg.get("i"):
            cell_burg["agreement"] += 1
        else:
            cell_burg["disagreement"] += 1
    total_cell_pop = stats["cells.pop"]["sum"]
    burg_cell_pop = sum(c.get("pop") for i, c in enumerate(cells) if i in burg_cells and isinstance(c, dict) and _num(c.get("pop")))
    state_rural_sum = stats["states.rural"]["sum"]
    state_urban_sum = stats["states.urban"]["sum"]
    religion_rows = {}
    cell_by_religion = _group_sum(cells, "religion", "pop")
    burg_by_religion = {}
    for burg in valid_burgs:
        cell_id = burg.get("cell")
        if isinstance(cell_id, int) and not isinstance(cell_id, bool) and 0 <= cell_id < len(cells) and isinstance(cells[cell_id], dict):
            rel = cells[cell_id].get("religion")
            pop = burg.get("population")
            if isinstance(rel, int) and not isinstance(rel, bool) and _num(pop):
                burg_by_religion[rel] = burg_by_religion.get(rel, 0) + pop
    for i, rel in enumerate(religions):
        if not isinstance(rel, dict):
            continue
        religion_rows[str(i)] = {"rural_claimed": rel.get("rural"), "rural_cell_sum": cell_by_religion.get(i, 0),
                                 "rural_comparison": _close(rel.get("rural"), cell_by_religion.get(i, 0)),
                                 "urban_claimed": rel.get("urban"), "urban_burg_sum": burg_by_religion.get(i, 0),
                                 "urban_comparison": _close(rel.get("urban"), burg_by_religion.get(i, 0))}
    state_summaries = {}
    for name, rows in (("urban", urban_comparisons), ("rural", rural_comparisons)):
        comparisons = [c for row in rows for c in row["comparisons"] if c["relative_difference"] is not None]
        state_summaries[name] = {"states_compared": len(rows),
            "max_absolute_difference": max((c["absolute_difference"] for c in comparisons), default=None),
            "max_relative_difference": max((c["relative_difference"] for c in comparisons), default=None),
            "within_tolerance_by_method": {label: sum(any(c["method"] == label and c["within_relative_1e-9"] for c in row["comparisons"]) for row in rows)
                                           for label in ("burgs grouped by burg.state", "burgs grouped by referenced cell.state", "cells grouped by cell.state")}}
    return {"settings": settings_result, "population_fields": stats,
        "state_comparisons": {"urban": urban_comparisons, "rural": rural_comparisons,
          "summary": state_summaries, "state_zero": {"cell_count": state_zero_cells, "burg_count": state_zero_burgs}},
        "burg_cell_checks": {"burg_state_vs_cell_state": burg_cell_state, "cell_burg_vs_explicit_burg_i": cell_burg},
        "burg_cells_population": {"cells_holding_burg_count": len(burg_cells),
          "zero_population_cells_holding_burg": sum(isinstance(cells[i], dict) and cells[i].get("pop") == 0 for i in burg_cells),
          "total_cell_population": total_cell_pop, "population_on_burg_cells": burg_cell_pop,
          "share_of_total_cell_population": burg_cell_pop / total_cell_pop if total_cell_pop else None},
        "totals": {"states_rural_sum": state_rural_sum, "states_urban_sum": state_urban_sum,
          "cells_pop_sum": total_cell_pop, "burgs_population_sum": stats["burgs.population"]["sum"],
          "state_rural_vs_cells": _close(state_rural_sum, total_cell_pop),
          "state_urban_vs_burgs": _close(state_urban_sum, stats["burgs.population"]["sum"])},
        "religion_comparisons": religion_rows, "candidate_references": _references(data),
        "malformed_records": {name: sum(not isinstance(x, dict) for x in _records(data, name)) + int(name in data and not isinstance(data[name], list))
          for name in ("cells","burgs","states","religions","provinces","cultures","rivers","routes")}}

def render_markdown(name: str, result: dict) -> str:
    """Render a compact, deterministic report from a measurement result."""
    def fmt(value):
        if value is None:
            return "n/a"
        if isinstance(value, float):
            return repr(value)
        if isinstance(value, (dict, list)):
            return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
        return str(value)
    lines = [f"## FMG measurement: {name}", "", "Measurement only; no FMG semantic conclusions are drawn.", "",
             "### Settings", "", "| Field | Type | Value |", "|---|---|---|"]
    for key, val in result["settings"].items():
        lines.append(f"| {key} | {val['type']} | {fmt(val['value'])} |")
    lines += ["", "### Population fields", "", "| Field | Count | Int | Float | Min | Max | Sum | Zero | Malformed/non-numeric |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for key, val in result["population_fields"].items():
        lines.append("| " + key + " | " + " | ".join(fmt(val[k]) for k in ("count","int_count","float_count","min","max","sum","zero_count","malformed_or_non_numeric")) + " |")
    lines += ["", "### State comparisons", "", fmt(result["state_comparisons"]), "", "### Burg/cell checks and totals", "", fmt(result["burg_cell_checks"]), "", fmt(result["burg_cells_population"]), "", fmt(result["totals"]), "", "### Religion comparisons", "", fmt(result["religion_comparisons"]), "", "### Candidate references", "", fmt(result["candidate_references"]), "", "### Malformed records", "", fmt(result["malformed_records"]), ""]
    return "\n".join(lines)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exports", nargs="+", type=Path)
    parser.add_argument("--json", type=Path, dest="json_path")
    args = parser.parse_args()
    reports, results = [], {}
    for path in args.exports:
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)
        result = measure_export(data)
        reports.append(render_markdown(path.name, result))
        results[path.name] = result
    print("\n\n".join(reports))
    if args.json_path:
        args.json_path.write_text(json.dumps(results, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
