from __future__ import annotations
import pytest
from experiments.anchored_succession.checker import check_solution
from experiments.anchored_succession.fixtures import family_fixture, generated_pool
from experiments.anchored_succession.model import Anchor, Person, Problem, Reign, Solution, canonical_problem_data
from experiments.anchored_succession.oracle import enumerate_solutions

def tiny_problem():
    people = (Person("A", 0, 70), Person("B", 20, 90, ("A",)), Person("C", 22, 95, ("A",)), Person("D", 42, 120, ("B",)))
    anchors = (Anchor("anchor-A", "hard", "A", start=16, end=35),)
    return Problem(people, anchors)

def test_fixture_and_seeded_pools_are_reproducible():
    assert len(family_fixture().people) == 12
    assert generated_pool(30) == generated_pool(30)
    assert len(generated_pool(100).people) == 100

def test_canonical_problem_description_ignores_person_and_anchor_order():
    problem = tiny_problem()
    shuffled = Problem(tuple(reversed(problem.people)), tuple(reversed(problem.anchors)), problem.rules, problem.seed)
    assert canonical_problem_data(problem) == canonical_problem_data(shuffled)

def test_independent_checker_rejects_empty_and_accepts_valid_single_reign():
    problem = tiny_problem()
    assert check_solution(problem, Solution((), ()))
    valid = Solution((Reign("A", 16, 35),), (Reign("A", 16, 35),))
    assert check_solution(problem, valid) == ()

def test_brute_force_oracle_is_tiny_only_and_returns_nonempty_solutions():
    solutions = enumerate_solutions(tiny_problem())
    assert len(solutions) > 0
    assert all(check_solution(tiny_problem(), solution) == () for solution in solutions)
    with pytest.raises(ValueError, match="limited to 6 people"):
        enumerate_solutions(generated_pool(7))
