from __future__ import annotations

import os
from dataclasses import replace

import pytest

from experiments.anchored_succession.checker import check_solution
from experiments.anchored_succession.clingo_backend import solve_problem as solve_clingo
from experiments.anchored_succession.cp_sat import solve_problem as solve_cp_sat
from experiments.anchored_succession.model import Anchor, Person, Problem, Result
from experiments.anchored_succession.objective import evaluate_objective
from experiments.anchored_succession.oracle import optimal_solutions
from experiments.anchored_succession.reconcile import (
    InconclusiveReconciliationError, changed_facts, problem_fingerprint, promote,
    projection_from_result, reconcile,
)
from experiments.anchored_succession.scenarios import three_person_problem


def _solve(problem, backend):
    try:
        if backend == "cp-sat":
            import ortools  # noqa: F401
        else:
            import clingo  # noqa: F401
    except ImportError:
        env_name = "WORLDLOOM_REQUIRE_CP_SAT" if backend == "cp-sat" else "WORLDLOOM_REQUIRE_CLINGO"
        if os.environ.get(env_name) == "1":
            pytest.fail(f"{backend} backend missing while {env_name}=1")
        pytest.skip(f"optional {backend} dependency is not installed outside its CI gate")
    return solve_cp_sat(problem, time_limit_seconds=10) if backend == "cp-sat" else solve_clingo(problem, time_limit_seconds=10)


def _projection(problem, backend):
    result = _solve(problem, backend)
    assert result.status in ("solved", "feasible") and result.solution is not None
    assert check_solution(problem, result.solution) == ()
    return projection_from_result(problem, result)


@pytest.mark.parametrize("backend", ["cp-sat", "clingo"])
@pytest.mark.parametrize("status", ["current", "reopened", "obsolete"])
def test_unchanged_fingerprint_preserves_status_without_solver_call(monkeypatch, backend, status):
    problem = three_person_problem()
    projection = _projection(problem, backend)
    previous = replace(projection, status=status, explanation=("retain this record",))
    import experiments.anchored_succession.reconcile as module
    monkeypatch.setattr(module, "_solve", lambda *args: pytest.fail("unchanged fingerprint must not call solver"))
    assert reconcile(previous, problem, backend) == previous


@pytest.mark.parametrize("backend", ["cp-sat", "clingo"])
def test_changed_feasible_problem_reopens_with_independent_fact_diff(backend):
    old_problem = three_person_problem()
    previous = _projection(old_problem, backend)
    new_problem = replace(old_problem, anchors=old_problem.anchors + (
        Anchor("prefer-C", "soft", "C", start=24, tolerance=0, weight=3),
    ))
    result = reconcile(previous, new_problem, backend)
    assert result.status == "reopened"
    assert result.problem_fingerprint == problem_fingerprint(new_problem)
    assert result.last_checked_fingerprint == problem_fingerprint(new_problem)
    assert check_solution(new_problem, result.solution) == ()
    assert result.objective == evaluate_objective(new_problem, result.solution)
    added, removed = changed_facts(previous.solution, result.solution)
    assert result.changed_facts_added == added
    assert result.changed_facts_removed == removed
    assert "proposal" in result.explanation[-1].lower()
    optima = optimal_solutions(new_problem, node_cap=100_000)
    assert result.solution in optima


@pytest.mark.parametrize("backend", ["cp-sat", "clingo"])
def test_obsolete_then_reopened_after_owner_removes_conflict_with_exact_explanation(backend):
    problem = Problem(
        people=(Person("A", 0, 30), Person("C", 0, 30, ("A",))),
        anchors=(Anchor("pin-A", "hard", "A", start=16, end=19),),
        rules=three_person_problem().rules,
        seed=20261013,
    )
    previous = _projection(problem, backend)
    conflict = replace(problem, anchors=problem.anchors + (
        Anchor("conflicting-C", "hard", "C", start=16, end=19, source="owner-test"),
    ))
    obsolete = reconcile(previous, conflict, backend)
    assert obsolete.status == "obsolete"
    assert obsolete.solution == previous.solution
    assert obsolete.problem_fingerprint == problem_fingerprint(problem)
    assert obsolete.last_checked_fingerprint == problem_fingerprint(conflict)
    prefix = "CP-SAT" if backend == "cp-sat" else "clingo"
    assert f"{prefix} conflicting anchor subset: conflicting-C, pin-A" in obsolete.explanation
    removal_line = next(line for line in obsolete.explanation if line.startswith("Exploratory smallest anchor-removal set(s):"))
    if backend == "cp-sat":
        assert removal_line == (
            "Exploratory smallest anchor-removal set(s): {conflicting-C} (resulting objective 0); "
            "{pin-A} (resulting objective 0). Minimality evidence: all smaller removal sets were tested "
            "and remained infeasible; this is an authorial intervention suggestion, not an automatic edit."
        )
    else:
        assert removal_line == (
            "Exploratory smallest anchor-removal set(s): {conflicting-C} (resulting objective 0); "
            "{pin-A} (resulting objective 0). All smaller removal sets were checked; "
            "this is authorial decision support, not an automatic edit."
        )
    assert reconcile(obsolete, conflict, backend) == obsolete
    restored = reconcile(obsolete, problem, backend)
    assert restored.status == "reopened"
    assert check_solution(problem, restored.solution) == ()


