from __future__ import annotations

import os
import pytest
from dataclasses import replace
from types import SimpleNamespace

from experiments.anchored_succession.checker import check_solution
from experiments.anchored_succession.model import Anchor, Person, Problem, Reign, Rules
from experiments.anchored_succession.objective import evaluate_objective
from experiments.anchored_succession.oracle import optimal_solutions
from experiments.anchored_succession.cp_sat import _map_cp_sat_status, solve_problem
from experiments.anchored_succession.scenarios import tied_optima_problem
from experiments.anchored_succession.tie_break import cp_sat_tie_coefficient


def small_rules() -> Rules:
    return Rules(
        min_accession_age=16, min_reign=3, max_reign=8, preferred_reign=4,
        horizon_start=0, horizon_end=30, child_preference_weight=1, stability_weight=0,
    )


def three_person_problem(include_soft: bool = False) -> Problem:
    people = (
        Person("A", 0, 30),
        Person("B", 2, 30, ("A",)),
        Person("C", 3, 30, ("A",)),
    )
    anchors = [Anchor("pin-A", "hard", "A", start=16, end=19)]
    if include_soft:
        anchors.append(Anchor("prefer-B", "soft", "B", start=20, tolerance=0, weight=1))
    return Problem(people, tuple(anchors), small_rules(), seed=20261013)


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
    problem = three_person_problem(include_soft=False)
    assert all(anchor.kind == "hard" for anchor in problem.anchors)
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
    assert removal_report.count("(resulting objective 0)") == 2
    assert "all smaller removal sets were tested" in removal_report


def test_scenario_3_soft_anchor_tolerance_cost_and_direction_match_oracle():
    require_backend()
    rules = replace(small_rules(), child_preference_weight=0)
    inside_tolerance = Problem(
        (Person("A", 0, 30),),
        (Anchor("prefer-start", "soft", "A", start=18, tolerance=2, weight=10),),
        rules,
    )
    inside = solve_problem(inside_tolerance, time_limit_seconds=10)
    assert_matches_oracle(inside_tolerance, inside)
    assert inside.solution is not None
    start = inside.solution.titular[0].start
    assert 18 - 2 <= start <= 18 + 2
    assert inside.objective == 0

    outside_tolerance = Problem(
        (Person("A", 0, 30),),
        (
            Anchor("pin-start", "hard", "A", lower=24, upper=24),
            Anchor("pin-span", "hard", "A", start=24, end=27),
            Anchor("prefer-start", "soft", "A", start=18, tolerance=2, weight=7),
        ),
        rules,
    )
    outside = solve_problem(outside_tolerance, time_limit_seconds=10)
    assert_matches_oracle(outside_tolerance, outside)
    assert outside.solution is not None
    assert outside.solution.titular == (Reign("A", 24, 27),)
    assert outside.objective == 7 * (abs(24 - 18) - 2)

    direction_problem = Problem(
        (Person("A", 0, 30), Person("B", 0, 30, ("A",))),
        (Anchor("pin-A", "hard", "A", start=16, end=19),
         Anchor("prefer-B", "soft", "B", start=25, tolerance=0, weight=10)),
        rules,
    )
    with_soft = solve_problem(direction_problem, time_limit_seconds=10)
    without_soft_problem = replace(
        direction_problem,
        anchors=tuple(anchor for anchor in direction_problem.anchors if anchor.kind != "soft"),
    )
    without_soft = solve_problem(without_soft_problem, time_limit_seconds=10)
    assert_matches_oracle(direction_problem, with_soft)
    assert_matches_oracle(without_soft_problem, without_soft)
    assert with_soft.solution is not None and without_soft.solution is not None
    assert with_soft.solution != without_soft.solution
    assert with_soft.objective > without_soft.objective
    assert any(reign.ruler == "B" for reign in with_soft.solution.titular)
    assert all(reign.ruler != "B" for reign in without_soft.solution.titular)
    assert with_soft.objective < 10 * (small_rules().horizon_end - small_rules().horizon_start + 1)


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

    marked_record = Problem(
        people,
        (
            Anchor("record-A", "record", "A", start=16, end=19, marked_reveal=True),
            Anchor("reveal-B", "reveal", "B", start=16, end=19),
        ),
        small_rules(),
    )
    marked_result = solve_problem(marked_record, time_limit_seconds=10)
    assert_matches_oracle(marked_record, marked_result)

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


