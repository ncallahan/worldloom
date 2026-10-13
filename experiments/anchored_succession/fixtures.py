"""Deterministic toy succession fixtures."""
from __future__ import annotations
from worldloom.core import Address, rng_for
from .model import Person, Problem

def family_fixture() -> Problem:
    people = (Person("A", 0, 80), Person("B", 20, 100, ("A",)), Person("C", 23, 110, ("A",)), Person("D", 45, 130, ("B",)), Person("E", 48, 140, ("B",)), Person("F", 50, 145, ("C",)), Person("G", 70, 165, ("D",)), Person("H", 72, 175, ("D",)), Person("I", 75, 180, ("E",)), Person("J", 80, 190, ("F",)), Person("K", 100, 220, ("G",)), Person("L", 105, 230, ("H",)))
    return Problem(people=people)

def generated_pool(size: int, seed: int = 20261013) -> Problem:
    if size < 1:
        raise ValueError("size must be positive")
    people = []
    for index in range(size):
        address = Address(("anchored-succession", "people", str(index)))
        rng = rng_for(seed, "worldloom.anchored_succession.pool", "1", address, "lifespan")
        birth = rng.randint(0, 260)
        death = min(300, birth + rng.randint(35, 95))
        parents = () if index < 2 or rng.random() < 0.25 else (f"P{rng.randrange(index)}",)
        people.append(Person(f"P{index}", birth, death, parents))
    return Problem(tuple(people), seed=seed)