@pytest.mark.parametrize("backend", ["cp-sat", "clingo"])
def test_promotion_is_explicit_and_promoted_anchor_is_in_exact_conflict_core(backend):
    original = three_person_problem()
    problem = replace(original, anchors=(
        Anchor("soft-A", "soft", "A", start=20, tolerance=0, weight=10),
    ))
    projection = _projection(problem, backend)
    promoted = promote(projection, (20, 23))
    assert promoted
    assert all(anchor.kind == "hard" for anchor in promoted)
    assert all(anchor.source == f"promoted:{projection.problem_fingerprint}" for anchor in promoted)
    promoted_problem = replace(problem, anchors=problem.anchors + promoted)
    solved = _solve(promoted_problem, backend)
    assert solved.status in ("solved", "feasible") and solved.solution is not None
    assert check_solution(promoted_problem, solved.solution) == ()
    for anchor in promoted:
        reign = next((r for r in solved.solution.titular if r.ruler == anchor.person_id), None)
        assert reign is not None and (reign.start, reign.end) == (anchor.start, anchor.end)

    promoted_anchor = promoted[0]
    other_person = next(p.person_id for p in problem.people if p.person_id != promoted_anchor.person_id)
    conflict = replace(promoted_problem, anchors=promoted_problem.anchors + (
        Anchor("conflict-with-promotion", "hard", other_person,
               start=promoted_anchor.start, end=promoted_anchor.end,
               source="owner-test", layer="titular"),
    ))
    obsolete = reconcile(projection, conflict, backend)
    assert obsolete.status == "obsolete"
    prefix = "CP-SAT" if backend == "cp-sat" else "clingo"
    expected_core = ", ".join(sorted((promoted_anchor.anchor_id, "conflict-with-promotion")))
    assert f"{prefix} conflicting anchor subset: {expected_core}" in obsolete.explanation


def test_statuses_agree_for_current_reopened_obsolete_and_solutions_are_checked():
    base = three_person_problem()
    changed = replace(base, anchors=base.anchors + (
        Anchor("prefer-C", "soft", "C", start=24, tolerance=0, weight=3),
    ))
    impossible = replace(base, anchors=base.anchors + (
        Anchor("pin-C", "hard", "C", start=16, end=19),
    ))
    statuses = {}
    for backend in ("cp-sat", "clingo"):
        projection = _projection(base, backend)
        current = reconcile(projection, base, backend)
        reopened = reconcile(projection, changed, backend)
        obsolete = reconcile(projection, impossible, backend)
        assert current.status == "current"
        assert reopened.status == "reopened"
        assert obsolete.status == "obsolete"
        assert check_solution(base, current.solution) == ()
        assert check_solution(changed, reopened.solution) == ()
        assert reopened.objective == evaluate_objective(changed, reopened.solution)
        assert reopened.solution in optimal_solutions(changed, node_cap=100_000)
        statuses[backend] = (current.status, reopened.status, obsolete.status)
    assert statuses["cp-sat"] == statuses["clingo"] == ("current", "reopened", "obsolete")


@pytest.mark.parametrize("backend", ["cp-sat", "clingo"])
def test_infeasible_independent_of_anchors_is_reported_exactly(backend):
    prior = _projection(three_person_problem(), backend)
    impossible = Problem(
        (Person("too-young", 20, 30),),
        (Anchor("pin-too-young", "hard", "too-young", start=16, end=19),),
        replace(three_person_problem().rules, min_accession_age=16),
    )
    obsolete = reconcile(prior, impossible, backend)
    assert obsolete.status == "obsolete"
    expected = (
        "Finding: infeasible independent of anchors; the model remains infeasible with all non-soft anchors disabled."
        if backend == "cp-sat"
        else "Finding: infeasible independent of anchors; disabling all non-soft anchors remains infeasible."
    )
    assert expected in obsolete.explanation


