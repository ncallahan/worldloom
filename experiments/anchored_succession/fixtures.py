"""Deterministic timeline-spanning, genealogically consistent toy fixtures."""
from __future__ import annotations
from worldloom.core import Address, rng_for
from .model import Person, Problem, Rules

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
