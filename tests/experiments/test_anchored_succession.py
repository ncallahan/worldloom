from __future__ import annotations
from dataclasses import replace
import pytest
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
    anchors = (Anchor("pin-A", "hard", "A", start=16, end=19),
               Anchor("prefer-B", "soft", "B", start=20, tolerance=0, weight=1))
    return Problem(people, anchors, small_rules())

def test_generated_pools_reproducible_seed_sensitive_and_fingerprint_pinned():
    assert len(family_fixture().people) == 12
    assert generated_pool(30, seed=101) == generated_pool(30, seed=101)
    assert generated_pool(30, seed=101) != generated_pool(30, seed=102)
    assert len(generated_pool(100, seed=101).people) == 100
    # Regression pin taken from CI output; this is not independent verification.
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

@pytest.mark.parametrize("size", [30, 100])
def test_generated_pool_spans_timeline_and_deaths_reach_horizon(size):
    pool = generated_pool(size, seed=101)
    births = [p.birth for p in pool.people]
    deaths = [p.death for p in pool.people]
    assert min(births) <= pool.rules.horizon_start + 10
    assert max(births) >= pool.rules.horizon_end - 100
    assert max(deaths) >= pool.rules.horizon_end - 10

def test_canonical_problem_description_ignores_person_and_anchor_order():
    problem = three_person_problem()
    shuffled = Problem(tuple(reversed(problem.people)), tuple(reversed(problem.anchors)), problem.rules, problem.seed)
    assert canonical_problem_data(problem) == canonical_problem_data(shuffled)

def test_canonical_fingerprint_excludes_stability_reference_but_tracks_semantic_changes():
    problem = three_person_problem()
    with_reference = replace(problem, stability_reference=(Reign("A", 16, 19),))
    assert canonical_problem_data(problem) == canonical_problem_data(with_reference)
    changed_anchor = replace(problem, anchors=(replace(problem.anchors[0], end=18), *problem.anchors[1:]))
    changed_rules = replace(problem, rules=replace(problem.rules, max_reign=7))
    changed_person = replace(problem, people=(replace(problem.people[0], birth=1), *problem.people[1:]))
    assert canonical_problem_data(problem) != canonical_problem_data(changed_anchor)
    assert canonical_problem_data(problem) != canonical_problem_data(changed_rules)
    assert canonical_problem_data(problem) != canonical_problem_data(changed_person)

def test_anchor_layer_defaults_and_soft_anchor_validation():
    assert Anchor("h", "hard", "A").layer == "both"
    assert Anchor("r", "record", "A").layer == "titular"
    assert Anchor("v", "reveal", "A", start=16, end=19).layer == "effective"
    with pytest.raises(ValueError, match="soft anchor requires start"):
        Anchor("s", "soft", "A")
    with pytest.raises(ValueError, match="soft anchor does not support lower/upper bounds"):
        Anchor("s", "soft", "A", start=16, lower=15, upper=17)

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
        problem = Problem((Person("A",0,30),Person("B",2,21,("A",))),
                          problem.anchors, problem.rules)
    _assert_error(problem, solution, expected)

def test_checker_rejects_invalid_succession_exactly():
    problem = Problem((Person("B",0,30),Person("C",0,30)), (), small_rules())
    solution = Solution((Reign("B",16,19),Reign("C",20,23)),(Reign("B",16,19),Reign("C",20,23)))
    _assert_error(problem, solution, "titular: invalid succession B->C")

def test_checker_reports_hard_anchor_interval_violation_exactly():
    solution = Solution((Reign("B",16,19),),(Reign("B",16,19),))
    _assert_error(three_person_problem(), solution, "anchor violated: pin-A (interval, titular)")

def test_checker_reports_hard_anchor_bounds_violation_exactly():
    problem = Problem((Person("A",0,30),),(Anchor("bounds-A","hard","A",lower=17,upper=18),),small_rules())
    solution = Solution((Reign("A",16,19),),(Reign("A",16,19),))
    _assert_error(problem, solution, "anchor violated: bounds-A (bounds, titular)")

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

def _record_reveal_case(marked: bool, titular_ruler: str) -> tuple[Problem, Solution]:
    people = (Person("A",0,30),Person("B",0,30,("A",)),Person("C",0,30,("A",)))
    anchors = (Anchor("record-A","record","A",start=16,end=19,marked_reveal=marked),
               Anchor("reveal-B","reveal","B",start=16,end=19))
    return Problem(people, anchors, small_rules()), Solution(
        (Reign(titular_ruler,16,19),), (Reign("B",16,19),))

def test_marked_record_and_reveal_can_coexist_when_titular_matches_record():
    problem, solution = _record_reveal_case(True, "A")
    assert check_solution(problem, solution) == ()

def test_marked_record_still_constrains_titular_layer():
    problem, solution = _record_reveal_case(True, "C")
    assert check_solution(problem, solution) == ("anchor violated: record-A (interval, titular)",)

def test_unmarked_record_and_overlapping_reveal_report_exact_contradiction():
    problem, solution = _record_reveal_case(False, "A")
    assert check_solution(problem, solution) == ("record contradicted by unmarked reveal: record-A->reveal-B",)