def test_reconcile_accepts_checker_valid_feasible_incumbent_without_optimality_proof(monkeypatch):
    problem = three_person_problem()
    previous = _projection(problem, "cp-sat")
    changed = replace(problem, anchors=problem.anchors + (
        Anchor("new-soft", "soft", "C", start=24, tolerance=0, weight=2),
    ))
    incumbent = previous.solution
    result = Result(status="feasible", solution=incumbent,
                    objective=evaluate_objective(changed, incumbent), backend="mock", backend_version="test")
    import experiments.anchored_succession.reconcile as module
    monkeypatch.setattr(module, "_solve", lambda *args: result)
    reopened = reconcile(previous, changed, "cp-sat")
    assert reopened.status == "reopened"
    assert reopened.solution == incumbent
    assert check_solution(changed, reopened.solution) == ()
    assert "optimality was not proven" in reopened.explanation[0]


def test_reconcile_timeout_with_checker_valid_incumbent_reopens_as_proposal(monkeypatch):
    problem = three_person_problem()
    previous = _projection(problem, "cp-sat")
    changed = replace(problem, anchors=problem.anchors + (
        Anchor("new-soft", "soft", "C", start=24, tolerance=0, weight=2),
    ))
    incumbent = previous.solution
    result = Result(status="timeout", solution=incumbent,
                    objective=evaluate_objective(changed, incumbent), backend="mock", backend_version="test")
    import experiments.anchored_succession.reconcile as module
    monkeypatch.setattr(module, "_solve", lambda *args: result)
    reopened = reconcile(previous, changed, "cp-sat")
    assert reopened.status == "reopened"
    assert "optimality was not proven" in reopened.explanation[0]


@pytest.mark.parametrize("status", ["timeout", "unknown"])
def test_reconcile_inconclusive_without_incumbent_raises_and_preserves_previous(monkeypatch, status):
    problem = three_person_problem()
    previous = _projection(problem, "cp-sat")
    changed = replace(problem, anchors=problem.anchors + (
        Anchor("new-soft", "soft", "C", start=24, tolerance=0, weight=2),
    ))
    result = Result(status=status, explanation=(f"mock {status}",), backend="mock", backend_version="test")
    import experiments.anchored_succession.reconcile as module
    monkeypatch.setattr(module, "_solve", lambda *args: result)
    with pytest.raises(InconclusiveReconciliationError, match="inconclusive"):
        reconcile(previous, changed, "cp-sat")
    assert previous.status == "current"
    assert previous.last_checked_fingerprint == problem_fingerprint(problem)


def test_reconcile_only_obsoletes_on_proven_infeasibility(monkeypatch):
    problem = three_person_problem()
    previous = _projection(problem, "cp-sat")
    changed = replace(problem, anchors=problem.anchors + (
        Anchor("new-hard", "hard", "C", start=16, end=19),
    ))
    result = Result(status="infeasible", explanation=("proved infeasible",), backend="mock", backend_version="test")
    import experiments.anchored_succession.reconcile as module
    monkeypatch.setattr(module, "_solve", lambda *args: result)
    obsolete = reconcile(previous, changed, "cp-sat")
    assert obsolete.status == "obsolete"
    assert obsolete.solution == previous.solution
    assert obsolete.problem_fingerprint == problem_fingerprint(problem)
    assert obsolete.last_checked_fingerprint == problem_fingerprint(changed)


@pytest.mark.parametrize("backend", ["cp-sat", "clingo"])
def test_stability_weight_measurement_three_anchor_changes(backend):
    base = three_person_problem()
    previous = _projection(base, backend)
    changes = [
        Anchor("soft-C-20", "soft", "C", start=20, tolerance=0, weight=2),
        Anchor("soft-B-24", "soft", "B", start=24, tolerance=1, weight=2),
        Anchor("soft-C-26", "soft", "C", start=26, tolerance=0, weight=4),
    ]
    measurements = []
    for anchor in changes:
        changed = replace(base, anchors=base.anchors + (anchor,))
        no_stability = _solve(changed, backend)
        stable_problem = replace(changed, rules=replace(changed.rules, stability_weight=2),
                                 stability_reference=previous.solution.titular)
        with_stability = _solve(stable_problem, backend)
        assert no_stability.status in ("solved", "feasible")
        assert with_stability.status in ("solved", "feasible")
        assert no_stability.solution is not None and with_stability.solution is not None
        assert check_solution(changed, no_stability.solution) == ()
        assert check_solution(stable_problem, with_stability.solution) == ()
        before = changed_facts(previous.solution, no_stability.solution)
        after = changed_facts(previous.solution, with_stability.solution)
        measurements.append((len(before[0]) + len(before[1]), len(after[0]) + len(after[1])))
    assert len(measurements) == 3
    assert all(before >= 0 and after >= 0 for before, after in measurements)
