"""Measure reconciliation churn, oracle baselines, and dominating stability weights."""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from experiments.anchored_succession.checker import check_solution
from experiments.anchored_succession.clingo_backend import solve_problem as solve_clingo
from experiments.anchored_succession.cp_sat import solve_problem as solve_cp_sat
from experiments.anchored_succession.model import Anchor, Problem, Solution
from experiments.anchored_succession.objective import evaluate_objective
from experiments.anchored_succession.oracle import enumerate_solutions
from experiments.anchored_succession.reconcile import changed_facts, projection_from_result
from experiments.anchored_succession.scenarios import three_person_problem


DOMINATING_STABILITY_WEIGHT = 1000
ORACLE_NODE_CAP = 1_000_000


def _solve(problem: Problem, backend: str):
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


def _churn(reference: Solution, candidate: Solution) -> int:
    added, removed = changed_facts(reference, candidate)
    return len(added) + len(removed)


def _oracle_baseline(problem: Problem, reference: Solution) -> dict[str, int]:
    # Stability is deliberately absent from this objective: "real objective"
    # means the original problem objective, independent of churn.
    real_problem = replace(
        problem, rules=replace(problem.rules, stability_weight=0),
        stability_reference=(),
    )
    solutions = enumerate_solutions(real_problem, node_cap=ORACLE_NODE_CAP)
    if not solutions:
        raise RuntimeError("oracle found no feasible solutions for stability baseline")
    scored = [(evaluate_objective(real_problem, solution), _churn(reference, solution)) for solution in solutions]
    optimum = min(objective for objective, _ in scored)
    return {
        "oracle_feasible_solution_count": len(solutions),
        "minimum_changed_facts_among_all_feasible": min(churn for _, churn in scored),
        "minimum_changed_facts_among_real_objective_optimal": min(
            churn for objective, churn in scored if objective == optimum
        ),
        "minimum_real_objective": optimum,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    # Keep the three prior cases exactly for comparison. Add two modest, present-ruler
    # cases whose soft penalties are small enough to compete with stability weight 2.
    changes = (
        Anchor("soft-C-20", "soft", "C", start=20, tolerance=0, weight=2),
        Anchor("soft-B-24", "soft", "B", start=24, tolerance=1, weight=2),
        Anchor("soft-C-26", "soft", "C", start=26, tolerance=0, weight=4),
        Anchor("sensitive-A-20", "soft", "A", start=20, tolerance=0, weight=1),
        Anchor("sensitive-B-24", "soft", "B", start=24, tolerance=0, weight=1),
    )
    rows = []
    for backend in ("cp-sat", "clingo"):
        base = three_person_problem()
        previous = _solve(base, backend)
        projection = projection_from_result(base, previous)
        for anchor in changes:
            changed = replace(base, anchors=base.anchors + (anchor,))
            plain = _solve(changed, backend)
            oracle = _oracle_baseline(changed, projection.solution)
            for stability_weight, label in (
                (2, "weight_2"),
                (DOMINATING_STABILITY_WEIGHT, "dominating_weight"),
            ):
                stable_problem = replace(
                    changed,
                    rules=replace(changed.rules, stability_weight=stability_weight),
                    stability_reference=projection.solution.titular,
                )
                stable = _solve(stable_problem, backend)
                # Compare real objectives under the same problem (without stability).
                plain_real = evaluate_objective(changed, plain.solution)
                stable_real = evaluate_objective(changed, stable.solution)
                stable_objective = evaluate_objective(stable_problem, stable.solution)
                if stable_objective > evaluate_objective(stable_problem, plain.solution):
                    raise RuntimeError(f"{backend}/{anchor.anchor_id}: stability objective regression")
                if plain_real > stable_real:
                    raise RuntimeError(f"{backend}/{anchor.anchor_id}: unexpected real-objective ordering")
                row = {
                    "backend": backend,
                    "anchor_change": anchor.anchor_id,
                    "anchor_weight": anchor.weight,
                    "stability_weight": stability_weight,
                    "weight_label": label,
                    "changed_facts_weight_0": _churn(projection.solution, plain.solution),
                    "changed_facts_stability_weight": _churn(projection.solution, stable.solution),
                    "no_stability_objective_under_changed_problem": plain_real,
                    "stability_solution_objective_under_changed_problem": stable_real,
                    "stability_solution_objective_under_stability_problem": stable_objective,
                    "independent_checker_passed": True,
                    **oracle,
                }
                rows.append(row)
    report = {
        "method": "changed facts = added plus removed (layer,ruler,start,end) facts on both titular and effective layers",
        "stability_metric_scope": "the churn metric counts both layers; the objective's stability term penalises titular mismatches only",
        "real_objective_comparison": "all real-objective values are evaluated under the same changed problem with stability disabled; the stability-augmented objective is reported separately",
        "dominance": {
            "stability_weight": DOMINATING_STABILITY_WEIGHT,
            "rationale": "1000 exceeds the conservative upper bound for the real objective in these three-person, 31-year fixtures (soft-anchor penalties at most 558, reign-length costs at most 24, sibling costs at most 4); any titular mismatch costs at least 1000",
        },
        "oracle_node_cap": ORACLE_NODE_CAP,
        "anchor_changes": len(changes),
        "rows": rows,
    }
    payload = json.dumps(report, indent=2) + "\\n"
    if args.output:
        args.output.write_text(payload)
    print(payload, end="")


if __name__ == "__main__":
    main()
