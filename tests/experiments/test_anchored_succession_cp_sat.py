from __future__ import annotations

import os
import pytest
from dataclasses import replace

from experiments.anchored_succession.checker import check_solution
from experiments.anchored_succession.model import Anchor, Person, Problem, Reign, Rules, Solution
from experiments.anchored_succession.objective import evaluate_objective
from experiments.anchored_succession.oracle import optimal_solutions
from experiments.anchored_succession.cp_sat import solve_problem


def small_rules() -> Rules:
    return Rules(
        min_accession_age=16, min_reign=3, max_reign=8, preferred_reign=4,
        horizon_start=0, horizon_end=30, child_preference_weight=1, stability_weight=0,
    )


def three_person_problem() -> Problem:
    people = (
        Person("A", 0, 30),
        Person("B", 2, 30, ("A",)),
        Person("C", 3, 30, ("A",)),
    )
    anchors = (
        Anchor("pin-A", "hard", "A", start=16, end=19),
        Anchor("prefer-B", "soft", "B", start=20, tolerance=0, weight=1),
    )
    return Problem(people, anchors, small_rules(), seed=20261013)


def require_backend() -> None:
    try:
        import ortools  # noqa: F401
    except ImportError:
        if os.environ.get("WORLDLOOM_REQUIRE_CP_SAT") == "1":
            pytest.fail("CP-SAT backend missing while WORLDLOOM_REQUIRE_CP_SAT=1")
        pytest.skip("optional CP-SAT dependency is not installed outside its CI gate")


def test_cp_sat_backend_presence_gate_fails_if_missing_in_ci():
    if os.environ.get("WORLDLOOM_REQUIRE_CP_SAT") != "1":
        pytest.skip("backend-presence assertion is enforced by the dedicated solver CI job")
    try:
        import ortools  # noqa: F401
    except ImportError:
        pytest.fail("CI requested CP-SAT but ortools is not installed")


def assert_matches_oracle(problem: Problem, result) -> None:
    assert result.status == "solved"
    assert result.solution is not None
    assert check_solution(problem, result.solution) == ()
    assert result.objective == evaluate_objective(problem, result.solution)
    oracle_optima = optimal_solutions(problem, node_cap=100_000)
    assert oracle_optima
    assert result.objective == min(evaluate_objective(problem, item) for item in oracle_optima)
    assert result.solution in oracle_optima


def test_scenario_1_feasible_hard_anchors_match_oracle_optimum():
    require_backend()
    problem = three_person_problem()
    result = solve_problem(problem, time_limit_seconds=10)
    assert_matches_oracle(problem, result)


def test_scenario_2_infeasible_anchor_core_and_smallest_removals_are_exploratory():
    require_backend()
    people = (Person("A", 0, 30), Person("B", 0, 30))
    anchors = (
        Anchor("pin-A", "hard", "A", start=16, end=19),
        Anchor("pin-B", "hard", "B", start=16, end=19),
    )
    problem = Problem(people, anchors, small_rules())
    result = solve_problem(problem, time_limit_seconds=5)
    assert result.status == "infeasible"
    assert result.conflict_minimal is True
    assert any("pin-A" in item and "pin-B" in item for item in result.explanation)
    assert any("subset-minimal" in item for item in result.explanation)
    removal_report = next(item for item in result.explanation if "smallest anchor-removal set" in item)
    assert "{pin-A}" in removal_report
    assert "{pin-B}" in removal_report
    assert "all smaller removal sets were tested" in removal_report


def test_scenario_3_soft_anchor_tolerance_and_objective_direction_match_oracle():
    require_backend()
    rules = replace(small_rules(), child_preference_weight=0)
    problem = Problem(
        (Person("A", 0, 30),),
        (Anchor("prefer-start", "soft", "A", start=18, tolerance=0, weight=10),),
        rules,
    )
    result = solve_problem(problem, time_limit_seconds=10)
    assert_matches_oracle(problem, result)
    assert result.solution is not None
    assert result.solution.titular == (Reign("A", 18, 21),)
    assert result.solution.effective == (Reign("A", 18, 21),)


def test_scenario_4_reveal_only_semantics_and_unmarked_contradiction():
    require_backend()
    people = (Person("A", 0, 30), Person("B", 0, 30, ("A",)))
    reveal_only = Problem(people, (Anchor("reveal-B", "reveal", "B", start=16, end=19),), small_rules())
    result = solve_problem(reveal_only, time_limit_seconds=10)
    assert_matches_oracle(reveal_only, result)
    assert result.solution is not None
    assert all(
        next((r.ruler for r in result.solution.effective if r.start <= year <= r.end), None) == "B"
        for year in range(16, 20)
    )
    assert all(
        next((r.ruler for r in result.solution.titular if r.start <= year <= r.end), None) != "B"
        for year in range(16, 20)
    )

    contradictory = Problem(
        people,
        (
            Anchor("record-A", "record", "A", start=16, end=19),
            Anchor("reveal-B", "reveal", "B", start=16, end=19),
        ),
        small_rules(),
    )
    conflict = solve_problem(contradictory, time_limit_seconds=5)
    assert conflict.status == "infeasible"
    assert conflict.conflict_minimal is True
    assert any("record-A" in item and "reveal-B" in item for item in conflict.explanation)


def test_scenario_5_repeatability_and_order_independence():
    require_backend()
    problem = three_person_problem()
    first = solve_problem(problem, time_limit_seconds=10)
    repeated = solve_problem(problem, time_limit_seconds=10)
    reordered = solve_problem(
        replace(problem, people=tuple(reversed(problem.people)), anchors=tuple(reversed(problem.anchors))),
        time_limit_seconds=10,
    )
    assert_matches_oracle(problem, first)
    assert first.solution == repeated.solution == reordered.solution
    assert first.objective == repeated.objective == reordered.objective
