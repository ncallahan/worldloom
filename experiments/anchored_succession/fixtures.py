"""Deterministic, genealogically consistent toy succession fixtures."""
from __future__ import annotations
from worldloom.core import Address, rng_for
from .model import Person, Problem, Rules
def family_fixture() -> Problem:
    people = (Person("A", 0, 80), Person("B", 20, 100, ("A",)), Person("C", 23, 110, ("A",)), Person("D", 45, 130, ("B",)), Person("E", 48, 140, ("B",)), Person("F", 50, 145, ("C",)), Person("G", 70, 165, ("D",)), Person("H", 72, 175, ("D",)), Person("I", 75, 180, ("E",)), Person("J", 80, 190, ("F",)), Person("K", 100, 220, ("G",)), Person("L", 105, 230, ("H",)))
    return Problem(people=people)
def generated_pool(size: int, seed: int = 20261013) -> Problem:
    """Generate stable generations with parents old enough and alive at each birth."""
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        raise ValueError("size must be a positive integer")
    rules = Rules()
    people: list[Person] = []
    generation_size = 10
    for index in range(size):
        generation = index // generation_size
        address = Address(("anchored-succession", "people", str(index)))
        rng = rng_for(seed, "worldloom.anchored_succession.pool", "1", address, "lifespan")
        if generation == 0:
            birth = rng.randint(0, 10)
            death = birth + rng.randint(70, 90)
            parents = ()
        else:
            start = (generation - 1) * generation_size
            end = min(generation * generation_size, len(people))
            eligible = [p for p in people[start:end] if p.birth + rules.min_accession_age <= p.death]
            if not eligible:
                raise ValueError(f"no eligible parent for generation {generation}")
            parent = eligible[rng.randrange(len(eligible))]
            birth = rng.randint(parent.birth + rules.min_accession_age, min(parent.death, parent.birth + 30))
            death = birth + rng.randint(55, 85)
            parents = (parent.person_id,)
        people.append(Person(f"P{index}", birth, death, parents))
    return Problem(tuple(people), seed=seed)
