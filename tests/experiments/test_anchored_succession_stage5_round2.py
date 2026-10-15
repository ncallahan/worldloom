from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path

import pytest

from experiments.anchored_succession.checker import check_solution
from experiments.anchored_succession.clingo_backend import solve_problem as solve_clingo
from experiments.anchored_succession.cp_sat import solve_problem as solve_cp_sat
from experiments.anchored_succession.fixtures import generated_parity_instance, generated_pool
from experiments.anchored_succession.model import Anchor, Person, Problem, Rules
from experiments.anchored_succession.objective import evaluate_objective
from experiments.anchored_succession.oracle import optimal_solutions, oracle_result
from experiments.anchored_succession.scenarios import (
    cross_backend_problems, small_rules, stage3_scenarios, tied_optima_problem,
)
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
    result = solve_cp_sat(problem, time_limit_seconds=10, analyze_infeasible=False, encoding=encoding)
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
    result = solve_clingo(problem, time_limit_seconds=10, analyze_infeasible=False, encoding=encoding)
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


def test_50_seeded_long_horizon_instances_match_oracle_and_tie_selection(capsys):
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
        # Enumerate the oracle once per instance; oracle_result() would repeat
        # the same exhaustive search merely to wrap its status/objective.
        optima = optimal_solutions(problem, node_cap=100_000)
        oracle_status = "solved" if optima else "infeasible"
        oracle_objective = min(evaluate_objective(problem, item) for item in optima) if optima else None
        if oracle_status == "solved":
            counts["oracle_feasible"] += 1
            if any(len(solution.titular) >= 2 for solution in optima):
                counts["oracle_optimum_with_two_rulers"] += 1
        else:
            counts["oracle_infeasible"] += 1
        pairs = (
            ("cp-sat", "legacy", solve_cp_sat(problem, time_limit_seconds=10, analyze_infeasible=False, encoding="legacy")),
            ("cp-sat", "linear-successor", solve_cp_sat(problem, time_limit_seconds=10, analyze_infeasible=False, encoding="linear-successor")),
            ("clingo", "legacy", solve_clingo(problem, time_limit_seconds=10, analyze_infeasible=False, encoding="legacy")),
            ("clingo", "aggregate-successor", solve_clingo(problem, time_limit_seconds=10, analyze_infeasible=False, encoding="aggregate-successor")),
        )
        by_backend = {"cp-sat": {}, "clingo": {}}
        for backend, encoding, result in pairs:
            by_backend[backend][encoding] = result
            assert _status(result) == oracle_status, (
                f"instance={index}, seed=20261015, backend={backend}, encoding={encoding}, "
                f"oracle={oracle_status}, actual={result.status}"
            )
            if oracle_status == "infeasible":
                continue
            assert result.solution is not None
            assert check_solution(problem, result.solution) == ()
            assert result.objective == evaluate_objective(problem, result.solution)
            assert result.objective == oracle_objective
            assert result.solution in optima
        if oracle_status == "solved":
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
    with capsys.disabled():
        print(f"Stage 5 parity non-vacuity counts: {summary}; unique-minimum exact-equality checks={exact_equality_checks}")
    assert exact_equality_checks > 0, f"no unique minimum tie-weight cases; {summary}"


def _test_kin_bridge(problem: Problem, source_id: str, target_id: str) -> bool:
    """Directed graph reachability over allowed child/sibling successor edges."""
    people = {p.person_id: p for p in problem.people}
    queue, seen = [source_id], {source_id}
    while queue:
        previous_id = queue.pop(0)
        if previous_id == target_id:
            return True
        previous = people[previous_id]
        for current_id, current in people.items():
            if current_id in seen:
                continue
            if previous_id in current.parents or set(previous.parents) & set(current.parents):
                seen.add(current_id)
                queue.append(current_id)
    return False


