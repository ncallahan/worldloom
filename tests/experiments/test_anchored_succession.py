from __future__ import annotations
import pytest
from dataclasses import replace
from worldloom.core.hashing import fingerprint
from experiments.anchored_succession.checker import check_solution
from experiments.anchored_succession.fixtures import family_fixture, generated_pool
from experiments.anchored_succession.model import Anchor, Person, Problem, Reign, Rules, Solution, canonical_problem_data
from experiments.anchored_succession.objective import evaluate_objective
from experiments.anchored_succession.oracle import OracleNodeLimitError, enumerate_solutions, optimal_solutions, oracle_result

def small_rules() -> Rules:
    return Rules(min_accession_age=16, min_reign=3, max_reign=8, preferred_reign=4,
                 horizon_start=0, horizon_end=30, child_preference_weight=1, stability_weight=2)
def three_person_problem() -> Problem:
    people = (Person("A", 0, 30), Person("B", 2, 30, ("A",)), Person("C", 3, 30, ("A",)))
    return Problem(people, (Anchor("pin-A", "hard", "A", start=16, end=19),), small_rules())
def test_generated_pools_reproducible_and_seed_sensitive():
    assert len(family_fixture().people) == 12
    assert generated_pool(30, seed=101) == generated_pool(30, seed=101)
    assert generated_pool(30, seed=101) != generated_pool(30, seed=102)
    assert len(generated_pool(100, seed=101).people) == 100
    assert fingerprint(canonical_problem_data(generated_pool(30, seed=101))) == "4553773e6eef07c7b086109179b7bcfe21efac8fb993a0ec74bd83e9c2845915"
@pytest.mark.parametrize("size", [30, 100])
def test_generated_pool_parent_is_old_enough_and_alive_at_birth(size):
    pool = generated_pool(size, seed=101)
    people = {p.person_id: p for p in pool.people}
    for child in pool.people:
        for parent_id in child.parents:
            parent = people[parent_id]
            assert child.birth - parent.birth >= pool.rules.min_accession_age
            assert parent.birth <= child.birth <= parent.death
def test_canonical_problem_description_ignores_person_and_anchor_order():
    problem = three_person_problem()
    shuffled = Problem(tuple(reversed(problem.people)), tuple(reversed(problem.anchors)), problem.rules, problem.seed)
    assert canonical_problem_data(problem) == canonical_problem_data(shuffled)
def test_checker_accepts_hand_built_valid_single_reign():
    solution = Solution((Reign("A", 16, 19),), (Reign("A", 16, 19),))
    assert check_solution(three_person_problem(), solution) == ()
def _assert_error(problem: Problem, solution: Solution, expected: str):
    errors = check_solution(problem, solution)
    assert expected in errors, f"expected {expected!r}; got {errors!r}"
@pytest.mark.parametrize(("solution", "expected"), [
    (Solution((Reign("A",16,18),Reign("A",19,21)),(Reign("A",16,18),Reign("A",19,21))), "titular: ruler repeats: A"),
    (Solution((Reign("A",16,17),),(Reign("A",16,17),)), "titular: invalid reign length: A"),
    (Solution((Reign("A",10,18),),(Reign("A",10,18),)), "titular: invalid reign length: A"),
    (Solution((Reign("A",-1,2),),(Reign("A",-1,2),)), "titular: reign outside horizon: A"),
    (Solution((Reign("B",10,13),),(Reign("B",10,13),)), "titular: accession too young: B"),
    (Solution((Reign("A",16,19),Reign("B",20,23)),(Reign("A",16,19),Reign("B",20,23))), "titular: ruler dies before reign ends: B"),
    (Solution((Reign("A",16,19),Reign("B",21,24)),(Reign("A",16,19),Reign("B",21,24))), "titular: reign chain not contiguous"),
])
def test_checker_rejects_each_hard_rule_violation(solution, expected):
    problem = three_person_problem()
    if "ruler dies before reign ends" in expected:
        problem = Problem((Person("A",0,30),Person("B",2,21,("A",))), problem.anchors, problem.rules)
    _assert_error(problem, solution, expected)
