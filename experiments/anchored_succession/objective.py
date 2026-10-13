"""Independent objective evaluator for the succession experiment."""
from __future__ import annotations
from .model import Problem, Reign, Solution
def _ruler_at(reigns: tuple[Reign, ...], year: int) -> str | None:
    for reign in reigns:
        if reign.start <= year <= reign.end:
            return reign.ruler
    return None
def evaluate_objective(problem: Problem, solution: Solution) -> int:
    """Compute soft-anchor, duration, sibling-preference, and stability costs."""
    people = {p.person_id: p for p in problem.people}
    rules = problem.rules
    cost = 0
    for anchor in problem.anchors:
        if anchor.kind != "soft":
            continue
        reign = next((r for r in solution.titular if r.ruler == anchor.person_id), None)
        distance = (rules.horizon_end - rules.horizon_start + 1 if reign is None
                    else abs(reign.start - anchor.start) if anchor.start is not None else 0)
        cost += anchor.weight * max(0, distance - anchor.tolerance)
    for layer in (solution.titular, solution.effective):
        cost += sum(abs((r.end - r.start + 1) - rules.preferred_reign) for r in layer)
        for previous, current in zip(layer, layer[1:]):
            previous_person = people.get(previous.ruler)
            current_person = people.get(current.ruler)
            if previous_person is not None and current_person is not None and previous.ruler not in current_person.parents:
                cost += rules.child_preference_weight
    if rules.stability_weight and problem.stability_reference:
        for year in range(rules.horizon_start, rules.horizon_end + 1):
            if _ruler_at(solution.titular, year) != _ruler_at(problem.stability_reference, year):
                cost += rules.stability_weight
    return cost
