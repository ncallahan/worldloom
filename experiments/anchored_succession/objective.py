"""Independent objective evaluator; see experiment page for counted layers."""
from __future__ import annotations
from .model import Problem, Reign, Solution

def _ruler_at(reigns: tuple[Reign, ...], year: int) -> str | None:
    for reign in reigns:
        if reign.start <= year <= reign.end:
            return reign.ruler
    return None

def _layers(solution: Solution, layer: str) -> tuple[tuple[str, tuple[Reign, ...]], ...]:
    if layer == "both":
        return (("titular", solution.titular), ("effective", solution.effective))
    return ((layer, solution.titular if layer == "titular" else solution.effective),)

def evaluate_objective(problem: Problem, solution: Solution) -> int:
    """Compute all costs deterministically.

    Duration deviation and sibling-transition costs are counted on BOTH
    titular and effective layers. Soft-anchor penalties use that anchor's
    layer(s). Stability mismatch is counted on the titular layer only.
    A missing soft-anchored ruler costs the inclusive horizon length per
    targeted layer, multiplied by the anchor weight.
    """
    people = {p.person_id: p for p in problem.people}
    rules = problem.rules
    cost = 0
    horizon_length = rules.horizon_end - rules.horizon_start + 1
    for anchor in problem.anchors:
        if anchor.kind != "soft":
            continue
        for _, reigns in _layers(solution, anchor.layer):
            reign = next((r for r in reigns if r.ruler == anchor.person_id), None)
            if reign is None:
                cost += anchor.weight * horizon_length
            else:
                cost += anchor.weight * max(0, abs(reign.start - anchor.start) - anchor.tolerance)
    for layer in (solution.titular, solution.effective):
        cost += sum(abs((r.end - r.start + 1) - rules.preferred_reign) for r in layer)
        for previous, current in zip(layer, layer[1:]):
            previous_person = people.get(previous.ruler)
            current_person = people.get(current.ruler)
            if previous_person is None or current_person is None:
                continue
            is_child = previous.ruler in current_person.parents
            is_sibling = bool(set(previous_person.parents) & set(current_person.parents))
            if is_sibling and not is_child:
                cost += rules.child_preference_weight
    if rules.stability_weight and problem.stability_reference:
        for year in range(rules.horizon_start, rules.horizon_end + 1):
            if _ruler_at(solution.titular, year) != _ruler_at(problem.stability_reference, year):
                cost += rules.stability_weight
    return cost
