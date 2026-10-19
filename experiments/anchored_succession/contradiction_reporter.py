"""Solver-free, conservative contradiction checks for anchored succession."""
from __future__ import annotations

from dataclasses import dataclass

from .model import Anchor, Problem, Rules


@dataclass(frozen=True)
class Contradiction:
    """One established contradiction, with a stable code and human explanation."""

    code: str
    anchor_ids: tuple[str, ...]
    explanation: str


def _target_layers(anchor: Anchor) -> tuple[str, ...]:
    if anchor.layer == "both":
        return ("effective", "titular")
    return (anchor.layer or "titular",)


def _has_eligible_interval_reign(person, anchor: Anchor, rules: Rules) -> bool:
    assert anchor.start is not None and anchor.end is not None
    earliest_start = max(rules.horizon_start, person.birth + rules.min_accession_age)
    latest_start = min(
        anchor.start,
        rules.horizon_end - rules.min_reign + 1,
        person.death - rules.min_reign + 1,
    )
    for start in range(earliest_start, latest_start + 1):
        earliest_end = max(anchor.end, start + rules.min_reign - 1)
        latest_end = min(
            start + rules.max_reign - 1,
            person.death,
            rules.horizon_end,
        )
        if earliest_end <= latest_end:
            return True
    return False


def _eligible_start_bounds(person, rules: Rules) -> tuple[int, int]:
    return (
        max(rules.horizon_start, person.birth + rules.min_accession_age),
        min(
            rules.horizon_end - rules.min_reign + 1,
            person.death - rules.min_reign + 1,
        ),
    )


def _anchor_eligibility(problem: Problem, anchor: Anchor) -> Contradiction | None:
    people = {person.person_id: person for person in problem.people}
    person = people.get(anchor.person_id)
    if person is None:
        return Contradiction(
            "ELIGIBILITY",
            (anchor.anchor_id,),
            f"Anchor {anchor.anchor_id} requires {anchor.person_id}, but that person is absent from the problem.",
        )

    rules = problem.rules
    if anchor.start is not None and anchor.end is not None:
        if _has_eligible_interval_reign(person, anchor, rules):
            return None
        earliest_start = max(rules.horizon_start, person.birth + rules.min_accession_age)
        latest_start = min(
            anchor.start,
            rules.horizon_end - rules.min_reign + 1,
            person.death - rules.min_reign + 1,
        )
        latest_possible_end = min(
            latest_start + rules.max_reign - 1,
            person.death,
            rules.horizon_end,
        )
        return Contradiction(
            "ELIGIBILITY",
            (anchor.anchor_id,),
            (
                f"Anchor {anchor.anchor_id} requires {person.person_id} to reign throughout "
                f"years {anchor.start}–{anchor.end}, but no single reign can cover that interval "
                f"under horizon {rules.horizon_start}–{rules.horizon_end}, inclusive reign "
                f"length {rules.min_reign}–{rules.max_reign}, minimum accession age "
                f"{rules.min_accession_age} (birth {person.birth}, earliest age-eligible year "
                f"{person.birth + rules.min_accession_age}), and death year {person.death}. "
                f"The latest candidate accession start that could cover the anchor is "
                f"{latest_start} (eligible-start lower bound {earliest_start}); its latest "
                f"possible reign end is {latest_possible_end}.",
            ),
        )

    if anchor.lower is not None and anchor.upper is not None:
        eligible_lower, eligible_upper = _eligible_start_bounds(person, rules)
        intersection_lower = max(anchor.lower, eligible_lower)
        intersection_upper = min(anchor.upper, eligible_upper)
        if intersection_lower <= intersection_upper:
            return None
        return Contradiction(
            "ELIGIBILITY",
            (anchor.anchor_id,),
            (
                f"Anchor {anchor.anchor_id} requires {person.person_id}'s accession start in "
                f"{anchor.lower}–{anchor.upper}, but a valid reign start must lie in "
                f"{eligible_lower}–{eligible_upper} after applying horizon "
                f"{rules.horizon_start}–{rules.horizon_end}, minimum accession age "
                f"{rules.min_accession_age} (birth {person.birth}, earliest eligible year "
                f"{person.birth + rules.min_accession_age}), inclusive reign length "
                f"{rules.min_reign}–{rules.max_reign}, and death year {person.death}.",
            ),
        )
    return None


