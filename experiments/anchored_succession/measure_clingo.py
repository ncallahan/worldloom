"""Record clingo grounding and solve measurements for the seven Stage 3 scenarios."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.anchored_succession.clingo_backend import solve_problem as solve_clingo
from experiments.anchored_succession.cp_sat import solve_problem as solve_cp_sat
from experiments.anchored_succession.objective import evaluate_objective
from experiments.anchored_succession.oracle import optimal_solutions, oracle_result
from experiments.anchored_succession.scenarios import cross_backend_problems, stage3_scenarios, three_person_problem


def result_data(result, problem):
    return {
        "status": result.status,
        "objective": result.objective,
        "selected_solution": None if result.solution is None else {
            "titular": [(r.ruler, r.start, r.end) for r in result.solution.titular],
            "effective": [(r.ruler, r.start, r.end) for r in result.solution.effective],
        },
        "independent_objective": (
            None if result.solution is None else evaluate_objective(problem, result.solution)
        ),
        "ground_atoms": result.ground_atoms,
        "ground_rules": result.ground_rules,
        "grounding_time_seconds": result.grounding_time_seconds,
        "solve_time_seconds": result.solve_time_seconds,
        "explanation": list(result.explanation),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = {}
    for name, problem in stage3_scenarios().items():
        asp = solve_clingo(problem, time_limit_seconds=10)
        cp = solve_cp_sat(problem, time_limit_seconds=10)
        rows[name] = {
            "clingo": result_data(asp, problem),
            "cp_sat": {
                "status": cp.status,
                "objective": cp.objective,
                "model_variables": cp.model_variables,
                "model_constraints": cp.model_constraints,
            },
            "selected_solutions_agree": (
                asp.solution is not None and cp.solution is not None and asp.solution == cp.solution
            ),
        }

    order_problem = three_person_problem(include_soft=True)
    cp_base = solve_cp_sat(order_problem, time_limit_seconds=10)
    asp_base = solve_clingo(order_problem, time_limit_seconds=10)
    rows["scenario_6_order_independence"] = {
        "seeds": {},
        "selected_solutions_agree": (
            cp_base.solution is not None and asp_base.solution is not None
            and cp_base.solution == asp_base.solution
        ),
    }
    for seed in (3, 17, 2026, 91003):
        cp_shuffled = solve_cp_sat(order_problem, time_limit_seconds=10, canonical_order=False, order_seed=seed)
        asp_shuffled = solve_clingo(order_problem, time_limit_seconds=10, canonical_order=False, order_seed=seed)
        rows["scenario_6_order_independence"]["seeds"][str(seed)] = {
            "cp_sat_solution_unchanged": cp_shuffled.solution == cp_base.solution,
            "cp_sat_objective_unchanged": cp_shuffled.objective == cp_base.objective,
            "clingo_solution_unchanged": asp_shuffled.solution == asp_base.solution,
            "clingo_objective_unchanged": asp_shuffled.objective == asp_base.objective,
            "clingo_ground_atoms": asp_shuffled.ground_atoms,
            "clingo_ground_rules": asp_shuffled.ground_rules,
            "clingo_grounding_time_seconds": asp_shuffled.grounding_time_seconds,
            "clingo_solve_time_seconds": asp_shuffled.solve_time_seconds,
        }

    findings = []
    comparisons = {}
    for name, problem in cross_backend_problems().items():
        oracle = oracle_result(problem)
        optima = optimal_solutions(problem)
        cp = solve_cp_sat(problem, time_limit_seconds=10)
        asp = solve_clingo(problem, time_limit_seconds=10)
        expected_feasible = oracle.status == "solved"
        checks = {}
        for backend_name, result in (("cp_sat", cp), ("clingo", asp)):
            checks[backend_name] = {
                "feasible_agrees": result.status == ("solved" if expected_feasible else "infeasible"),
                "objective_agrees": not expected_feasible or result.objective == oracle.objective,
                "solution_in_oracle_optimal_set": not expected_feasible or result.solution in optima,
            }
            for field, okay in checks[backend_name].items():
                if not okay:
                    findings.append(f"{name}: {backend_name} {field} mismatch")
        comparisons[name] = {
            "oracle_status": oracle.status,
            "oracle_objective": oracle.objective,
            "cp_sat": checks["cp_sat"],
            "clingo": checks["clingo"],
            "selected_solutions_agree": cp.solution is not None and asp.solution is not None and cp.solution == asp.solution,
            "clingo_ground_atoms": asp.ground_atoms,
            "clingo_ground_rules": asp.ground_rules,
            "clingo_grounding_time_seconds": asp.grounding_time_seconds,
            "clingo_solve_time_seconds": asp.solve_time_seconds,
        }
    rows["scenario_7_cross_backend_oracle_agreement"] = {
        "comparisons": comparisons,
        "findings": findings,
    }
    args.output.write_text(json.dumps({
        "backend": "clingo-asp",
        "version": "5.8.2",
        "real_objective_priority": 2,
        "tie_break_priority": 1,
        "tie_break_method": "rng_for-derived weights at a subordinate ASP optimization priority",
        "scenarios": rows,
        "scale_claim": None,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
