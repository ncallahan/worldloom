from __future__ import annotations

from dataclasses import replace

import pytest

from experiments.anchored_succession.checker import check_solution
from experiments.anchored_succession.clingo_backend import solve_problem as solve_clingo
from experiments.anchored_succession.cp_sat import solve_problem as solve_cp_sat
from experiments.anchored_succession.fixtures import generated_parity_instance, generated_pool
from experiments.anchored_succession.model import Anchor, Person, Problem, Rules
from experiments.anchored_succession.objective import evaluate_objective
from experiments.anchored_succession.oracle import optimal_solutions, oracle_result
from experiments.anchored_succession.scenarios import small_rules
from experiments.anchored_succession.tie_break import cp_sat_tie_coefficient, clingo_tie_weight


CP_ENCODINGS = ("legacy", "linear-successor")
CLINGO_ENCODINGS = ("legacy", "aggregate-successor")


def _status(result) -> str:
    if result.status in ("solved", "optimal", "feasible"):
        return "solved"
    if result.status == "infeasible":
        return "infeasible"
    return result.status


def _succession_cases() -> tuple[tuple[str, Problem, str], ...]:
    rules = small_rules()
    no_bridge = Problem(
        (Person("A", -40, 19), Person("Z", -40, 30)),
        (Anchor("first", "hard", "A", start=16, end=19),
         Anchor("last", "hard", "Z", start=25, end=28)),
        rules,
        seed=20261015,
    )
    kin_bridge = Problem(
        (Person("A", -40, 19), Person("B", -10, 24, ("A",)),
         Person("Z", -5, 30, ("B",))),
        (Anchor("first", "hard", "A", start=16, end=19),
         Anchor("last", "hard", "Z", start=25, end=28)),
        rules,
        seed=20261016,
    )
    only_nonkin_successor = Problem(
        (Person("A", -40, 24), Person("N", -30, 30)),
        (Anchor("first", "hard", "A", start=16, end=19),
         Anchor("last", "hard", "N", start=25, end=28)),
        rules,
        seed=20261017,
    )
    return (
        ("unrelated rulers with no bridge", no_bridge, "infeasible"),
        ("kin bridge", kin_bridge, "solved"),
        ("only candidate successor is non-kin", only_nonkin_successor, "infeasible"),
    )


@pytest.mark.parametrize(("label", "problem", "expected"), _succession_cases())
@pytest.mark.parametrize("encoding", CP_ENCODINGS)
def test_cp_sat_encodings_exercise_succession_cases(label, problem, expected, encoding):
    pytest.importorskip("ortools")
    oracle = oracle_result(problem, node_cap=100_000)
    assert oracle.status == expected, label
    result = solve_cp_sat(problem, time_limit_seconds=10, encoding=encoding)
    assert _status(result) == oracle.status, (label, encoding, result.explanation)
    if expected == "solved":
        optima = optimal_solutions(problem, node_cap=100_000)
        assert result.solution is not None
        assert check_solution(problem, result.solution) == ()
        assert result.objective == evaluate_objective(problem, result.solution)
        assert result.objective == min(evaluate_objective(problem, item) for item in optima)
        assert result.solution in optima


@pytest.mark.parametrize(("label", "problem", "expected"), _succession_cases())
@pytest.mark.parametrize("encoding", CLINGO_ENCODINGS)
def test_clingo_encodings_exercise_succession_cases(label, problem, expected, encoding):
    pytest.importorskip("clingo")
    oracle = oracle_result(problem, node_cap=100_000)
    assert oracle.status == expected, label
    result = solve_clingo(problem, time_limit_seconds=10, encoding=encoding)
    assert _status(result) == oracle.status, (label, encoding, result.explanation)
    if expected == "solved":
        optima = optimal_solutions(problem, node_cap=100_000)
        assert result.solution is not None
        assert check_solution(problem, result.solution) == ()
        assert result.objective == evaluate_objective(problem, result.solution)
        assert result.objective == min(evaluate_objective(problem, item) for item in optima)
        assert result.solution in optima


def _tie_score(problem: Problem, solution, backend: str) -> int:
    score = 0
    for layer, reigns in (("titular", solution.titular), ("effective", solution.effective)):
        for reign in reigns:
            for year in range(reign.start, reign.end + 1):
                if backend == "cp-sat":
                    score += cp_sat_tie_coefficient(problem.seed, layer, reign.ruler, year)
                else:
                    score += clingo_tie_weight(
                        problem.seed, problem.generator_id, problem.generator_version,
                        layer, reign.ruler, year,
                    )
    return score


