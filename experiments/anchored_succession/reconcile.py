"""Projection reconciliation lifecycle for the anchored-succession experiment.

Reconciliation proposes solutions only. It never edits anchors or promotes a
projection implicitly; authorial promotion is an explicit separate operation.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from worldloom.core.hashing import fingerprint

from .checker import check_solution
from .model import Anchor, Problem, Result, Solution, canonical_problem_data
from .objective import evaluate_objective

ProjectionStatus = Literal["current", "reopened", "obsolete"]


class InconclusiveReconciliationError(RuntimeError):
    """The solver did not establish a safe reconciliation outcome."""


@dataclass(frozen=True)
class Projection:
    # Fingerprint of the problem that produced this retained solution.
    problem_fingerprint: str
    solution: Solution
    backend: str
    backend_version: str
    objective: int
    status: ProjectionStatus = "current"
    explanation: tuple[str, ...] = ()
    changed_facts_added: tuple[tuple[str, str, int, int], ...] = ()
    changed_facts_removed: tuple[tuple[str, str, int, int], ...] = ()
    # Fingerprint most recently checked, which may differ while status=obsolete.
    last_checked_fingerprint: str | None = None


def problem_fingerprint(problem: Problem) -> str:
    """Fingerprint semantic problem data, excluding seed and stability reference."""
    return fingerprint(canonical_problem_data(problem))


def _facts(solution: Solution) -> set[tuple[str, str, int, int]]:
    return {
        (layer, reign.ruler, reign.start, reign.end)
        for layer, reigns in (("titular", solution.titular), ("effective", solution.effective))
        for reign in reigns
    }


def changed_facts(previous: Solution, current: Solution) -> tuple[
    tuple[tuple[str, str, int, int], ...],
    tuple[tuple[str, str, int, int], ...],
]:
    """Independently diff layer/ruler/start/end facts, without solver logic."""
    old, new = _facts(previous), _facts(current)
    return tuple(sorted(new - old)), tuple(sorted(old - new))


def reconcile(previous: Projection, new_problem: Problem, backend: str = "cp-sat") -> Projection:
    """Return unchanged, reopened proposal, or retained obsolete projection."""
    new_fingerprint = problem_fingerprint(new_problem)
    last_checked = previous.last_checked_fingerprint or previous.problem_fingerprint
    if new_fingerprint == last_checked:
        # Preserve every field, including status and explanation, and do not solve.
        return previous

    result = _solve(new_problem, backend)
    if result.status == "infeasible":
        explanation = (
            *result.explanation,
            "Exploratory smallest anchor-removal sets are suggestions for authorial review, not automatic edits.",
        )
        return replace(
            previous,
            status="obsolete",
            last_checked_fingerprint=new_fingerprint,
            explanation=tuple(explanation),
            changed_facts_added=(),
            changed_facts_removed=(),
        )

    # A checker-valid incumbent is useful even if the backend did not prove optimality.
    has_incumbent = result.solution is not None
    if result.status == "unknown":
        raise InconclusiveReconciliationError(
            "reconciliation is inconclusive: backend returned unknown; previous projection was retained unchanged"
        )
    if result.status == "timeout" and not has_incumbent:
        raise InconclusiveReconciliationError(
            "reconciliation is inconclusive: time limit reached without a feasible incumbent; previous projection was retained unchanged"
        )
    if result.status not in ("solved", "feasible", "timeout") or not has_incumbent:
        raise InconclusiveReconciliationError(
            f"reconciliation is inconclusive: backend status={result.status!r} did not provide a checker-valid incumbent"
        )

    errors = check_solution(new_problem, result.solution)
    if errors:
        raise InconclusiveReconciliationError(
            "reconciliation is inconclusive: independent checker rejected incumbent: " + "; ".join(errors)
        )
    objective = evaluate_objective(new_problem, result.solution)
    if result.objective is not None and result.objective != objective:
        raise InconclusiveReconciliationError(
            f"reconciliation is inconclusive: reported objective {result.objective} != independently evaluated {objective}"
        )

    added, removed = changed_facts(previous.solution, result.solution)
    if result.status == "solved":
        explanation = ("Reopened solution is a proposal; anchors were not modified.",)
    else:
        explanation = (
            "A feasible incumbent was accepted as a proposal; optimality was not proven.",
            "Reopened solution is a proposal; anchors were not modified.",
        )
    return Projection(
        problem_fingerprint=new_fingerprint,
        last_checked_fingerprint=new_fingerprint,
        solution=result.solution,
        backend=result.backend,
        backend_version=result.backend_version,
        objective=objective,
        status="reopened",
        explanation=explanation,
        changed_facts_added=added,
        changed_facts_removed=removed,
    )


def _solve(problem: Problem, backend: str) -> Result:
    if backend in ("cp-sat", "ortools", "CP-SAT"):
        from .cp_sat import solve_problem
    elif backend in ("clingo", "ASP"):
        from .clingo_backend import solve_problem
    else:
        raise ValueError(f"unknown anchored-succession backend: {backend}")
    return solve_problem(problem, time_limit_seconds=10.0)


def promote(projection: Projection, years: tuple[int, int]) -> tuple[Anchor, ...]:
    """Explicitly promote titular reign intervals intersecting the inclusive year span."""
    start, end = years
    if start > end:
        raise ValueError("promotion year span start must not exceed end")
    source = f"promoted:{projection.problem_fingerprint}"
    promoted: list[Anchor] = []
    for index, reign in enumerate(projection.solution.titular):
        if reign.end < start or reign.start > end:
            continue
        promoted.append(
            Anchor(
                anchor_id=f"promoted-{index}-{reign.ruler}-{reign.start}",
                kind="hard",
                person_id=reign.ruler,
                start=reign.start,
                end=reign.end,
                source=source,
                layer="titular",
            )
        )
    return tuple(promoted)


def projection_from_result(problem: Problem, result: Result) -> Projection:
    """Create an initial current projection from a checker-valid solver result."""
    if result.status not in ("solved", "feasible") or result.solution is None:
        raise ValueError("a current projection requires a feasible result with a solution")
    errors = check_solution(problem, result.solution)
    if errors:
        raise ValueError("a current projection requires a checker-valid solution: " + "; ".join(errors))
    objective = evaluate_objective(problem, result.solution)
    if result.objective is not None and result.objective != objective:
        raise ValueError("solver objective disagrees with independent objective evaluator")
    current_fingerprint = problem_fingerprint(problem)
    return Projection(
        problem_fingerprint=current_fingerprint,
        last_checked_fingerprint=current_fingerprint,
        solution=result.solution,
        backend=result.backend,
        backend_version=result.backend_version,
        objective=objective,
    )
