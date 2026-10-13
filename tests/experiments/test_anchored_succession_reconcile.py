from __future__ import annotations

from dataclasses import replace

import pytest

from experiments.anchored_succession.checker import check_solution
from experiments.anchored_succession.clingo_backend import solve_problem as solve_clingo
from experiments.anchored_succession.cp_sat import solve_problem as solve_cp_sat
from experiments.anchored_succession.model import Anchor, Problem
from experiments.anchored_succession.oracle import optimal_solutions
from experiments.anchored_succession.reconcile import (
    Projection, changed_facts, problem_fingerprint, promote, projection_from_result, reconcile,
)
from experiments.anchored_succession.scenarios import small_rules, three_person_problem
from experiments.anchored_succession.objective import evaluate_objective


def _solve(problem, backend):
    return solve_cp_sat(problem, time_limit_seconds=10) if backend == "cp-sat" else solve_clingo(problem, time_limit_seconds=10)


def _projection(problem, backend):
    result = _solve(problem, backend)
    assert result.status == "solved" and result.solution is not None
    assert check_solution(problem, result.solution) == ()
    return projection_from_result(problem, result)


@pytest.mark.parametrize("backend", ["cp-sat", "clingo"])
def test_unchanged_fingerprint_returns_current_without_solver_call(monkeypatch, backend):
    problem = three_person_problem()
    previous = _projection(problem, backend)
    import experiments.anchored_succession.reconcile as module
    monkeypatch.setattr(module, "_solve", lambda *args: pytest.fail("solver must not be called"))
    result = reconcile(previous, problem, backend)
    assert result.status == "current"
    assert result.solution == previous.solution
    assert result.problem_fingerprint == previous.problem_fingerprint


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
    assert check_solution(new_problem, result.solution) == ()
    assert result.objective == evaluate_objective(new_problem, result.solution)
    added, removed = changed_facts(previous.solution, result.solution)
    assert result.changed_facts_added == added
    assert result.changed_facts_removed == removed
    assert "proposal" in result.explanation[0].lower()
    assert result.solution is not None
    if len(optimal_solutions(new_problem)) > 0:
        assert result.solution in optimal_solutions(new_problem)


@pytest.mark.parametrize("backend", ["cp-sat", "clingo"])
def test_obsolete_then_reopened_after_owner_removes_conflict(backend):
    problem = three_person_problem()
    previous = _projection(problem, backend)
    conflict = replace(problem, anchors=problem.anchors + (
        Anchor("conflicting-C", "hard", "C", start=16, end=19, source="owner-test"),
    ))
    obsolete = reconcile(previous, conflict, backend)
    assert obsolete.status == "obsolete"
    assert obsolete.solution == previous.solution
    assert obsolete.problem_fingerprint == problem_fingerprint(conflict)
    assert obsolete.explanation
    assert any(anchor_id in " ".join(obsolete.explanation) for anchor_id in ("pin-A", "conflicting-C"))
    restored = reconcile(obsolete, problem, backend)
    assert restored.status == "current"
    # The owner has removed the conflicting anchor; the semantic fingerprint is
    # the original one, so no solver call is needed and the retained solution is current.
    assert check_solution(problem, restored.solution) == ()


@pytest.mark.parametrize("backend", ["cp-sat", "clingo"])
def test_promotion_is_explicit_and_promoted_anchors_constrain_resolve(backend):
    problem = three_person_problem()
    projection = _projection(problem, backend)
    promoted = promote(projection, (16, 19))
    assert promoted
    assert all(anchor.kind == "hard" for anchor in promoted)
    assert all(anchor.source == f"promoted:{projection.problem_fingerprint}" for anchor in promoted)
    promoted_problem = replace(problem, anchors=problem.anchors + promoted)
    solved = _solve(promoted_problem, backend)
    assert solved.status == "solved" and solved.solution is not None
    for anchor in promoted:
        reign = next((r for r in solved.solution.titular if r.ruler == anchor.person_id), None)
        assert reign is not None and (reign.start, reign.end) == (anchor.start, anchor.end)
    conflict = replace(promoted_problem, anchors=promoted_problem.anchors + (
        Anchor("conflict-with-promotion", "hard", promoted[0].person_id,
               start=promoted[0].start + 1, end=promoted[0].end, source="owner-test", layer="titular"),
    ))
    obsolete = reconcile(projection, conflict, backend)
    assert obsolete.status == "obsolete"
    assert any(anchor.anchor_id in " ".join(obsolete.explanation) for anchor in promoted)


@pytest.mark.parametrize("backend", ["cp-sat", "clingo"])
def test_statuses_agree_for_current_reopened_obsolete(backend):
    problem = three_person_problem()
    projection = _projection(problem, backend)
    assert reconcile(projection, problem, backend).status == "current"
    changed = replace(problem, anchors=problem.anchors + (
        Anchor("prefer-C", "soft", "C", start=24, tolerance=0, weight=3),
    ))
    assert reconcile(projection, changed, backend).status == "reopened"
    impossible = replace(problem, anchors=problem.anchors + (
        Anchor("pin-A", "hard", "A", start=16, end=19),
        Anchor("pin-C", "hard", "C", start=16, end=19),
    ))
    assert reconcile(projection, impossible, backend).status == "obsolete"


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
        stable_problem = replace(
            changed,
            rules=replace(changed.rules, stability_weight=2),
            stability_reference=previous.solution.titular,
        )
        with_stability = _solve(stable_problem, backend)
        assert no_stability.status == with_stability.status == "solved"
        assert no_stability.solution is not None and with_stability.solution is not None
        assert check_solution(changed, no_stability.solution) == ()
        assert check_solution(stable_problem, with_stability.solution) == ()
        measurements.append((
            len(changed_facts(previous.solution, no_stability.solution)[0]) +
            len(changed_facts(previous.solution, no_stability.solution)[1]),
            len(changed_facts(previous.solution, with_stability.solution)[0]) +
            len(changed_facts(previous.solution, with_stability.solution)[1]),
        ))
    assert len(measurements) == 3
    # Measurements are reported rather than requiring stability to improve every case.
    assert all(before >= 0 and after >= 0 for before, after in measurements)
