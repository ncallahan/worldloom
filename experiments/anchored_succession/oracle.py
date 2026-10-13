"""Tiny brute-force oracle for tests only; maximum six people."""
from __future__ import annotations
from .checker import check_solution
from .model import Problem, Reign, Result, Solution
from .objective import evaluate_objective
class OracleNodeLimitError(RuntimeError):
    """Raised when exhaustive enumeration reaches its explicit safety cap."""
def _solution_key(solution: Solution) -> tuple:
    return (tuple((r.ruler, r.start, r.end) for r in solution.titular),
            tuple((r.ruler, r.start, r.end) for r in solution.effective))
def enumerate_solutions(problem: Problem, limit: int = 6, node_cap: int = 100_000) -> tuple[Solution, ...]:
    """Enumerate valid chains, including chains that do not span the horizon.

    A solution is any valid chain satisfying all hard rules and anchors. The
    oracle is test-only, limited to six people, and raises rather than hangs
    when its explicit node cap is exceeded.
    """
    if len(problem.people) > limit:
        raise ValueError(f"brute-force oracle limited to {limit} people")
    if node_cap < 1:
        raise ValueError("node_cap must be positive")
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
    found: dict[tuple[Reign, ...], Solution] = {}
    explored = 0
    def extend(chain: tuple[Reign, ...]) -> None:
        nonlocal explored
        explored += 1
        if explored > node_cap:
            raise OracleNodeLimitError(f"brute-force oracle node cap exceeded ({node_cap} nodes; {len(candidates)} candidate reigns)")
        if chain:
            solution = Solution(chain, chain)
            if not check_solution(problem, solution):
                found[chain] = solution
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
    return tuple(sorted(found.values(), key=_solution_key))
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
