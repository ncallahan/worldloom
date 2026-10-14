"""Deterministic timeline-spanning, genealogically consistent toy fixtures."""
from __future__ import annotations
from worldloom.core import Address, rng_for
from .model import Anchor, Person, Problem, Rules

def family_fixture() -> Problem:
    people = (
        Person("A", 0, 80), Person("B", 20, 100, ("A",)), Person("C", 23, 110, ("A",)),
        Person("D", 45, 130, ("B",)), Person("E", 48, 140, ("B",)), Person("F", 50, 145, ("C",)),
        Person("G", 70, 165, ("D",)), Person("H", 72, 175, ("D",)), Person("I", 75, 180, ("E",)),
        Person("J", 80, 190, ("F",)), Person("K", 100, 220, ("G",)), Person("L", 105, 230, ("H",)),
    )
    return Problem(people=people)

def generated_pool(size: int, seed: int = 20261013) -> Problem:
    """Generate people across the horizon in generations with valid parent links."""
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        raise ValueError("size must be a positive integer")
    rules = Rules()
    latest_root_birth = rules.horizon_start + 10
    generations = min(size, max(2, (rules.horizon_end - latest_root_birth) // 30 + 1))
    people: list[Person] = []
    person_generation: list[int] = []
    for index in range(size):
        generation = min(generations - 1, index * generations // size)
        address = Address(("anchored-succession", "people", str(index)))
        rng = rng_for(seed, "worldloom.anchored_succession.pool", "2", address, "lifespan")
        if generation == 0:
            birth = rng.randint(rules.horizon_start, rules.horizon_start + 10)
            death = birth + rng.randint(70, 90)
            parents = ()
        else:
            parent_candidates = [
                p for p, p_generation in zip(people, person_generation)
                if p_generation == generation - 1
            ]
            if not parent_candidates:
                raise ValueError(f"no eligible parent for generation {generation}")
            parent = parent_candidates[rng.randrange(len(parent_candidates))]
            earliest_birth = parent.birth + 20
            latest_birth = min(parent.death, parent.birth + 30, rules.horizon_end)
            birth = rng.randint(earliest_birth, latest_birth)
            death = birth + rng.randint(55, 85)
            parents = (parent.person_id,)
        people.append(Person(f"P{index}", birth, death, parents))
        person_generation.append(generation)
    return Problem(tuple(people), seed=seed)


def generated_parity_instance(index: int, seed: int = 20261015) -> Problem:
    """Purpose-built tiny oracle instance with a long enough horizon for real reign chains.

    The seed and instance index are both incorporated into rng_for's address so
    generation is reproducible and independent of call order. Exactly three
    people can legally rule throughout the horizon; random parent links may
    leave some pairs unrelated, and each instance has zero to three hard anchors.
    """
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise ValueError("index must be a non-negative integer")
    address = Address(("anchored-succession", "parity", str(index)))
    rng = rng_for(seed, "worldloom.anchored_succession.parity", "1", address, "instance")
    horizon_end = rng.randint(40, 60)
    rules = Rules(
        min_accession_age=16, min_reign=3, max_reign=8, preferred_reign=4,
        horizon_start=0, horizon_end=horizon_end,
        child_preference_weight=rng.randint(0, 2), stability_weight=0,
    )
    people: list[Person] = []
    for i in range(3):
        parent_ids: tuple[str, ...] = ()
        if i and rng.random() < 0.8:
            parent_ids = (f"P{rng.randrange(i)}",)
        people.append(Person(f"P{i}", -30 + rng.randint(0, 5), horizon_end + 8, parent_ids))
    anchor_count = rng.randint(0, 3)
    anchors = []
    for j in range(anchor_count):
        person_id = f"P{rng.randrange(3)}"
        start = rng.randint(16, max(16, horizon_end - 5))
        end = min(horizon_end, start + rng.randint(2, 5))
        anchors.append(Anchor(f"parity-{index}-anchor-{j}", "hard", person_id, start=start, end=end))
    return Problem(tuple(people), tuple(anchors), rules, seed=seed + index)