def test_cp_sat_objective_parity_includes_sibling_and_stability_costs():
    require_backend()
    people = (
        Person("A", 0, 30),
        Person("B", 0, 30, ("A",)),
        Person("C", 0, 30, ("A",)),
    )
    rules = replace(small_rules(), child_preference_weight=7, stability_weight=3)
    anchors = (
        Anchor("pin-B", "hard", "B", start=16, end=19),
        Anchor("pin-C", "hard", "C", start=20, end=23),
    )
    reference = (Reign("A", 16, 19), Reign("C", 20, 23))
    problem = Problem(people, anchors, rules, stability_reference=reference)
    result = solve_problem(problem, time_limit_seconds=10)
    assert_matches_oracle(problem, result)
    assert result.objective == 26


def test_cp_sat_objective_parity_for_missing_soft_ruler_with_positive_tolerance():
    require_backend()
    people = (Person("A", 0, 30), Person("C", 30, 30))
    problem = Problem(
        people,
        (Anchor("soft-missing", "soft", "C", start=16, tolerance=5, weight=2),),
        replace(small_rules(), child_preference_weight=0),
    )
    result = solve_problem(problem, time_limit_seconds=10)
    assert_matches_oracle(problem, result)
    assert result.objective == 62


def test_scenario_5_repeatability_and_order_independence():
    require_backend()
    problem = three_person_problem(include_soft=True)
    first = solve_problem(problem, time_limit_seconds=10)
    repeated = solve_problem(problem, time_limit_seconds=10)
    assert_matches_oracle(problem, first)
    assert first.solution == repeated.solution
    assert first.objective == repeated.objective
    for seed in (3, 17, 2026, 91003):
        shuffled = solve_problem(
            problem, time_limit_seconds=10, canonical_order=False, order_seed=seed
        )
        assert_matches_oracle(problem, shuffled)
        assert shuffled.solution == first.solution, f"selected solution changed for shuffled model seed {seed}"
        assert shuffled.objective == first.objective, f"objective changed for shuffled model seed {seed}"



def test_cp_sat_status_mapping_distinguishes_timeout_from_unknown_with_or_without_incumbent():
    codes = SimpleNamespace(OPTIMAL=0, FEASIBLE=1, INFEASIBLE=2, UNKNOWN=3, MODEL_INVALID=4)
    assert _map_cp_sat_status(codes.OPTIMAL, codes, time_limit_reached=True) == "optimal"
    assert _map_cp_sat_status(codes.FEASIBLE, codes, time_limit_reached=False) == "feasible"
    assert _map_cp_sat_status(codes.FEASIBLE, codes, time_limit_reached=True) == "timeout"
    assert _map_cp_sat_status(codes.UNKNOWN, codes, time_limit_reached=False) == "unknown"
    assert _map_cp_sat_status(codes.UNKNOWN, codes, time_limit_reached=True) == "timeout"
    assert _map_cp_sat_status(codes.INFEASIBLE, codes, time_limit_reached=True) == "infeasible"
    assert _map_cp_sat_status(codes.MODEL_INVALID, codes, time_limit_reached=True) == "model_invalid"


def test_anchor_removal_analysis_reports_infeasibility_independent_of_anchors():
    require_backend()
    rules = replace(small_rules(), horizon_start=0, horizon_end=30, min_accession_age=16)
    problem = Problem(
        (Person("too-young", 20, 30),),
        (Anchor("pin-too-young", "hard", "too-young", start=16, end=19),),
        rules,
    )
    result = solve_problem(problem, time_limit_seconds=5)
    assert result.status == "infeasible"
    assert any("infeasible independent of anchors" in item for item in result.explanation)
    assert not any("smallest anchor-removal set" in item for item in result.explanation)


