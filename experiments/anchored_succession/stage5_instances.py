"""Reusable deterministic Stage 5 larger-instance generator."""
from __future__ import annotations

from dataclasses import dataclass

from worldloom.core import Address, rng_for

from .model import Anchor, Person, Problem, Rules


@dataclass(frozen=True)
class Stage5LargerInstance:
    """Problem and diagnostics formerly constructed inline by the Stage 5 test."""

    index: int
    seed: int
    size: int
    horizon_end: int
    first_id: str
    last_id: str
    nonkin_ordered_pairs: int
    kin_bridge_exists: bool
    problem: Problem


def has_kin_path(problem: Problem, source_id: str, target_id: str) -> bool:
    """Directed graph reachability over allowed child/sibling successor edges."""
    people = {person.person_id: person for person in problem.people}
    if source_id not in people or target_id not in people:
        return False
    queue, seen = [source_id], {source_id}
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


def generate_stage5_larger_instance(index: int) -> Stage5LargerInstance:
    """Reproduce one of the 20 seeded Stage 5 instances without invoking a solver."""
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < 20:
        raise ValueError("Stage 5 instance index must be an integer from 0 through 19")

    size, horizon_end, seed = 10 + index % 3, 60 + index % 21, 20300000 + index
    prefix = f"I{index}-"
    rng = rng_for(
        seed,
        "worldloom.anchored_succession.larger",
        "3",
        Address(("anchored-succession", "round3-larger", str(index))),
        "lineages",
    )
    people = [Person(prefix + "L0", -100, horizon_end + 10),
              Person(prefix + "R0", -100, horizon_end + 10)]
    split = 2 + (size - 2) // 2
    for j in range(2, size):
        root = prefix + ("L0" if j < split else "R0")
        parents = (root,)
        if index % 4 == 0 and j == size - 1:
            parents = (prefix + "R0", prefix + "P2")
        people.append(Person(prefix + f"P{j}", -40 + rng.randint(0, 2), horizon_end + 10, parents))

    ids = [person.person_id for person in people]
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"instance={index}: duplicate person ids")
    rules = Rules(
        min_accession_age=16,
        min_reign=3,
        max_reign=20,
        preferred_reign=8,
        horizon_start=0,
        horizon_end=horizon_end,
        child_preference_weight=1,
        stability_weight=0,
    )
    first_id, last_id = prefix + "P2", prefix + f"P{size - 1}"
    anchors = (
        Anchor(f"r3-{index}-first", "hard", first_id, start=0, end=3),
        Anchor(f"r3-{index}-last", "hard", last_id, start=horizon_end - 3, end=horizon_end),
    )
    problem = Problem(tuple(people), anchors, rules, seed=seed)
    nonkin = sum(
        1 for previous in people for current in people
        if previous.person_id != current.person_id
        and previous.person_id not in current.parents
        and not (set(previous.parents) & set(current.parents))
    )
    return Stage5LargerInstance(
        index=index,
        seed=seed,
        size=size,
        horizon_end=horizon_end,
        first_id=first_id,
        last_id=last_id,
        nonkin_ordered_pairs=nonkin,
        kin_bridge_exists=has_kin_path(problem, first_id, last_id),
        problem=problem,
    )