@pytest.mark.stage5_heavy
def test_20_larger_instances_compare_legacy_and_improved_without_oracle(tmp_path, capsys):
    """Seeded, non-vacuous two-lineage comparisons; writes per-instance JSON."""
    pytest.importorskip("ortools")
    pytest.importorskip("clingo")
    from worldloom.core import Address, rng_for
    rows = []
    summary = {b: {"both_decided_and_agree": 0, "decided_mismatch": 0,
                   "legacy_timeout_only": 0, "improved_timeout_only": 0,
                   "both_timed_out": 0, "legacy_feasible_unproven_only": 0,
                   "improved_feasible_unproven_only": 0, "both_feasible_unproven": 0,
                   "decided_by_both_encodings": 0}
               for b in ("cp-sat", "clingo")}
    graph_true = graph_false = 0
    for index in range(20):
        size, horizon_end, seed = 10 + index % 3, 60 + index % 21, 20300000 + index
        prefix = f"I{index}-"
        rng = rng_for(seed, "worldloom.anchored_succession.larger", "3",
                      Address(("anchored-succession", "round3-larger", str(index))), "lineages")
        people = [Person(prefix+"L0", -100, horizon_end+10), Person(prefix+"R0", -100, horizon_end+10)]
        split = 2 + (size - 2) // 2
        for j in range(2, size):
            root = prefix+("L0" if j < split else "R0")
            parents = (root,)
            if index % 4 == 0 and j == size - 1:
                parents = (prefix+"R0", prefix+"P2")
            people.append(Person(prefix+f"P{j}", -40+rng.randint(0, 2), horizon_end+10, parents))
        ids = [p.person_id for p in people]
        assert len(ids) == len(set(ids)), f"instance={index}: duplicate person ids"
        rules = Rules(min_accession_age=16, min_reign=3, max_reign=20, preferred_reign=8,
                      horizon_start=0, horizon_end=horizon_end, child_preference_weight=1, stability_weight=0)
        first_id, last_id = prefix+"P2", prefix+f"P{size-1}"
        anchors = (Anchor(f"r3-{index}-first", "hard", first_id, start=0, end=3),
                   Anchor(f"r3-{index}-last", "hard", last_id, start=horizon_end-3, end=horizon_end))
        assert len({a.anchor_id for a in anchors}) == len(anchors)
        problem = Problem(tuple(people), anchors, rules, seed=seed)
        nonkin = sum(1 for a in people for b in people if a.person_id != b.person_id
                     and a.person_id not in b.parents and not (set(a.parents) & set(b.parents)))
        assert nonkin > 0, f"instance={index}: non-kin succession family is empty"
        bridge = _test_kin_bridge(problem, first_id, last_id)
        graph_true += int(bridge); graph_false += int(not bridge)
        instance = {"index": index, "seed": seed, "people": size, "horizon_years": horizon_end+1,
                    "ordered_nonkin_pairs": nonkin, "kin_bridge_exists": bridge,
                    "anchors": [{"id": a.anchor_id, "person_id": a.person_id, "start": a.start, "end": a.end} for a in anchors],
                    "backends": {}}
        for backend, solver, legacy_name, improved_name in (
            ("cp-sat", solve_cp_sat, "legacy", "linear-successor"),
            ("clingo", solve_clingo, "legacy", "aggregate-successor")):
            outcomes = {}
            for encoding in (legacy_name, improved_name):
                started = __import__("time").perf_counter()
                result = solver(problem, time_limit_seconds=5, encoding=encoding)
                elapsed = __import__("time").perf_counter() - started
                status = result.status if result.status == "feasible" else _status(result)
                if result.solution is not None:
                    assert check_solution(problem, result.solution) == (), f"{index}/{backend}/{encoding}: checker rejected"
                    assert result.objective == evaluate_objective(problem, result.solution)
                outcomes[encoding] = {"status": status, "raw_status": result.status, "objective": result.objective,
                    "wall_time_seconds": elapsed, "time_limit_seconds": 5, "solution_present": result.solution is not None,
                    "grounding_time_seconds": getattr(result, "grounding_time_seconds", None),
                    "solve_time_seconds": getattr(result, "solve_time_seconds", None),
                    "time_to_first_solution_seconds": getattr(result, "time_to_first_solution_seconds", None),
                    "time_to_proven_optimal_seconds": getattr(result, "time_to_proven_optimal_seconds", None),
                    "proven_optimal": result.status in ("solved", "optimal")}
            legacy, improved = outcomes[legacy_name], outcomes[improved_name]
            ld, id_ = legacy["status"] in ("solved", "infeasible"), improved["status"] in ("solved", "infeasible")
            if not bridge:
                assert legacy["status"] == improved["status"] == "infeasible", (
                    f"no kin bridge but not proven infeasible: instance={index}, backend={backend}, outcomes={outcomes}")
            if ld and id_:
                summary[backend]["decided_by_both_encodings"] += 1
                mismatch = legacy["status"] != improved["status"]
                if not mismatch and legacy["status"] == "solved":
                    mismatch = legacy["objective"] != improved["objective"]
                if mismatch:
                    summary[backend]["decided_mismatch"] += 1
                else:
                    summary[backend]["both_decided_and_agree"] += 1
            elif not ld and not id_:
                if legacy["status"] == improved["status"] == "feasible":
                    summary[backend]["both_feasible_unproven"] += 1
                elif legacy["status"] == "feasible":
                    summary[backend]["legacy_feasible_unproven_only"] += 1
                elif improved["status"] == "feasible":
                    summary[backend]["improved_feasible_unproven_only"] += 1
                else:
                    summary[backend]["both_timed_out"] += 1
            elif not ld:
                if legacy["status"] == "feasible":
                    summary[backend]["legacy_feasible_unproven_only"] += 1
                else:
                    summary[backend]["legacy_timeout_only"] += 1
            else:
                if improved["status"] == "feasible":
                    summary[backend]["improved_feasible_unproven_only"] += 1
                else:
                    summary[backend]["improved_timeout_only"] += 1
            instance["backends"][backend] = {"legacy_encoding": legacy_name, "improved_encoding": improved_name,
                                               "legacy": legacy, "improved": improved}
        rows.append(instance)
    assert graph_true > 0 and graph_false > 0, f"must include bridged and unbridged instances: {graph_true}/{graph_false}"
    for backend, counts in summary.items():
        assert counts["decided_by_both_encodings"] >= 15, (
            f"{backend}: fewer than 15/20 decided by both encodings; counts={counts}; investigate encoding-specific timeouts")
    result_path = Path(os.environ.get("WORLDLOOM_STAGE5_RESULTS_JSON", "stage5_larger_comparisons.json"))
    result_path.write_text(json.dumps({"ci_run_id": os.environ.get("GITHUB_RUN_ID"),
        "test": "test_20_larger_instances_compare_legacy_and_improved_without_oracle",
        "per_solve_time_limit_seconds": 5, "instances": rows, "summary": summary,
        "graph_check": {"bridged_instances": graph_true, "unbridged_instances": graph_false,
                        "soundness_violations": 0}}, indent=2) + "\n", encoding="utf-8")
    with capsys.disabled():
        print("Stage 5 larger comparison summary: " + json.dumps(summary, sort_keys=True))
        print(f"Stage 5 results JSON: {result_path}")
    assert all(counts["decided_mismatch"] == 0 for counts in summary.values()), (
        "decided legacy/improved mismatch; per-instance JSON written to " + str(result_path) + ": " + json.dumps(summary)
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
        assert any(
            "conflicting anchor subset" in line and "pin-A" in line and "pin-B" in line
            for line in legacy.explanation
        ), (backend, legacy.explanation)
        removal_lines = [
            line for line in legacy.explanation if "Exploratory smallest anchor-removal set(s)" in line
        ]
        assert len(removal_lines) == 1, (backend, legacy.explanation)
        assert "{pin-A}" in removal_lines[0] and "{pin-B}" in removal_lines[0], (
            backend, removal_lines[0]
        )



@pytest.mark.parametrize(("backend", "solver", "encodings"), [
    ("cp-sat", solve_cp_sat, CP_ENCODINGS),
    ("clingo", solve_clingo, CLINGO_ENCODINGS),
])
def test_scenarios_1_to_7_and_objective_parity_under_both_encodings(backend, solver, encodings):
    pytest.importorskip("ortools")
    pytest.importorskip("clingo")
    cases = {**stage3_scenarios(), **cross_backend_problems()}
    findings = []
    for encoding in encodings:
        for name, problem in cases.items():
            oracle = oracle_result(problem, node_cap=100_000)
            result = solver(problem, time_limit_seconds=10, encoding=encoding)
            if _status(result) != oracle.status:
                findings.append(
                    f"{backend}/{encoding}/{name}: status={result.status}, oracle={oracle.status}"
                )
                continue
            if oracle.status == "infeasible":
                continue
            optima = optimal_solutions(problem, node_cap=100_000)
            if result.solution is None:
                findings.append(f"{backend}/{encoding}/{name}: no solution returned")
                continue
            if check_solution(problem, result.solution):
                findings.append(f"{backend}/{encoding}/{name}: independent checker rejected solution")
            if result.objective != evaluate_objective(problem, result.solution):
                findings.append(f"{backend}/{encoding}/{name}: objective disagrees with evaluator")
            if result.objective != min(evaluate_objective(problem, item) for item in optima):
                findings.append(f"{backend}/{encoding}/{name}: objective disagrees with oracle optimum")
            if result.solution not in optima:
                findings.append(f"{backend}/{encoding}/{name}: selected solution not in oracle optimal set")
    assert not findings, "encoding scenario/objective findings:\\n" + "\\n".join(findings)


@pytest.mark.parametrize(("backend", "solver", "encodings"), [
    ("cp-sat", solve_cp_sat, CP_ENCODINGS),
    ("clingo", solve_clingo, CLINGO_ENCODINGS),
])
def test_tied_optima_shuffle_and_seed_positive_control_under_both_encodings(backend, solver, encodings):
    pytest.importorskip("ortools")
    pytest.importorskip("clingo")
    problem = tied_optima_problem()
    optima = optimal_solutions(problem, node_cap=100_000)
    assert len(optima) > 1, "non-vacuity guard: tied-optima fixture must have multiple optima"
    selected_across_seeds = set()
    for encoding in encodings:
        reference = solver(problem, time_limit_seconds=10, encoding=encoding)
        assert _status(reference) == "solved" and reference.solution in optima
        assert reference.objective == evaluate_objective(problem, reference.solution)
        assert check_solution(problem, reference.solution) == ()
        for order_seed in (3, 17, 2026, 91003):
            shuffled = solver(
                problem, time_limit_seconds=10, encoding=encoding,
                canonical_order=False, order_seed=order_seed,
            )
            assert _status(shuffled) == "solved" and shuffled.solution in optima
            assert shuffled.solution == reference.solution, (
                f"{backend}/{encoding}: shuffled model changed tied-optimum selection at {order_seed}"
            )
            assert shuffled.objective == reference.objective
        for problem_seed in (1, 2, 3, 5, 8, 13, 21, 34, 55, 89):
            seeded = replace(problem, seed=problem_seed)
            seeded_optima = optimal_solutions(seeded, node_cap=100_000)
            assert len(seeded_optima) > 1
            result = solver(seeded, time_limit_seconds=10, encoding=encoding)
            assert _status(result) == "solved" and result.solution in seeded_optima
            assert result.objective == evaluate_objective(seeded, result.solution)
            assert check_solution(seeded, result.solution) == ()
            selected_across_seeds.add((backend, encoding, problem_seed, result.solution))
    for encoding in encodings:
        selected = {item[3] for item in selected_across_seeds if item[1] == encoding}
        assert len(selected) > 1, f"{backend}/{encoding}: keyed seed positive control did not vary"


@pytest.mark.parametrize(("backend", "solver", "encodings"), [
    ("cp-sat", solve_cp_sat, CP_ENCODINGS),
    ("clingo", solve_clingo, CLINGO_ENCODINGS),
])
def test_missing_soft_ruler_objective_parity_under_both_encodings(backend, solver, encodings):
    pytest.importorskip("ortools")
    pytest.importorskip("clingo")
    problem = Problem(
        (Person("A", 0, 80), Person("C", 60, 80)),
        (Anchor("soft-missing", "soft", "C", start=16, tolerance=5, weight=2),),
        replace(small_rules(), horizon_end=80, child_preference_weight=0),
    )
    optima = optimal_solutions(problem, node_cap=100_000)
    for encoding in encodings:
        result = solver(problem, time_limit_seconds=10, encoding=encoding)
        assert _status(result) == "solved", (backend, encoding, result.explanation)
        assert result.solution is not None
        assert check_solution(problem, result.solution) == ()
        assert result.objective == evaluate_objective(problem, result.solution)
        assert result.objective == min(evaluate_objective(problem, item) for item in optima)
