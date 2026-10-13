"""Independent hard-rule checker; deliberately does not import solver code."""
from __future__ import annotations
from .model import Problem, Solution

def _ruler_at(reigns, year: int) -> str | None:
    return next((reign.ruler for reign in reigns if reign.start <= year <= reign.end), None)

def check_solution(problem: Problem, solution: Solution) -> tuple[str, ...]:
    errors: list[str] = []
    people = {person.person_id: person for person in problem.people}
    rules = problem.rules
    if not solution.titular:
        errors.append("empty titular reign sequence")
        return tuple(errors)
    for layer_name, reigns in (("titular", solution.titular), ("effective", solution.effective)):
        if not reigns:
            errors.append(f"empty {layer_name} reign sequence")
            continue
        seen: set[str] = set()
        for index, reign in enumerate(reigns):
            person = people.get(reign.ruler)
            if person is None:
                errors.append(f"unknown ruler {reign.ruler}")
                continue
            if reign.ruler in seen:
                errors.append(f"{layer_name}: ruler repeats: {reign.ruler}")
            seen.add(reign.ruler)
            length = reign.end - reign.start + 1
            if not rules.min_reign <= length <= rules.max_reign:
                errors.append(f"{layer_name}: invalid reign length: {reign.ruler}")
            if reign.start < rules.horizon_start or reign.end > rules.horizon_end:
                errors.append(f"{layer_name}: reign outside horizon: {reign.ruler}")
            if reign.start - person.birth < rules.min_accession_age:
                errors.append(f"{layer_name}: accession too young: {reign.ruler}")
            if person.death < reign.end:
                errors.append(f"{layer_name}: ruler dies before reign ends: {reign.ruler}")
            if index:
                previous = reigns[index - 1]
                if reign.start != previous.end + 1:
                    errors.append(f"{layer_name}: reign chain not contiguous")
                prev_person = people.get(previous.ruler)
                if prev_person and reign.ruler != previous.ruler:
                    is_child = previous.ruler in person.parents
                    is_sibling = bool(set(person.parents) & set(prev_person.parents))
                    if not (is_child or is_sibling):
                        errors.append(f"{layer_name}: invalid succession {previous.ruler}->{reign.ruler}")
    for anchor in problem.anchors:
        if anchor.kind != "hard" and not (anchor.kind == "record" and not anchor.marked_reveal):
            continue
        reign = next((r for r in solution.titular if r.ruler == anchor.person_id), None)
        if anchor.start is not None and anchor.end is not None and (reign is None or reign.start > anchor.start or reign.end < anchor.end):
            errors.append(f"anchor violated: {anchor.anchor_id}")
        if anchor.lower is not None and anchor.upper is not None and (reign is None or not anchor.lower <= reign.start <= anchor.upper):
            errors.append(f"anchor violated: {anchor.anchor_id}")
    for anchor in problem.anchors:
        if anchor.kind == "reveal":
            for year in range(anchor.start or 0, (anchor.end or -1) + 1):
                if _ruler_at(solution.titular, year) == _ruler_at(solution.effective, year):
                    errors.append(f"reveal not expressed at {year}: {anchor.anchor_id}")
                    break
    return tuple(errors)