def _kin_path_exists(problem: Problem, source_id: str, target_id: str) -> bool:
    people = {person.person_id: person for person in problem.people}
    if source_id not in people or target_id not in people:
        return False
    queue = [source_id]
    seen = {source_id}
    while queue:
        previous_id = queue.pop(0)
        if previous_id == target_id:
            return True
        previous = people[previous_id]
        for current_id, current in people.items():
            if current_id in seen:
                continue
            if previous_id in current.parents or set(previous.parents) & set(current.parents):
                seen.add(current_id)
                queue.append(current_id)
    return False


def report_contradictions(problem: Problem) -> tuple[Contradiction, ...]:
    """Return only contradictions established by these solver-free checks.

    Soft and reveal anchors are intentionally outside this first pass. The
    reporter never changes a problem or infers that an unflagged problem is
    feasible.
    """
    findings: list[Contradiction] = []
    anchors = tuple(
        anchor for anchor in problem.anchors if anchor.kind in ("hard", "record")
    )

    # An interval anchor must fit inside one legal reign; a bounds anchor must
    # permit at least one legal accession start.
    for anchor in anchors:
        finding = _anchor_eligibility(problem, anchor)
        if finding is not None:
            findings.append(finding)

    # Two different rulers cannot both occupy the same layer in an overlapping
    # interval. Bounds-only anchors do not establish an interval for this test.
    for index, first in enumerate(anchors):
        if first.start is None or first.end is None:
            continue
        for second in anchors[index + 1:]:
            if second.start is None or second.end is None:
                continue
            if first.person_id == second.person_id:
                continue
            shared_layers = sorted(set(_target_layers(first)) & set(_target_layers(second)))
            if not shared_layers:
                continue
            overlap_start = max(first.start, second.start)
            overlap_end = min(first.end, second.end)
            if overlap_start <= overlap_end:
                findings.append(
                    Contradiction(
                        "ANCHOR_OVERLAP",
                        (first.anchor_id, second.anchor_id),
                        (
                            f"Anchors {first.anchor_id} ({first.person_id}, "
                            f"{first.start}–{first.end}) and {second.anchor_id} "
                            f"({second.person_id}, {second.start}–{second.end}) require "
                            f"different rulers on shared layer(s) {', '.join(shared_layers)} "
                            f"during overlapping years {overlap_start}–{overlap_end}; "
                            "each layer can have only one ruler at a time."
                        ),
                    )
                )

    # A continuous layer chain can move between chronologically ordered anchor
    # intervals only along directed child/sibling succession edges.
    for first in anchors:
        if first.start is None or first.end is None:
            continue
        for second in anchors:
            if second.start is None or second.end is None:
                continue
            if first.anchor_id == second.anchor_id or first.person_id == second.person_id:
                continue
            if first.end >= second.start:
                continue
            shared_layers = sorted(set(_target_layers(first)) & set(_target_layers(second)))
            if not shared_layers:
                continue
            if not _kin_path_exists(problem, first.person_id, second.person_id):
                findings.append(
                    Contradiction(
                        "NO_KIN_PATH",
                        (first.anchor_id, second.anchor_id),
                        (
                            f"Anchor {first.anchor_id} requires {first.person_id} through "
                            f"year {first.end}; later anchor {second.anchor_id} requires "
                            f"{second.person_id} from year {second.start}. No directed path "
                            "of allowed child/sibling successor relationships connects those "
                            f"people, so a continuous succession on shared layer(s) "
                            f"{', '.join(shared_layers)} cannot connect the anchors."
                        ),
                    )
                )

    order = {"ELIGIBILITY": 0, "ANCHOR_OVERLAP": 1, "NO_KIN_PATH": 2, "GAP_COVERAGE": 3}
    findings.sort(key=lambda item: (order.get(item.code, 99), item.anchor_ids, item.explanation))
    return tuple(findings)
