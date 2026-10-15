"""Measure grounded ASP rule families with isolated grounding runs.

No ASP encoding or solver objective is changed. Each named constraint's count is
measured as the incremental ground-rule count when added to its minimal support
program. "Everything else" is measured by grounding the full source with the two
named constraint templates removed, rather than computed by subtraction.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from experiments.anchored_succession.clingo_backend import _GroundingCounter, _program
from experiments.anchored_succession.fixtures import generated_pool
from experiments.anchored_succession.model import Anchor


AT_MOST_ONCE = ":- start(L,P,Y), start(L,P,Z), Y < Z."
NON_KIN = ":- present(L,P,Y), present(L,Q,Z), Z = Y+1, P != Q, not parent(Q,P), not sibling(P,Q)."
PRESENT = "0 { present(L,P,Y) : person(P,_,_) } 1 :- layer(L), year(Y)."
START = "start(L,P,Y) :- present(L,P,Y), not present(L,P,Y-1)."
SIBLING = "sibling(P,Q) :- parent(P,A), parent(Q,A), P != Q."


def _ground_rules(source: str) -> int:
    import clingo

    counter = _GroundingCounter()
    control = clingo.Control(["--warn=none"])
    control.register_observer(counter, replace=True)
    control.add("base", [], source)
    control.ground([("base", [])])
    return counter.rules


def _problem(size: int):
    generated = generated_pool(size)
    rules = replace(generated.rules, horizon_start=0, horizon_end=299)
    years = (49, 149, 249)
    anchors = tuple(
        Anchor(f"scale-pin-{i}", "hard", f"P{i}", start=year, end=year + 2)
        for i, year in enumerate(years)
    )
    return replace(generated, rules=rules, anchors=anchors)


def _common_lines(source: str) -> list[str]:
    # Keep input facts, active-anchor declarations, and directives; exclude all
    # logic rules, then add only the support rules needed by each isolated family.
    return [
        line for line in source.splitlines()
        if line.strip()
        and ":-" not in line
        and not line.startswith(PRESENT)
        and not line.startswith("#minimize")
    ]


def _family_counts(problem) -> dict[str, int]:
    source, _ = _program(problem)
    common = _common_lines(source)
    present = PRESENT
    start = START
    sibling = SIBLING
    at_most_base = "\n".join([*common, present, start])
    at_most_full = "\n".join([at_most_base, AT_MOST_ONCE])
    non_kin_base = "\n".join([*common, present, sibling])
    non_kin_full = "\n".join([non_kin_base, NON_KIN])
    full = _ground_rules(source)
    at_most_once = _ground_rules(at_most_full) - _ground_rules(at_most_base)
    non_kin_succession = _ground_rules(non_kin_full) - _ground_rules(non_kin_base)
    if source.count(AT_MOST_ONCE) != 1 or source.count(NON_KIN) != 1:
        raise RuntimeError("expected exactly one instance of each target constraint template")
    without_targets = source.replace(AT_MOST_ONCE, "").replace(NON_KIN, "")
    other = _ground_rules(without_targets)
    if min(at_most_once, non_kin_succession, other) < 0:
        raise RuntimeError("isolated rule-family grounding returned a negative count")
    return {
        "total_ground_rules": full,
        "at_most_once_ruler_constraint": at_most_once,
        "non_kin_succession_constraint": non_kin_succession,
        "everything_else": other,
        "method": "incremental isolated grounding for each target constraint with minimal support rules; everything_else measured by grounding the full source with both target templates removed",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--planted-chain", action="store_true", help="isolate anchor, occupancy-span, soft-anchor and remaining rules for the 100-person planted 250-year chain")
    args = parser.parse_args()
    if args.planted_chain:
        from time import perf_counter
        from experiments.anchored_succession.measure_construction import succession_chain_problem
        problem, planted, lower_bound = succession_chain_problem(100, horizon_years=250, include_soft_anchors=True)
        source, _ = _program(problem, encoding="aggregate-successor")
        families: dict[str, list[str]] = {
            "anchor_rules": [], "occupancy_span_pairwise_rules": [],
            "soft_anchor_rules": [], "everything_else": [],
        }
        for line in source.splitlines():
            if "not occupied(" in line and "active(" in line:
                families["occupancy_span_pairwise_rules"].append(line)
            elif "chain-mid-soft" in line or "soft_anchor(" in line:
                families["soft_anchor_rules"].append(line)
            elif "chain-first" in line or "chain-last" in line:
                families["anchor_rules"].append(line)
            else:
                families["everything_else"].append(line)
        shared = families["everything_else"]
        rows = []
        for name in ("anchor_rules", "occupancy_span_pairwise_rules", "soft_anchor_rules", "everything_else"):
            isolated_source = "\\n".join(shared if name == "everything_else" else shared + families[name])
            started = perf_counter()
            rule_count = _ground_rules(isolated_source)
            elapsed = perf_counter() - started
            rows.append({"family": name, "source_line_count": len(families[name]),
                         "ground_rules": rule_count, "grounding_time_seconds": elapsed,
                         "measurement": "ground shared support/everything-else rules plus only this isolated family" if name != "everything_else" else "ground everything-else support without the three target families"})
        full_started = perf_counter()
        full_rules = _ground_rules(source)
        full_elapsed = perf_counter() - full_started
        report = {"mode": "planted-chain-rule-family-attribution", "people": 100,
                  "horizon_years": 250, "encoding": "aggregate-successor",
                  "encoding_changed": False, "time_limit_seconds": None,
                  "rules": {"min_reign": problem.rules.min_reign, "max_reign": problem.rules.max_reign,
                            "preferred_reign": problem.rules.preferred_reign},
                  "analytic_lower_bound_rulers": lower_bound,
                  "planted_reigns": [{"ruler": reign.ruler, "start": reign.start, "end": reign.end,
                                      "length": reign.end-reign.start+1} for reign in planted.titular],
                  "families": rows, "full_program": {"ground_rules": full_rules,
                                                       "grounding_time_seconds": full_elapsed},
                  "method": "Each family is grounded with shared support/everything-else rules; the family-specific lines are added alone. The full program is separately grounded as a reference. Counts are isolated-run totals, not additive partitions."}
        payload = json.dumps(report, indent=2) + "\\n"
        if args.output:
            args.output.write_text(payload)
        print(payload, end="")
        return
    report = {
        "horizon_years": 300,
        "people_sizes": [12, 30, 100],
        "encoding_changed": False,
        "rows": [
            {"people": size, **_family_counts(_problem(size))}
            for size in (12, 30, 100)
        ],
        "caveat": "Named-family counts are incremental ground instances of the isolated constraint templates; everything_else is a direct grounding run of the complete source with both named templates removed. Counts may not sum to the full count if removing constraints changes grounding simplification.",
    }
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload)
    print(payload, end="")


if __name__ == "__main__":
    main()