def test_hard_anchor_can_target_effective_layer_during_reveal():
    people = (Person("A",0,30),Person("B",0,30,("A",)))
    anchors = (Anchor("hard-B","hard","B",start=16,end=19,layer="effective"),
               Anchor("reveal-B","reveal","B",start=16,end=19))
    solution = Solution((Reign("A",16,19),),(Reign("B",16,19),))
    assert check_solution(Problem(people,anchors,small_rules()), solution) == ()

def test_both_layer_hard_anchor_conflicts_with_reveal_exactly():
    people = (Person("A",0,30),Person("B",0,30,("A",)))
    anchors = (Anchor("hard-A","hard","A",start=16,end=19,layer="both"),
               Anchor("reveal-B","reveal","B",start=16,end=19))
    solution = Solution((Reign("A",16,19),),(Reign("B",16,19),))
    _assert_error(Problem(people,anchors,small_rules()), solution,
                  "anchor violated: hard-A (interval, effective)")

def test_checker_reports_unoccupied_year_inside_anchor_span_exactly():
    people = (Person("A",0,19),Person("B",0,30))
    anchors = (Anchor("first","hard","A",start=16,end=19),
               Anchor("second","hard","B",start=25,end=28))
    solution = Solution((Reign("A",16,19),Reign("B",25,28)),
                        (Reign("A",16,19),Reign("B",25,28)))
    _assert_error(Problem(people,anchors,small_rules()), solution,
                  "titular: throne unoccupied at year 20 within anchored span")

def test_oracle_rederives_hand_calculated_optimum_and_infeasible_cases():
    problem = three_person_problem()
    expected = {(("A",16,19),("B",20,23))}
    actual = {tuple((r.ruler,r.start,r.end) for r in s.titular) for s in optimal_solutions(problem)}
    assert actual == expected
    result = oracle_result(problem)
    assert result.status == "solved"
    assert result.objective == evaluate_objective(problem,result.solution)
    impossible = Problem(problem.people,(Anchor("impossible","hard","missing",start=16,end=19),),problem.rules)
    assert oracle_result(impossible).status == "infeasible"

def test_oracle_marked_record_reveal_has_solutions_but_unmarked_is_infeasible():
    marked_problem, _ = _record_reveal_case(True, "A")
    unmarked_problem, _ = _record_reveal_case(False, "A")
    assert enumerate_solutions(marked_problem, node_cap=100_000)
    assert oracle_result(unmarked_problem, node_cap=100_000).status == "infeasible"

def test_oracle_gap_between_anchors_is_infeasible_when_no_successor_can_bridge_it():
    people = (Person("A",0,19),Person("Z",0,30))
    anchors = (Anchor("first","hard","A",start=16,end=19),
               Anchor("last","hard","Z",start=25,end=28))
    problem = Problem(people,anchors,small_rules())
    assert oracle_result(problem,node_cap=100_000).status == "infeasible"

def test_oracle_node_cap_raises_instead_of_hanging():
    with pytest.raises(OracleNodeLimitError,match="node cap exceeded"):
        enumerate_solutions(three_person_problem(),node_cap=1)

def test_oracle_rejects_more_than_six_people():
    with pytest.raises(ValueError,match="limited to 6 people"):
        enumerate_solutions(generated_pool(7))

def _objective_problem(people, rules=None, anchors=(), stability_reference=()):
    return Problem(tuple(people), tuple(anchors), rules or replace(small_rules(), horizon_start=0, horizon_end=30),
                   stability_reference=tuple(stability_reference))

def test_objective_soft_anchor_tolerance_hand_computed():
    rules = replace(small_rules(), preferred_reign=4, stability_weight=0)
    problem = _objective_problem((Person("A",0,30),), rules,
        (Anchor("soft-A","soft","A",start=18,tolerance=1,weight=3),))
    solution = Solution((Reign("A",16,19),),(Reign("A",16,19),))
    assert evaluate_objective(problem, solution) == 3

def test_objective_missing_soft_anchored_ruler_hand_computed():
    problem = _objective_problem((Person("A",0,30),),
        replace(small_rules(), preferred_reign=4, stability_weight=0),
        (Anchor("soft-missing","soft","C",start=16,weight=2),))
    solution = Solution((Reign("A",16,19),),(Reign("A",16,19),))
    assert evaluate_objective(problem, solution) == 62

def test_objective_preferred_length_deviation_counts_both_layers():
    problem = _objective_problem((Person("A",0,30),), replace(small_rules(), preferred_reign=4, stability_weight=0))
    solution = Solution((Reign("A",16,21),),(Reign("A",16,21),))
    assert evaluate_objective(problem, solution) == 4

def test_objective_sibling_succession_cost_counts_both_layers():
    people = (Person("A",0,30),Person("B",0,30,("A",)),Person("C",0,30,("A",)))
    rules = replace(small_rules(), preferred_reign=4, child_preference_weight=7, stability_weight=0)
    solution = Solution((Reign("B",16,19),Reign("C",20,23)),(Reign("B",16,19),Reign("C",20,23)))
    assert evaluate_objective(_objective_problem(people,rules), solution) == 14

def test_objective_stability_cost_counts_titular_mismatches_only():
    rules = replace(small_rules(), horizon_start=16, horizon_end=19, preferred_reign=4, stability_weight=5)
    problem = _objective_problem((Person("A",0,30),Person("B",0,30)), rules,
                                 stability_reference=(Reign("A",16,19),))
    solution = Solution((Reign("B",16,19),),(Reign("B",16,19),))
    assert evaluate_objective(problem, solution) == 20
