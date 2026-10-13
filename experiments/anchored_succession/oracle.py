"""Tiny brute-force oracle for tests only; maximum six people.

A solution is any valid chain satisfying all hard rules and anchors, including
chains that do not span the horizon. When hard or record anchors exist, each
layer must be occupied continuously from the earliest through latest anchored
year; no coverage is required otherwise. This prevents the objective favouring
fewer rulers by leaving years unoccupied.
"""
from __future__ import annotations
from dataclasses import replace
from .checker import check_solution
from .model import Anchor, Problem, Reign, Result, Solution
from .objective import evaluate_objective

class OracleNodeLimitError(RuntimeError):
    """Raised when exhaustive enumeration reaches its explicit safety cap."""

def _solution_key(solution: Solution) -> tuple:
    return (
        tuple((r.ruler, r.start, r.end) for r in solution.titular),
        tuple((r.ruler, r.start, r.end) for r in solution.effective),
    )

def _anchor_span(anchor: Anchor) -> tuple[int, int] | None:
    if anchor.start is not None and anchor.end is not None:
        return anchor.start, anchor.end
    return None

def _ruler_at(chain: tuple[Reign, ...], year: int) -> str | None:
    return next((r.ruler for r in chain if r.start <= year <= r.end), None)

def _layer_chain_compatible(problem: Problem, chain: tuple[Reign, ...], layer: str) -> bool:
    anchored_spans = [
        span for anchor in problem.anchors if anchor.kind in ("hard", "record")
        for span in (_anchor_span(anchor),) if span is not None
    ]
    if anchored_spans:
        first = min(span[0] for span in anchored_spans)
        last = max(span[1] for span in anchored_spans)
        if any(_ruler_at(chain, year) is None for year in range(first, last + 1)):
            return False
    for anchor in problem.anchors:
        if anchor.kind not in ("hard", "record"):
            continue
        if anchor.layer != "both" and anchor.layer != layer:
            continue
        span = _anchor_span(anchor)
        reign = next((r for r in chain if r.ruler == anchor.person_id), None)
        if span is not None and (reign is None or reign.start > span[0] or reign.end < span[1]):
            return False
        if anchor.lower is not None and anchor.upper is not None:
            if reign is None or not anchor.lower <= reign.start <= anchor.upper:
                return False
    for anchor in problem.anchors:
        if anchor.kind != "reveal" or anchor.start is None or anchor.end is None:
            continue
        if layer == "effective":
            if any(_ruler_at(chain, year) != anchor.person_id for year in range(anchor.start, anchor.end + 1)):
                return False
        else:
            # The effective layer names the reveal ruler; the titular layer
            # must differ during the reveal interval.
            if any(_ruler_at(chain, year) == anchor.person_id for year in range(anchor.start, anchor.end + 1)):
                return False
    return True

def _has_unmarked_record_reveal_conflict(problem: Problem) -> bool:
    for record in problem.anchors:
        if record.kind != "record" or record.marked_reveal:
            continue
        record_span = _anchor_span(record)
        if record_span is None:
            continue
        for reveal in problem.anchors:
            if reveal.kind != "reveal" or reveal.start is None or reveal.end is None:
                continue
            overlap_start = max(record_span[0], reveal.start)
            overlap_end = min(record_span[1], reveal.end)
            if overlap_start <= overlap_end and record.person_id != reveal.person_id:
                return True
    return False

def enumerate_solutions(problem: Problem, limit: int = 6, node_cap: int = 100_000) -> tuple[Solution, ...]:
    """Enumerate valid chains, including chains that do not span the horizon."""
    if len(problem.people) > limit:
        raise ValueError(f"brute-force oracle limited to {limit} people")
    if node_cap < 1:
        raise ValueError("node_cap must be positive")
    if _has_unmarked_record_reveal_conflict(problem):
        return ()
    people = {p.person_id: p for p in problem.people}
    rules = problem.rules
    candidates = []
    for person in problem.people:
        earliest = max(rules.horizon_start, person.birth + rules.min_accession_age)
        latest = min(rules.horizon_end, person.death)
        for start in range(earliest, latest - rules.min_reign + 2):
            for duration in range(rules.min_reign, min(rules.max_reign, latest - start + 1) + 1):
                candidates.append(Reign(person.person_id, start, start + duration - 1))
    by_start: dict[int, list[Reign]] = {}
    for candidate in candidates:
        by_start.setdefault(candidate.start, []).append(candidate)
    chains: list[tuple[Reign, ...]] = []
    explored = 0
    base_problem = replace(problem, anchors=())

    def tick() -> None:
        nonlocal explored
        explored += 1
        if explored > node_cap:
            raise OracleNodeLimitError(
                f"brute-force oracle node cap exceeded ({node_cap} nodes; {len(candidates)} candidate reigns)"
            )

    def extend(chain: tuple[Reign, ...]) -> None:
        tick()
        if chain and not check_solution(base_problem, Solution(chain, chain)):
            chains.append(chain)
        if chain and chain[-1].end >= rules.horizon_end:
            return
        options = candidates if not chain else by_start.get(chain[-1].end + 1, ())
        used = {r.ruler for r in chain}
        for candidate in options:
            if candidate.ruler in used:
                continue
            if chain:
                previous, current = people[chain[-1].ruler], people[candidate.ruler]
                if not (chain[-1].ruler in current.parents or set(current.parents) & set(previous.parents)):
                    continue
            extend(chain + (candidate,))
    extend(())

    titular_chains = [c for c in chains if _layer_chain_compatible(problem, c, "titular")]
    effective_chains = [c for c in chains if _layer_chain_compatible(problem, c, "effective")]
    solutions: dict[tuple, Solution] = {}
    has_reveal = any(anchor.kind == "reveal" for anchor in problem.anchors)
    if has_reveal:
        for titular in titular_chains:
            for effective in effective_chains:
                tick()
                solution = Solution(titular, effective)
                if not check_solution(problem, solution):
                    solutions[_solution_key(solution)] = solution
    else:
        for chain in titular_chains:
            if chain not in effective_chains:
                continue
            solution = Solution(chain, chain)
            if not check_solution(problem, solution):
                solutions[_solution_key(solution)] = solution
    return tuple(sorted(solutions.values(), key=_solution_key))

def optimal_solutions(problem: Problem, limit: int = 6, node_cap: int = 100_000) -> tuple[Solution, ...]:
    """Return all minimum-objective feasible solutions in deterministic tie order."""
    feasible = enumerate_solutions(problem, limit=limit, node_cap=node_cap)
    if not feasible:
        return ()
    best = min(evaluate_objective(problem, s) for s in feasible)
    return tuple(s for s in feasible if evaluate_objective(problem, s) == best)

def oracle_result(problem: Problem, limit: int = 6, node_cap: int = 100_000) -> Result:
    solutions = optimal_solutions(problem, limit=limit, node_cap=node_cap)
    if not solutions:
        return Result("infeasible", backend="brute-force-oracle", explanation=("no enumerated feasible solution",))
    return Result("solved", solutions[0], objective=evaluate_objective(problem, solutions[0]), backend="brute-force-oracle")