def test_cp_sat_model_size_is_reported_from_model_proto():
    require_backend()
    from experiments.anchored_succession.cp_sat import _build_model

    built = _build_model(three_person_problem())
    proto = built["model"].Proto()
    assert built["model_variables"] == len(proto.variables)
    assert built["model_constraints"] == len(proto.constraints)


def test_tied_optima_order_independence_and_seed_positive_control():
    require_backend()
    problem = tied_optima_problem()
    optima = optimal_solutions(problem, node_cap=100_000)
    assert len(optima) > 1, "non-vacuity guard: problem must have multiple real-optimal solutions"
    reference = solve_problem(problem, time_limit_seconds=10)
    _assert_unique_tie_minimum(problem, optima)
    assert_matches_oracle(problem, reference)
    assert reference.solution in optima
    for order_seed in (3, 17, 2026, 91003):
        shuffled = solve_problem(problem, time_limit_seconds=10, canonical_order=False, order_seed=order_seed)
        assert_matches_oracle(problem, shuffled)
        assert shuffled.solution in optima
        assert shuffled.solution == reference.solution, f"tied-optimum selection changed for shuffled model seed {order_seed}"
    selected = set()
    for problem_seed in (1, 2, 3, 5, 8, 13, 21, 34, 55, 89):
        seeded = replace(problem, seed=problem_seed)
        seeded_optima = optimal_solutions(seeded, node_cap=100_000)
        assert len(seeded_optima) > 1
        _assert_unique_tie_minimum(seeded, seeded_optima)
        result = solve_problem(seeded, time_limit_seconds=10)
        assert_matches_oracle(seeded, result)
        assert result.solution in seeded_optima
        selected.add(result.solution)
    assert len(selected) > 1, "positive control: keyed perturbation did not vary across problem.seed values"


def _assert_unique_tie_minimum(problem, optima):
    def score(solution):
        return sum(
            cp_sat_tie_coefficient(problem.seed, layer, reign.ruler, year)
            for layer, reigns in (("titular", solution.titular), ("effective", solution.effective))
            for reign in reigns
            for year in range(reign.start, reign.end + 1)
        )
    scores = [score(solution) for solution in optima]
    minimum = min(scores)
    tied = [solution for solution, value in zip(optima, scores) if value == minimum]
    assert len(tied) == 1, (
        f"residual CP-SAT tie-weight collision at problem.seed={problem.seed}: "
        f"minimum weight {minimum} attained by {len(tied)} oracle-optimal solutions"
    )


@pytest.mark.parametrize("size", [3])
def test_linear_successor_encoding_matches_legacy_and_oracle(size):
    require_backend()
    problem = three_person_problem(include_soft=True)
    legacy = solve_problem(problem, time_limit_seconds=10, encoding="legacy")
    improved = solve_problem(problem, time_limit_seconds=10, encoding="linear-successor")
    optima = optimal_solutions(problem, node_cap=100_000)
    assert legacy.status == improved.status == "solved"
    assert legacy.solution is not None and improved.solution is not None
    assert check_solution(problem, legacy.solution) == ()
    assert check_solution(problem, improved.solution) == ()
    assert legacy.objective == evaluate_objective(problem, legacy.solution)
    assert improved.objective == evaluate_objective(problem, improved.solution)
    assert legacy.objective == improved.objective == min(
        evaluate_objective(problem, candidate) for candidate in optima
    )
    assert legacy.solution in optima and improved.solution in optima


def test_linear_successor_encoding_construction_is_smaller_than_pairwise_baseline():
    require_backend()
    from experiments.anchored_succession.cp_sat import _build_model
    problem = three_person_problem(include_soft=True)
    legacy = _build_model(problem, encoding="legacy")
    improved = _build_model(problem, encoding="linear-successor")
    assert improved["model_constraints"] < legacy["model_constraints"]
