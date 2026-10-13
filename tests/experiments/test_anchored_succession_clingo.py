from __future__ import annotations

import os

import pytest

from experiments.anchored_succession.checker import check_solution
from experiments.anchored_succession.clingo_backend import solve_problem as solve_clingo
from experiments.anchored_succession.model import Anchor, Person, Problem, Reign
from experiments.anchored_succession.objective import evaluate_objective
from experiments.anchored_succession.oracle import optimal_solutions, oracle_result
from experiments.anchored_succession.scenarios import (
    cross_backend_problems,
    small_rules,
    stage3_scenarios,
    three_person_problem,
)


def require_clingo() -> None:
    try:
        import clingo  # noqa: F401
    except ImportError:
        if os.environ.get("WORLDLOOM_REQUIRE_CLINGO") == "1":
            pytest.fail("clingo backend missing while WORLDLOOM_REQUIRE_CLINGO=1")
        pytest.skip("optional clingo dependency is not installed outside its CI gate")


def require_both_backends() -> None:
    require_clingo()
    try:
        import ortools  # noqa: F401
    except ImportError:
        if os.environ.get("WORLDLOOM_REQUIRE_CP_SAT") == "1":
            pytest.fail("CP-SAT backend missing while WORLDLOOM_REQUIRE_CP_SAT=1")
        pytest.skip("cross-backend comparisons require the optional CP-SAT extra")


def test_clingo_backend_presence_gate_fails_if_missing_in_ci():
    if os.environ.get("WORLDLOOM_REQUIRE_CLINGO") != "1":
        pytest.skip("backend-presence assertion is enforced by the dedicated clingo CI job")
    try:
        import clingo  # noqa: F401
    except ImportError:
        pytest.fail("clingo backend missing while WORLDLOOM_REQUIRE_CLINGO=1")


def test_scenario_1_hard_anchors_only_matches_oracle_optimum():
    require_clingo()
    problem = stage3_scenarios()["scenario_1_hard_anchors_only"]
    assert all(anchor.kind == "hard" for anchor in problem.anchors)
    result = solve_clingo(problem, time_limit_seconds=10)
    expected = optimal_solutions(problem)
    assert result.status == "solved"
    assert result.solution is not None and result.solution in expected
    assert result.objective == min(evaluate_objective(problem, item) for item in expected)
    assert result.objective == evaluate_objective(problem, result.solution)
    assert check_solution(problem, result.solution) == ()
    assert result.ground_atoms is not None and result.ground_atoms > 0
    assert result.ground_rules is not None and result.ground_rules > 0
    assert result.grounding_time_seconds is not None and result.solve_time_seconds is not None


def test_scenario_2_conflict_core_is_deletion_minimal_and_removals_are_exploratory():
    require_clingo()
    problem = stage3_scenarios()["scenario_2_conflicting_hard_anchors"]
    result = solve_clingo(problem, time_limit_seconds=10)
    assert result.status == "infeasible"
    assert result.conflict_minimal is True
    assert any("conflicting anchor subset" in line for line in result.explanation)
    assert any("subset-minimal under deletion checks" in line for line in result.explanation)
    assert any("Exploratory smallest anchor-removal set(s)" in line for line in result.explanation)
    assert any("{pin-A}" in line and "{pin-B}" in line for line in result.explanation)
    assert any("resulting objective 0" in line for line in result.explanation)


def test_scenario_2_reports_infeasibility_independent_of_anchors_when_ruler_is_too_young():
    require_clingo()
    rules = small_rules()
    problem = Problem(
        (Person("too-young", 20, 30),),
        (Anchor("pin-too-young", "hard", "too-young", start=16, end=19),),
        rules,
    )
    result = solve_clingo(problem, time_limit_seconds=10)
    assert result.status == "infeasible"
    assert any("infeasible independent of anchors" in line for line in result.explanation)


def test_scenario_3_soft_tolerance_cost_and_direction_match_oracle():
    require_clingo()
    rules = small_rules()
    inside_problem = Problem(
        (Person("A", 0, 30),),
        (Anchor("soft-A", "soft", "A", start=18, tolerance=2, weight=10),),
        rules,
    )
    inside = solve_clingo(inside_problem, time_limit_seconds=10)
    assert inside.solution is not None
    assert 16 <= inside.solution.titular[0].start <= 20
    assert inside.objective == 0
    assert inside.objective == evaluate_objective(inside_problem, inside.solution)

    outside_problem = Problem(
        (Person("A", 0, 30),),
        (
            Anchor("pin-start", "hard", "A", lower=24, upper=24),
            Anchor("pin-span", "hard", "A", start=24, end=27),
            Anchor("soft-A", "soft", "A", start=18, tolerance=2, weight=7),
        ),
        rules,
    )
    outside = solve_clingo(outside_problem, time_limit_seconds=10)
    assert outside.solution is not None
    assert outside.solution.titular == (Reign("A", 24, 27),)
    assert outside.objective == 7 * (abs(24 - 18) - 2)
    assert outside.objective == evaluate_objective(outside_problem, outside.solution)

    direction = Problem(
        (Person("A", 0, 30), Person("B", 0, 30, ("A",))),
        (
            Anchor("pin-A", "hard", "A", start=16, end=19),
            Anchor("soft-B", "soft", "B", start=25, tolerance=0, weight=10),
        ),
        rules,
    )
    with_soft = solve_clingo(direction, time_limit_seconds=10)
    without_problem = Problem(direction.people, tuple(a for a in direction.anchors if a.kind != "soft"), rules)
    without_soft = solve_clingo(without_problem, time_limit_seconds=10)
    assert with_soft.solution is not None and without_soft.solution is not None
    assert with_soft.solution != without_soft.solution
    assert with_soft.objective > without_soft.objective
    assert any(reign.ruler == "B" for reign in with_soft.solution.titular)
    assert all(reign.ruler != "B" for reign in without_soft.solution.titular)
    assert with_soft.objective < 10 * (rules.horizon_end - rules.horizon_start + 1)