def test_checker_rejects_invalid_succession_exactly():
    problem = Problem((Person("B",0,30),Person("C",0,30)), (), small_rules())
    solution = Solution((Reign("B",16,19),Reign("C",20,23)),(Reign("B",16,19),Reign("C",20,23)))
    _assert_error(problem, solution, "titular: invalid succession B->C")
def test_checker_reports_hard_anchor_interval_violation_exactly():
    solution = Solution((Reign("B",16,19),),(Reign("B",16,19),))
    _assert_error(three_person_problem(), solution, "anchor violated: pin-A (interval)")
def test_checker_reports_hard_anchor_bounds_violation_exactly():
    problem = Problem((Person("A",0,30),),(Anchor("bounds-A","hard","A",lower=17,upper=18),),small_rules())
    solution = Solution((Reign("A",16,19),),(Reign("A",16,19),))
    _assert_error(problem, solution, "anchor violated: bounds-A (bounds)")
def test_checker_reports_reveal_not_expressed_exactly():
    people = (Person("A",0,30),Person("B",0,30,("A",)))
    problem = Problem(people,(Anchor("reveal-B","reveal","B",start=16,end=19),),small_rules())
    same = Solution((Reign("B",16,19),),(Reign("B",16,19),))
    _assert_error(problem, same, "reveal not expressed at 16: reveal-B")
def test_checker_reports_wrong_effective_ruler_exactly():
    people = (Person("A",0,30),Person("B",0,30,("A",)),Person("C",0,30,("A",)))
    problem = Problem(people,(Anchor("reveal-C","reveal","C",start=16,end=19),),small_rules())
    solution = Solution((Reign("A",16,19),),(Reign("B",16,19),))
    _assert_error(problem, solution, "reveal wrong effective ruler at 16: reveal-C")
def test_checker_reports_divergence_outside_reveal_exactly():
    people = (Person("A",0,30),Person("B",0,30,("A",)))
    solution = Solution((Reign("A",16,19),),(Reign("B",16,19),))
    _assert_error(Problem(people,(),small_rules()), solution, "titular/effective diverge outside reveal at 16")
def test_checker_reports_record_contradicted_by_unmarked_reveal():
    people = (Person("A",0,30),Person("B",0,30,("A",)))
    anchors = (Anchor("record-A","record","A",start=16,end=19),Anchor("reveal-B","reveal","B",start=16,end=19))
    solution = Solution((Reign("A",16,19),),(Reign("B",16,19),))
    _assert_error(Problem(people,anchors,small_rules()), solution,
                  "record contradicted by unmarked reveal: record-A->reveal-B")
def test_oracle_matches_hand_derived_optimal_solution_set_and_infeasible_case():
    problem = three_person_problem()
    expected = {(("A",16,19),),(("A",16,19),("B",20,23)),(("A",16,19),("C",20,23))}
    actual = {tuple((r.ruler,r.start,r.end) for r in s.titular) for s in optimal_solutions(problem)}
    assert actual == expected
    result = oracle_result(problem)
    assert result.status == "solved"
    assert result.objective == evaluate_objective(problem,result.solution)
    impossible = Problem(problem.people,(Anchor("impossible","hard","missing",start=16,end=19),),problem.rules)
    assert oracle_result(impossible).status == "infeasible"
def test_oracle_node_cap_raises_instead_of_hanging():
    with pytest.raises(OracleNodeLimitError,match="node cap exceeded"):
        enumerate_solutions(three_person_problem(),node_cap=1)
def test_oracle_rejects_more_than_six_people():
    with pytest.raises(ValueError,match="limited to 6 people"):
        enumerate_solutions(generated_pool(7))
def test_seed_and_generator_identity_are_excluded_from_problem_fingerprint():
    original = generated_pool(30,seed=101)
    changed_metadata = replace(original, seed=999, generator_id="another-generator", generator_version="99")
    assert canonical_problem_data(original) == canonical_problem_data(changed_metadata)