def test_50_seeded_long_horizon_instances_match_oracle_and_tie_selection():
    pytest.importorskip("ortools")
    pytest.importorskip("clingo")
    counts = {
        "at_least_two_possible_rulers": 0,
        "oracle_feasible": 0,
        "oracle_infeasible": 0,
        "oracle_optimum_with_two_rulers": 0,
    }
    exact_equality_checks = 0
    for index in range(50):
        problem = generated_parity_instance(index, seed=20261015)
        assert 40 <= problem.rules.horizon_end <= 60
        assert len(problem.people) <= 6
        possible = [
            p for p in problem.people
            if max(problem.rules.horizon_start, p.birth + problem.rules.min_accession_age)
            <= min(problem.rules.horizon_end, p.death) - problem.rules.min_reign + 1
        ]
        if len(possible) >= 2:
            counts["at_least_two_possible_rulers"] += 1
        oracle = oracle_result(problem, node_cap=100_000)
        optima = optimal_solutions(problem, node_cap=100_000)
        if oracle.status == "solved":
            counts["oracle_feasible"] += 1
            if any(len(solution.titular) >= 2 for solution in optima):
                counts["oracle_optimum_with_two_rulers"] += 1
        else:
            counts["oracle_infeasible"] += 1
        pairs = (
            ("cp-sat", "legacy", solve_cp_sat(problem, time_limit_seconds=10, encoding="legacy")),
            ("cp-sat", "linear-successor", solve_cp_sat(problem, time_limit_seconds=10, encoding="linear-successor")),
            ("clingo", "legacy", solve_clingo(problem, time_limit_seconds=10, encoding="legacy")),
            ("clingo", "aggregate-successor", solve_clingo(problem, time_limit_seconds=10, encoding="aggregate-successor")),
        )
        by_backend = {"cp-sat": {}, "clingo": {}}
        for backend, encoding, result in pairs:
            by_backend[backend][encoding] = result
            assert _status(result) == oracle.status, (
                f"instance={index}, seed=20261015, backend={backend}, encoding={encoding}, "
                f"oracle={oracle.status}, actual={result.status}"
            )
            if oracle.status == "infeasible":
                continue
            assert result.solution is not None
            assert check_solution(problem, result.solution) == ()
            assert result.objective == evaluate_objective(problem, result.solution)
            assert result.objective == min(evaluate_objective(problem, item) for item in optima)
            assert result.solution in optima
        if oracle.status == "solved":
            for backend, legacy_name, improved_name in (
                ("cp-sat", "legacy", "linear-successor"),
                ("clingo", "legacy", "aggregate-successor"),
            ):
                scores = [_tie_score(problem, item, backend) for item in optima]
                minimum = min(scores)
                if scores.count(minimum) == 1:
                    exact_equality_checks += 1
                    assert (
                        by_backend[backend][legacy_name].solution
                        == by_backend[backend][improved_name].solution
                    ), (
                        f"unique minimum keyed tie weight but solution differs: "
                        f"instance={index}, seed=20261015, backend={backend}, minimum={minimum}"
                    )
    summary = ", ".join(f"{key}={value}/50" for key, value in counts.items())
    assert counts["at_least_two_possible_rulers"] > 0, summary
    assert counts["oracle_feasible"] > 0, summary
    assert counts["oracle_infeasible"] > 0, summary
    assert counts["oracle_optimum_with_two_rulers"] > 0, summary
    assert exact_equality_checks > 0, f"no unique minimum tie-weight cases; {summary}"


@pytest.mark.parametrize("index", range(20))
def test_20_larger_instances_compare_legacy_and_improved_without_oracle(index):
    pytest.importorskip("ortools")
    pytest.importorskip("clingo")
    size = 10 + (index % 3)
    horizon_end = 60 + (index % 21)
    generated = generated_pool(size, seed=20300000 + index)
    problem = replace(
        generated,
        rules=replace(generated.rules, horizon_start=0, horizon_end=horizon_end),
        anchors=(),
        seed=20300000 + index,
    )
    cp_legacy = solve_cp_sat(problem, time_limit_seconds=20, encoding="legacy")
    cp_improved = solve_cp_sat(problem, time_limit_seconds=20, encoding="linear-successor")
    asp_legacy = solve_clingo(problem, time_limit_seconds=20, encoding="legacy")
    asp_improved = solve_clingo(problem, time_limit_seconds=20, encoding="aggregate-successor")
    for backend, legacy, improved in (
        ("cp-sat", cp_legacy, cp_improved), ("clingo", asp_legacy, asp_improved)
    ):
        assert _status(legacy) == _status(improved), (
            f"index={index}, size={size}, horizon={horizon_end}, backend={backend}, "
            f"legacy={legacy.status}, improved={improved.status}"
        )
        if _status(legacy) == "solved":
            assert legacy.solution is not None and improved.solution is not None
            assert check_solution(problem, legacy.solution) == ()
            assert check_solution(problem, improved.solution) == ()
            assert legacy.objective == evaluate_objective(problem, legacy.solution)
            assert improved.objective == evaluate_objective(problem, improved.solution)
            assert legacy.objective == improved.objective, (
                f"index={index}, size={size}, horizon={horizon_end}, backend={backend}, "
                f"objectives={legacy.objective}/{improved.objective}"
            )


def test_scenario_2_conflict_cores_and_exact_removal_sets_match_across_encodings():
    pytest.importorskip("ortools")
    pytest.importorskip("clingo")
    people = (Person("A", 0, 30), Person("B", 0, 30))
    problem = Problem(
        people,
        (Anchor("pin-A", "hard", "A", start=16, end=19),
         Anchor("pin-B", "hard", "B", start=16, end=19)),
        small_rules(),
    )
    for backend, solver, encodings in (
        ("cp-sat", solve_cp_sat, CP_ENCODINGS),
        ("clingo", solve_clingo, CLINGO_ENCODINGS),
    ):
        results = {
            encoding: solver(problem, time_limit_seconds=10, encoding=encoding)
            for encoding in encodings
        }
        legacy, improved = results.values()
        assert legacy.status == improved.status == "infeasible", backend
        assert legacy.conflict_minimal == improved.conflict_minimal is True, backend
        assert legacy.explanation == improved.explanation, (backend, legacy.explanation, improved.explanation)
