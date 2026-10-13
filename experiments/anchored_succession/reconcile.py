"""Projection reconciliation lifecycle for the anchored-succession experiment.

Reconciliation proposes solutions only. It never edits anchors or promotes a
projection implicitly; authorial promotion is an explicit separate operation.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from worldloom.core.hashing import fingerprint

from .model import Anchor, Problem, Result, Solution, canonical_problem_data


ProjectionStatus = Literal["current", "reopened", "obsolete"]


@dataclass(frozen=True)
class Projection:
    problem_fingerprint: str
    solution: Solution
    backend: str
    backend_version: str
    objective: int
    status: ProjectionStatus = "current"
    explanation: tuple[str, ...] = ()
    changed_facts_added: tuple[tuple[str, str, int, int], ...] = ()
    changed_facts_removed: tuple[tuple[str, str, int, int], ...] = ()


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
    """Return current without solving, reopen as a proposal, or retain as obsolete."""
    new_fingerprint = problem_fingerprint(new_problem)
    if new_fingerprint == previous.problem_fingerprint:
        return replace(
            previous,
            status="current",
            explanation=(),
            changed_facts_added=(),
            changed_facts_removed=(),
        )

    result = _solve(new_problem, backend)
    if result.status == "solved" and result.solution is not None and result.objective is not None:
        added, removed = changed_facts(previous.solution, result.solution)
        return Projection(
            problem_fingerprint=new_fingerprint,
            solution=result.solution,
            backend=result.backend,
            backend_version=result.backend_version,
            objective=result.objective,
            status="reopened",
            explanation=("Reopened solution is a proposal; anchors were not modified.",),
            changed_facts_added=added,
            changed_facts_removed=removed,
        )

    explanation = (
        *result.explanation,
        "Exploratory smallest anchor-removal sets are suggestions for authorial review, not automatic edits.",
    )
    return replace(
        previous,
        problem_fingerprint=new_fingerprint,
        status="obsolete",
        explanation=tuple(explanation),
        changed_facts_added=(),
        changed_facts_removed=(),
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
    """Create an initial current projection from a feasible solver result."""
    if result.status != "solved" or result.solution is None or result.objective is None:
        raise ValueError("a current projection requires a solved result with a solution and objective")
    return Projection(
        problem_fingerprint=problem_fingerprint(problem),
        solution=result.solution,
        backend=result.backend,
        backend_version=result.backend_version,
        objective=result.objective,
    )
