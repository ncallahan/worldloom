"""Independent hard-rule checker.

A throne must be occupied on each layer for every year between the earliest
and latest year covered by a hard or record anchor. With no such anchors,
this occupancy-span rule imposes no coverage requirement. This prevents the
objective from winning trivially by choosing fewer rulers and leaving years
uncovered.
"""
from __future__ import annotations
from .model import Problem, Solution

def _ruler_at(reigns, year: int) -> str | None:
    return next((r.ruler for r in reigns if r.start <= year <= r.end), None)

def _anchor_span(anchor) -> tuple[int, int] | None:
    if anchor.start is not None and anchor.end is not None:
        return (anchor.start, anchor.end)
    if anchor.lower is not None and anchor.upper is not None:
        return (anchor.lower, anchor.upper)
    return None

def _target_layers(layer: str) -> tuple[str, ...]:
    return ("titular", "effective") if layer == "both" else (layer,)

def check_solution(problem: Problem, solution: Solution) -> tuple[str, ...]:
    errors: list[str] = []
    people = {p.person_id: p for p in problem.people}
    rules = problem.rules
    layer_sequences = (("titular", solution.titular), ("effective", solution.effective))
    for layer_name, reigns in layer_sequences:
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

    anchored_spans = [
        span for anchor in problem.anchors
        if anchor.kind in ("hard", "record")
        for span in (_anchor_span(anchor),) if span is not None
    ]
    if anchored_spans:
        first_year = min(span[0] for span in anchored_spans)
        last_year = max(span[1] for span in anchored_spans)
        for layer_name, reigns in layer_sequences:
            for year in range(first_year, last_year + 1):
                if _ruler_at(reigns, year) is None:
                    errors.append(f"{layer_name}: throne unoccupied at year {year} within anchored span")
                    break

    for anchor in problem.anchors:
        if anchor.kind not in ("hard", "record"):
            continue
        span = _anchor_span(anchor)
        for layer_name in _target_layers(anchor.layer):
            reigns = solution.titular if layer_name == "titular" else solution.effective
            reign = next((r for r in reigns if r.ruler == anchor.person_id), None)
            if span is not None:
                if reign is None or reign.start > span[0] or reign.end < span[1]:
                    errors.append(f"anchor violated: {anchor.anchor_id} (interval, {layer_name})")
            if anchor.lower is not None and anchor.upper is not None:
                if reign is None or not anchor.lower <= reign.start <= anchor.upper:
                    errors.append(f"anchor violated: {anchor.anchor_id} (bounds, {layer_name})")

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
        record_span = _anchor_span(record)
        if record_span is None:
            continue
        for reveal in problem.anchors:
            if reveal.kind != "reveal" or reveal.start is None or reveal.end is None:
                continue
            overlap_start = max(record_span[0], reveal.start)
            overlap_end = min(record_span[1], reveal.end)
            if overlap_start <= overlap_end and record.person_id != reveal.person_id:
                errors.append(f"record contradicted by unmarked reveal: {record.anchor_id}->{reveal.anchor_id}")
                break
    return tuple(errors)
