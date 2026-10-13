"""Tiny-instance brute-force oracle, for test use only (six people maximum)."""
from __future__ import annotations
from .checker import check_solution
from .model import Problem, Reign, Result, Solution

def enumerate_solutions(problem: Problem, limit: int = 6) -> tuple[Solution, ...]:
    """Enumerate tiny candidate chains as a test oracle, never as a production solver."""
    if len(problem.people) > limit:
        raise ValueError(f"brute-force oracle limited to {limit} people")
    people = {p.person_id: p for p in problem.people}
    rules = problem.rules
    candidates = []
    for person in problem.people:
        earliest = max(rules.horizon_start, person.birth + rules.min_accession_age)
        latest = min(rules.horizon_end, person.death)
        for start in range(earliest, latest - rules.min_reign + 2):
            for duration in range(rules.min_reign, min(rules.max_reign, latest - start + 1) + 1):
                candidates.append(Reign(person.person_id, start, start + duration - 1))
    found = {}
    def extend(chain: tuple[Reign, ...]) -> None:
        if chain:
            solution = Solution(chain, chain)
            if not check_solution(problem, solution):
                found[chain] = solution
        if chain and chain[-1].end >= rules.horizon_end:
            return
        for candidate in candidates:
            if chain and candidate.start != chain[-1].end + 1:
                continue
            if chain and candidate.ruler == chain[-1].ruler:
                continue
            if chain:
                prev = people[chain[-1].ruler]
                current = people[candidate.ruler]
                if not (chain[-1].ruler in current.parents or set(current.parents) & set(prev.parents)):
                    continue
            if not chain and candidate.start != rules.horizon_start:
                continue
            extend(chain + (candidate,))
    extend(())
    return tuple(found.values())

def oracle_result(problem: Problem) -> Result:
    solutions = enumerate_solutions(problem)
    if not solutions:
        return Result("infeasible", backend="brute-force-oracle", explanation=("no enumerated feasible solution",))
    return Result("solved", solutions[0], objective=0, backend="brute-force-oracle")
