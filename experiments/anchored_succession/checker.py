"""Independent hard-rule checker; deliberately does not import solver code."""
from __future__ import annotations
from .model import Problem, Solution
def _ruler_at(reigns, year: int) -> str | None:
    return next((r.ruler for r in reigns if r.start <= year <= r.end), None)
def check_solution(problem: Problem, solution: Solution) -> tuple[str, ...]:
    errors: list[str] = []
    people = {p.person_id: p for p in problem.people}
    rules = problem.rules
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
                previous_person = people.get(previous.ruler)
                if previous_person is not None and reign.ruler != previous.ruler:
                    child = previous.ruler in person.parents
                    sibling = bool(set(person.parents) & set(previous_person.parents))
                    if not (child or sibling):
                        errors.append(f"{layer_name}: invalid succession {previous.ruler}->{reign.ruler}")
    for anchor in problem.anchors:
        if anchor.kind != "hard" and not (anchor.kind == "record" and not anchor.marked_reveal):
            continue
        reign = next((r for r in solution.titular if r.ruler == anchor.person_id), None)
        if anchor.start is not None and anchor.end is not None:
            if reign is None or reign.start > anchor.start or reign.end < anchor.end:
                errors.append(f"anchor violated: {anchor.anchor_id} (interval)")
        if anchor.lower is not None and anchor.upper is not None:
            if reign is None or not anchor.lower <= reign.start <= anchor.upper:
                errors.append(f"anchor violated: {anchor.anchor_id} (bounds)")
    reveal_years: set[int] = set()
    for anchor in problem.anchors:
        if anchor.kind != "reveal":
            continue
        if anchor.start is None or anchor.end is None:
            errors.append(f"reveal missing interval: {anchor.anchor_id}")
            continue
        for year in range(anchor.start, anchor.end + 1):
            reveal_years.add(year)
            effective = _ruler_at(solution.effective, year)
            titular = _ruler_at(solution.titular, year)
            if effective != anchor.person_id:
                errors.append(f"reveal wrong effective ruler at {year}: {anchor.anchor_id}")
                break
            if effective == titular:
                errors.append(f"reveal not expressed at {year}: {anchor.anchor_id}")
                break
    for year in range(rules.horizon_start, rules.horizon_end + 1):
        if year not in reveal_years and _ruler_at(solution.titular, year) != _ruler_at(solution.effective, year):
            errors.append(f"titular/effective diverge outside reveal at {year}")
            break
    for record in problem.anchors:
        if record.kind != "record" or record.marked_reveal:
            continue
        start = record.start if record.start is not None else record.lower
        end = record.end if record.end is not None else record.upper
        if start is None or end is None:
            continue
        for reveal in problem.anchors:
            if reveal.kind != "reveal" or reveal.start is None or reveal.end is None:
                continue
            overlap_start, overlap_end = max(start, reveal.start), min(end, reveal.end)
            if overlap_start > overlap_end or record.person_id == reveal.person_id:
                continue
            if any(_ruler_at(solution.effective, year) == reveal.person_id for year in range(overlap_start, overlap_end + 1)):
                errors.append(f"record contradicted by unmarked reveal: {record.anchor_id}->{reveal.anchor_id}")
                break
    return tuple(errors)