def test_scenario_4_reveal_only_and_marked_unmarked_record_semantics():
    require_clingo()
    reveal_problem = stage3_scenarios()["scenario_4_reveal_only"]
    reveal_result = solve_clingo(reveal_problem, time_limit_seconds=10)
    assert reveal_result.status == "solved"
    assert reveal_result.solution is not None
    assert any(r.ruler == "B" and r.start <= 16 and r.end >= 19 for r in reveal_result.solution.effective)
    assert all(
        not any(r.ruler == "B" and r.start <= year <= r.end for r in reveal_result.solution.titular)
        for year in range(16, 20)
    )
    assert reveal_result.objective == evaluate_objective(reveal_problem, reveal_result.solution)

    unmarked = Problem(
        (Person("A", 0, 30), Person("B", 0, 30, ("A",))),
        (
            Anchor("record-A", "record", "A", start=16, end=19),
            Anchor("reveal-B", "reveal", "B", start=16, end=19),
        ),
        small_rules(),
    )
    assert solve_clingo(unmarked, time_limit_seconds=10).status == "infeasible"
    marked = cross_backend_problems()["marked_record_reveal"]
    marked_result = solve_clingo(marked, time_limit_seconds=10)
    assert marked_result.status == "solved"
    assert marked_result.solution is not None
    assert check_solution(marked, marked_result.solution) == ()


def test_scenario_5_repeatability_and_scenario_metrics():
    require_clingo()
    problem = stage3_scenarios()["scenario_5_repeatability"]
    first = solve_clingo(problem, time_limit_seconds=10)
    repeated = solve_clingo(problem, time_limit_seconds=10)
    assert first.status == repeated.status == "solved"
    assert first.solution == repeated.solution
    assert first.objective == repeated.objective
    assert first.ground_atoms == repeated.ground_atoms
    assert first.ground_rules == repeated.ground_rules


def test_scenario_6_order_independence_for_both_encodings():
    require_both_backends()
    from experiments.anchored_succession.cp_sat import solve_problem as solve_cp_sat

    problem = three_person_problem(include_soft=True)
    cp_reference = solve_cp_sat(problem, time_limit_seconds=10)
    asp_reference = solve_clingo(problem, time_limit_seconds=10)
    assert cp_reference.solution is not None and asp_reference.solution is not None
    for seed in (3, 17, 2026, 91003):
        cp_shuffled = solve_cp_sat(
            problem, time_limit_seconds=10, canonical_order=False, order_seed=seed
        )
        asp_shuffled = solve_clingo(
            problem, time_limit_seconds=10, canonical_order=False, order_seed=seed
        )
        assert cp_shuffled.solution == cp_reference.solution, f"CP-SAT solution changed at seed {seed}"
        assert cp_shuffled.objective == cp_reference.objective, f"CP-SAT objective changed at seed {seed}"
        assert asp_shuffled.solution == asp_reference.solution, f"clingo solution changed at seed {seed}"
        assert asp_shuffled.objective == asp_reference.objective, f"clingo objective changed at seed {seed}"


def test_scenario_7_cross_backend_agreement_with_oracle_reports_all_disagreements():
    require_both_backends()
    from experiments.anchored_succession.cp_sat import solve_problem as solve_cp_sat

    findings: list[str] = []
    for name, problem in cross_backend_problems().items():
        oracle = oracle_result(problem)
        cp_result = solve_cp_sat(problem, time_limit_seconds=10)
        asp_result = solve_clingo(problem, time_limit_seconds=10)
        expected_feasible = oracle.status == "solved"
        for backend_name, result in (("CP-SAT", cp_result), ("clingo", asp_result)):
            actual_feasible = result.status == "solved"
            if actual_feasible != expected_feasible:
                findings.append(f"{name}: {backend_name} feasibility={actual_feasible}, oracle={expected_feasible}")
            if expected_feasible:
                optima = optimal_solutions(problem)
                if result.objective != oracle.objective:
                    findings.append(f"{name}: {backend_name} objective={result.objective}, oracle={oracle.objective}")
                if result.solution not in optima:
                    findings.append(f"{name}: {backend_name} selected solution is not in the oracle optimal set")
                if result.solution is not None and result.objective != evaluate_objective(problem, result.solution):
                    findings.append(f"{name}: {backend_name} objective disagrees with independent evaluator")
    assert not findings, "cross-backend disagreement findings:\n" + "\n".join(findings)

 

def test_clingo_objective_parity_includes_sibling_and_stability_costs():
    require_both_backends()
    from experiments.anchored_succession.cp_sat import solve_problem as solve_cp_sat

    problem = cross_backend_problems()["sibling_and_stability_costs"]
    asp = solve_clingo(problem, time_limit_seconds=10)
    cp = solve_cp_sat(problem, time_limit_seconds=10)
    optima = optimal_solutions(problem)
    assert asp.status == cp.status == "solved"
    assert asp.solution is not None and cp.solution is not None
    assert asp.objective == evaluate_objective(problem, asp.solution)
    assert cp.objective == evaluate_objective(problem, cp.solution)
    assert asp.objective == cp.objective == 26
    assert asp.solution in optima and cp.solution in optima
