"""Measure how titular stability weight changes proposal churn on tiny instances."""
from __future__ import annotations
import argparse
import json
from dataclasses import replace
from pathlib import Path

from experiments.anchored_succession.checker import check_solution
from experiments.anchored_succession.clingo_backend import solve_problem as solve_clingo
from experiments.anchored_succession.cp_sat import solve_problem as solve_cp_sat
from experiments.anchored_succession.model import Anchor
from experiments.anchored_succession.objective import evaluate_objective
from experiments.anchored_succession.reconcile import changed_facts, projection_from_result
from experiments.anchored_succession.scenarios import three_person_problem


def _solve(problem, backend):
    result = solve_cp_sat(problem, time_limit_seconds=10) if backend == "cp-sat" else solve_clingo(problem, time_limit_seconds=10)
    if result.status not in ("solved", "feasible") or result.solution is None:
        raise RuntimeError(f"{backend} stability measurement did not find a feasible incumbent: {result.status}")
    errors = check_solution(problem, result.solution)
    if errors:
        raise RuntimeError(f"{backend} stability result failed independent checker: {errors}")
    expected = evaluate_objective(problem, result.solution)
    if result.objective != expected:
        raise RuntimeError(f"{backend} objective mismatch: {result.objective} != {expected}")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    changes = (
        Anchor("soft-C-20", "soft", "C", start=20, tolerance=0, weight=2),
        Anchor("soft-B-24", "soft", "B", start=24, tolerance=1, weight=2),
        Anchor("soft-C-26", "soft", "C", start=26, tolerance=0, weight=4),
    )
    rows = []
    for backend in ("cp-sat", "clingo"):
        base = three_person_problem()
        previous = _solve(base, backend)
        projection = projection_from_result(base, previous)
        for anchor in changes:
            changed = replace(base, anchors=base.anchors + (anchor,))
            plain = _solve(changed, backend)
            stable_problem = replace(
                changed, rules=replace(changed.rules, stability_weight=2),
                stability_reference=previous.solution.titular,
            )
            stable = _solve(stable_problem, backend)
            plain_diff = changed_facts(projection.solution, plain.solution)
            stable_diff = changed_facts(projection.solution, stable.solution)
            before = len(plain_diff[0]) + len(plain_diff[1])
            after = len(stable_diff[0]) + len(stable_diff[1])
            rows.append({
                "backend": backend, "anchor_change": anchor.anchor_id,
                "changed_facts_without_stability": before,
                "changed_facts_with_stability": after, "stability_helped": after < before,
                "no_stability_objective": plain.objective, "with_stability_objective": stable.objective,
                "no_stability_checker_passed": True, "with_stability_checker_passed": True,
            })
    report = {
        "method": "total added plus removed (layer,ruler,start,end) facts vs the prior titular/effective solution",
        "stability_weight": 2, "anchor_changes": 3, "rows": rows,
    }
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload)
    else:
        print(payload)


if __name__ == "__main__":
    main()
