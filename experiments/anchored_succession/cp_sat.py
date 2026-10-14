"""OR-Tools CP-SAT adapter for the anchored-succession experiment.

The adapter is experiment-local. It reports the unperturbed objective evaluated
from its model variables; keyed tie-breaking is strictly subordinate to that
integer objective. Infeasibility explanations and anchor-removal suggestions
are exploratory, not automatic edits to authorial canon.
"""
from __future__ import annotations

from dataclasses import replace
from itertools import combinations
import random
from typing import Any

from .tie_break import cp_sat_tie_coefficient

from .checker import check_solution
from .model import Problem, Reign, Result, Solution
from .objective import evaluate_objective


def _load_cp_model() -> tuple[Any, str]:
    try:
        import ortools
        from ortools.sat.python import cp_model
    except ImportError as exc:
        raise RuntimeError(
            "CP-SAT backend is unavailable; install worldloom[cp-sat]"
        ) from exc
    return cp_model, ortools.__version__


def _target_layers(layer: str) -> tuple[str, ...]:
    return ("titular", "effective") if layer == "both" else (layer,)


def _ruler_at(reigns: tuple[Reign, ...], year: int) -> str | None:
    return next((reign.ruler for reign in reigns if reign.start <= year <= reign.end), None)


def _build_model(
    problem: Problem,
    assumption_states: dict[str, bool] | None = None,
    *,
    canonical_order: bool = True,
    order_seed: int | None = None,
    encoding: str = "legacy",
    tie_break: bool = True,
) -> dict[str, Any]:
    if encoding not in ("legacy", "linear-successor"):
        raise ValueError(f"unknown CP-SAT succession encoding: {encoding}")
    cp_model, version = _load_cp_model()
    model = cp_model.CpModel()
    rules = problem.rules
    years = tuple(range(rules.horizon_start, rules.horizon_end + 1))
    people = list(problem.people)
    anchor_order = list(problem.anchors)
    layer_order = ["titular", "effective"]
    creation_years = list(years)
    if canonical_order:
        people.sort(key=lambda item: item.person_id)
        anchor_order.sort(key=lambda item: item.anchor_id)
    else:
        shuffle_rng = random.Random(problem.seed if order_seed is None else order_seed)
        shuffle_rng.shuffle(people)
        shuffle_rng.shuffle(anchor_order)
        shuffle_rng.shuffle(layer_order)
        shuffle_rng.shuffle(creation_years)
    people = tuple(people)
    person_ids = {person.person_id for person in people}
    if len(person_ids) != len(people):
        raise ValueError("person_id values must be unique")
    anchor_ids = [anchor.anchor_id for anchor in problem.anchors]
    if len(set(anchor_ids)) != len(anchor_ids):
        raise ValueError("anchor_id values must be unique")
    if not years:
        raise ValueError("horizon_start must be <= horizon_end")

    presence: dict[tuple[str, str, int], Any] = {}
    starts: dict[tuple[str, str, int], Any] = {}
    used: dict[tuple[str, str], Any] = {}
    occupied: dict[tuple[str, int], Any] = {}
    start_occupied: dict[tuple[str, int], Any] = {}
    end_occupied: dict[tuple[str, int], Any] = {}
    anchor_lits: dict[str, Any] = {}
    real_terms: list[tuple[Any, int]] = []
    tie_terms: list[tuple[Any, int]] = []
    horizon_length = len(years)

    for anchor in anchor_order:
        if anchor.kind != "soft":
            anchor_lits[anchor.anchor_id] = model.NewBoolVar(f"anchor_{anchor.anchor_id}")

    for layer in layer_order:
        for person in people:
            for year in creation_years:
                variable = model.NewBoolVar(f"present_{layer}_{person.person_id}_{year}")
                presence[(layer, person.person_id, year)] = variable
                if year < person.birth + rules.min_accession_age or year > person.death:
                    model.Add(variable == 0)
            for year in creation_years:
                previous = presence[(layer, person.person_id, year - 1)] if year > years[0] else 0
                current = presence[(layer, person.person_id, year)]
                start = model.NewBoolVar(f"start_{layer}_{person.person_id}_{year}")
                starts[(layer, person.person_id, year)] = start
                model.Add(start <= current)
                if isinstance(previous, int):
                    model.Add(start == current)
                else:
                    model.Add(start + previous <= 1)
                    model.Add(start >= current - previous)
            used_var = model.NewBoolVar(f"used_{layer}_{person.person_id}")
            used[(layer, person.person_id)] = used_var
            person_presence = [presence[(layer, person.person_id, year)] for year in years]
            person_starts = [starts[(layer, person.person_id, year)] for year in years]
            model.Add(sum(person_starts) == used_var)
            model.Add(sum(person_presence) >= rules.min_reign * used_var)
            model.Add(sum(person_presence) <= rules.max_reign * used_var)
            deviation_limit = max(abs(rules.preferred_reign), abs(horizon_length - rules.preferred_reign))
            duration_deviation = model.NewIntVar(
                0, deviation_limit, f"duration_deviation_{layer}_{person.person_id}"
            )
            model.AddAbsEquality(duration_deviation, sum(person_presence) - rules.preferred_reign)
            duration_cost = model.NewIntVar(
                0, deviation_limit, f"duration_cost_{layer}_{person.person_id}"
            )
            model.Add(duration_cost == duration_deviation).OnlyEnforceIf(used_var)
            model.Add(duration_cost == 0).OnlyEnforceIf(used_var.Not())
            real_terms.append((duration_cost, 1))

    # Each layer is one non-empty, contiguous chain; no ruler may reappear.
    # Create all occupancy variables before adding constraints that reference
    # adjacent years, so the forward neighbor is always defined.
    for layer in layer_order:
        for year in creation_years:
            occ = model.NewBoolVar(f"occupied_{layer}_{year}")
            occupied[(layer, year)] = occ
            model.Add(sum(presence[(layer, p.person_id, year)] for p in people) == occ)
        for year in creation_years:
            occ = occupied[(layer, year)]
            start_occ = model.NewBoolVar(f"chain_start_{layer}_{year}")
            start_occupied[(layer, year)] = start_occ
            previous = occupied[(layer, year - 1)] if year > years[0] else 0
            model.Add(start_occ <= occ)
            if isinstance(previous, int):
                model.Add(start_occ == occ)
            else:
                model.Add(start_occ + previous <= 1)
                model.Add(start_occ >= occ - previous)
            end_occ = model.NewBoolVar(f"chain_end_{layer}_{year}")
            end_occupied[(layer, year)] = end_occ
            following = occupied[(layer, year + 1)] if year < years[-1] else 0
            model.Add(end_occ <= occ)
            if isinstance(following, int):
                model.Add(end_occ == occ)
            else:
                model.Add(end_occ + following <= 1)
                model.Add(end_occ >= occ - following)
        model.Add(sum(start_occupied[(layer, year)] for year in years) == 1)
        model.Add(sum(end_occupied[(layer, year)] for year in years) == 1)

    # A change of ruler must be a child or sibling succession. Keep the
    # pairwise encoding as the parity baseline; the linear encoding expresses
    # the same implication once per (layer, previous ruler, year).
    if encoding == "legacy":
        for layer in layer_order:
            for year, next_year in zip(years, years[1:]):
                for previous in people:
                    for current in people:
                        if previous.person_id == current.person_id:
                            continue
                        is_child = previous.person_id in current.parents
                        is_sibling = bool(set(previous.parents) & set(current.parents))
                        if is_child or is_sibling:
                            continue
                        model.Add(
                            presence[(layer, previous.person_id, year)]
                            + presence[(layer, current.person_id, next_year)] <= 1
                        )
    else:
        # If p is present at y but absent at y+1, either the next year is
        # unoccupied or an allowed child/sibling successor of p is present.
        # Occupancy is constrained to equal the sum of presence variables and
        # each layer has at most one ruler per year, so this is equivalent to
        # the legacy pairwise exclusions without enumerating disallowed pairs.
        for layer in layer_order:
            for year, next_year in zip(years, years[1:]):
                for previous in people:
                    allowed = []
                    for current in people:
                        if current.person_id == previous.person_id:
                            continue
                        if (previous.person_id in current.parents
                                or bool(set(previous.parents) & set(current.parents))):
                            allowed.append(presence[(layer, current.person_id, next_year)])
                    model.Add(
                        presence[(layer, previous.person_id, year)]
                        - presence[(layer, previous.person_id, next_year)]
                        <= sum(allowed, 1 - occupied[(layer, next_year)])
                    )

    def impossible_if_active(literal: Any) -> None:
        model.AddBoolOr([]).OnlyEnforceIf(literal)

    # Hard and record anchors constrain the requested layer(s); reveal anchors
    # constrain the effective ruler and require a distinct titular ruler.
    for anchor in anchor_order:
        if anchor.kind == "soft":
            continue
        literal = anchor_lits[anchor.anchor_id]
        if anchor.kind in ("hard", "record"):
            if anchor.start is not None and anchor.end is not None:
                if anchor.start > anchor.end or anchor.start < years[0] or anchor.end > years[-1]:
                    impossible_if_active(literal)
                elif anchor.person_id not in person_ids:
                    impossible_if_active(literal)
                else:
                    for layer in _target_layers(anchor.layer):
                        for year in range(anchor.start, anchor.end + 1):
                            model.Add(presence[(layer, anchor.person_id, year)] == 1).OnlyEnforceIf(literal)
            if anchor.lower is not None and anchor.upper is not None:
                for layer in _target_layers(anchor.layer):
                    if anchor.person_id not in person_ids:
                        impossible_if_active(literal)
                        break
                    start_vars = [
                        starts[(layer, anchor.person_id, year)]
                        for year in years if anchor.lower <= year <= anchor.upper
                    ]
                    model.Add(sum(start_vars) == 1).OnlyEnforceIf(literal)
        elif anchor.kind == "reveal":
            if anchor.start is None or anchor.end is None or anchor.start > anchor.end:
                impossible_if_active(literal)
                continue
            if anchor.start < years[0] or anchor.end > years[-1] or anchor.person_id not in person_ids:
                impossible_if_active(literal)
                continue
            for year in range(anchor.start, anchor.end + 1):
                model.Add(presence[("effective", anchor.person_id, year)] == 1).OnlyEnforceIf(literal)
                model.Add(presence[("titular", anchor.person_id, year)] == 0).OnlyEnforceIf(literal)

    # A marked record still constrains titular; only an unmarked conflicting
    # record/reveal pair is itself contradictory.
    for record in anchor_order:
        if record.kind != "record" or record.marked_reveal or record.start is None or record.end is None:
            continue
        for reveal in anchor_order:
            if reveal.kind != "reveal" or reveal.start is None or reveal.end is None:
                continue
            overlap = max(record.start, reveal.start) <= min(record.end, reveal.end)
            if overlap and record.person_id != reveal.person_id:
                model.AddBoolOr([
                    anchor_lits[record.anchor_id].Not(),
                    anchor_lits[reveal.anchor_id].Not(),
                ])

    # Occupancy spans are conditional on the hard/record interval anchors that
    # establish their endpoints. Pairwise endpoint constraints preserve the
    # rule when an anchor assumption is disabled for conflict analysis.
    interval_anchors = [
        anchor for anchor in anchor_order
        if anchor.kind in ("hard", "record") and anchor.start is not None and anchor.end is not None
    ]
    for left_index, left in enumerate(interval_anchors):
        for right in interval_anchors[left_index:]:
            first = min(left.start, right.start)
            last = max(left.end, right.end)
            literals = [anchor_lits[left.anchor_id]]
            if right.anchor_id != left.anchor_id:
                literals.append(anchor_lits[right.anchor_id])
            for year in range(max(first, years[0]), min(last, years[-1]) + 1):
                for layer in layer_order:
                    model.Add(occupied[(layer, year)] == 1).OnlyEnforceIf(literals)

    # Active reveal years are exactly the union of enabled reveal anchors.
    for year in years:
        covering_reveals = [
            anchor_lits[anchor.anchor_id] for anchor in anchor_order
            if anchor.kind == "reveal" and anchor.start is not None and anchor.end is not None
            and anchor.start <= year <= anchor.end
        ]
        if not covering_reveals:
            for person in people:
                model.Add(
                    presence[("titular", person.person_id, year)]
                    == presence[("effective", person.person_id, year)]
                )
            continue
        active_reveal = model.NewBoolVar(f"reveal_active_{year}")
        model.AddBoolOr(covering_reveals).OnlyEnforceIf(active_reveal)
        model.AddBoolAnd([literal.Not() for literal in covering_reveals]).OnlyEnforceIf(active_reveal.Not())
        for person in people:
            model.Add(
                presence[("titular", person.person_id, year)]
                == presence[("effective", person.person_id, year)]
            ).OnlyEnforceIf(active_reveal.Not())

    # Objective terms are kept separate from the tie-break expression so the
    # returned objective can be checked independently against evaluate_objective.
    for anchor in anchor_order:
        if anchor.kind != "soft":
            continue
        for layer in _target_layers(anchor.layer):
            if anchor.person_id not in person_ids:
                used_var = None
                start_expression = 0
            else:
                used_var = used[(layer, anchor.person_id)]
                start_expression = sum(
                    year * starts[(layer, anchor.person_id, year)] for year in years
                )
            max_distance = max(abs(year - anchor.start) for year in years)
            distance = model.NewIntVar(0, max_distance, f"soft_distance_{anchor.anchor_id}_{layer}")
            model.AddAbsEquality(distance, start_expression - anchor.start)
            tolerance_cost = model.NewIntVar(0, max_distance, f"soft_tolerance_cost_{anchor.anchor_id}_{layer}")
            model.AddMaxEquality(tolerance_cost, [distance - anchor.tolerance, 0])
            maximum_cost = max(horizon_length, max_distance) * abs(anchor.weight)
            cost = model.NewIntVar(0, maximum_cost, f"soft_cost_{anchor.anchor_id}_{layer}")
            if used_var is None:
                model.Add(cost == horizon_length * anchor.weight)
            else:
                model.Add(cost == tolerance_cost * anchor.weight).OnlyEnforceIf(used_var)
                model.Add(cost == horizon_length * anchor.weight).OnlyEnforceIf(used_var.Not())
            real_terms.append((cost, 1))

    if rules.child_preference_weight:
        for layer in layer_order:
            for year, next_year in zip(years, years[1:]):
                for previous in people:
                    for current in people:
                        if previous.person_id == current.person_id:
                            continue
                        is_sibling = bool(set(previous.parents) & set(current.parents))
                        is_child = previous.person_id in current.parents
                        if not is_sibling or is_child:
                            continue
                        transition = model.NewBoolVar(
                            f"sibling_transition_{layer}_{previous.person_id}_{current.person_id}_{year}"
                        )
                        before = presence[(layer, previous.person_id, year)]
                        after = presence[(layer, current.person_id, next_year)]
                        model.AddBoolAnd([before, after]).OnlyEnforceIf(transition)
                        model.AddBoolOr([before.Not(), after.Not()]).OnlyEnforceIf(transition.Not())
                        real_terms.append((transition, rules.child_preference_weight))

    if rules.stability_weight and problem.stability_reference:
        for year in creation_years:
            reference = _ruler_at(problem.stability_reference, year)
            same = model.NewBoolVar(f"stability_same_{year}")
            if reference in person_ids:
                model.Add(same == presence[("titular", reference, year)])
            elif reference is None:
                model.Add(same + occupied[("titular", year)] == 1)
            else:
                model.Add(same == 0)
            mismatch = model.NewBoolVar(f"stability_mismatch_{year}")
            model.Add(mismatch + same == 1)
            real_terms.append((mismatch, rules.stability_weight))

    tie_upper_bound = 0
    for layer in layer_order:
        for person in people:
            for year in years:
                coefficient = cp_sat_tie_coefficient(problem.seed, layer, person.person_id, year)
                tie_terms.append((presence[(layer, person.person_id, year)], coefficient))
                tie_upper_bound += coefficient
    subordinate_multiplier = tie_upper_bound + 1
    real_expression = sum(coefficient * variable for variable, coefficient in real_terms)
    tie_expression = sum(coefficient * variable for variable, coefficient in tie_terms)
    model.Minimize(subordinate_multiplier * real_expression + tie_expression if tie_break else real_expression)

    if assumption_states is None:
        model.AddAssumptions(list(anchor_lits.values()))
    else:
        assumptions = []
        for anchor_id, literal in anchor_lits.items():
            assumptions.append(literal if assumption_states.get(anchor_id, True) else literal.Not())
        model.AddAssumptions(assumptions)

    proto = model.Proto()
    return {
        "model": model,
        "version": version,
        "people": people,
        "years": years,
        "presence": presence,
        "real_terms": real_terms,
        "anchor_lits": anchor_lits,
        "model_variables": len(proto.variables),
        "model_constraints": len(proto.constraints),
    }


def _extract_solution(built: dict[str, Any], solver: Any) -> Solution:
    reign_sequences: dict[str, tuple[Reign, ...]] = {}
    for layer in ("titular", "effective"):
        reigns: list[Reign] = []
        current_person: str | None = None
        current_start: int | None = None
        previous_year: int | None = None
        for year in built["years"]:
            ruler = next(
                (person.person_id for person in built["people"]
                 if solver.Value(built["presence"][(layer, person.person_id, year)])),
                None,
            )
            if ruler != current_person or (previous_year is not None and year != previous_year + 1):
                if current_person is not None and current_start is not None and previous_year is not None:
                    reigns.append(Reign(current_person, current_start, previous_year))
                current_person, current_start = ruler, year if ruler is not None else None
            previous_year = year
        if current_person is not None and current_start is not None and previous_year is not None:
            reigns.append(Reign(current_person, current_start, previous_year))
        reign_sequences[layer] = tuple(reigns)
    return Solution(reign_sequences["titular"], reign_sequences["effective"])


def _map_cp_sat_status(status_code: int, cp_model: Any, *, time_limit_reached: bool) -> str:
    """Map CP-SAT status independently of solver construction for focused tests."""
    if status_code == cp_model.OPTIMAL:
        return "optimal"
    if status_code == cp_model.INFEASIBLE:
        return "infeasible"
    if status_code == cp_model.MODEL_INVALID:
        return "model_invalid"
    if status_code == cp_model.FEASIBLE:
        return "timeout" if time_limit_reached else "feasible"
    if status_code == cp_model.UNKNOWN:
        return "timeout" if time_limit_reached else "unknown"
    return "unknown"


def _solve_once(
    problem: Problem,
    time_limit_seconds: float | None,
    assumption_states: dict[str, bool] | None = None,
    *,
    canonical_order: bool = True,
    order_seed: int | None = None,
    encoding: str = "legacy",
    tie_break: bool = True,
) -> tuple[str, Any, Any]:
    cp_model, _ = _load_cp_model()
    built = _build_model(problem, assumption_states, canonical_order=canonical_order, order_seed=order_seed, encoding=encoding, tie_break=tie_break)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = int(problem.seed) % 2_147_483_647
    solver.parameters.randomize_search = False
    if time_limit_seconds is not None:
        solver.parameters.max_time_in_seconds = max(0.001, time_limit_seconds)
    status_code = solver.Solve(built["model"])
    # This adapter configures no early-stop mechanism other than the time limit.
    time_limit_reached = time_limit_seconds is not None and status_code in (cp_model.FEASIBLE, cp_model.UNKNOWN)
    built["status_code"] = status_code
    return _map_cp_sat_status(status_code, cp_model, time_limit_reached=time_limit_reached), solver, built


def _minimal_conflict_core(
    problem: Problem, initial_core: tuple[str, ...], time_limit_seconds: float | None
) -> tuple[tuple[str, ...], bool]:
    core = list(initial_core)
    conclusive = True
    for anchor_id in tuple(core):
        candidate = [item for item in core if item != anchor_id]
        states = {item.anchor_id: item.anchor_id in candidate for item in problem.anchors if item.kind != "soft"}
        status, _, _ = _solve_once(problem, time_limit_seconds, states)
        if status == "infeasible":
            core = candidate
        elif status not in ("optimal", "feasible"):
            conclusive = False
    return tuple(core), conclusive


def smallest_anchor_removals(
    problem: Problem, max_anchors: int = 12, time_limit_seconds: float | None = 5.0
) -> tuple[tuple[tuple[str, ...], int | None], ...] | None:
    """Find smallest anchor-removal sets restoring feasibility; exploratory."""
    ids = tuple(sorted(anchor.anchor_id for anchor in problem.anchors if anchor.kind != "soft"))
    all_disabled = {anchor_id: False for anchor_id in ids}
    baseline_status, _, baseline_built = _solve_once(problem, time_limit_seconds, all_disabled)
    cp_model, _ = _load_cp_model()
    if baseline_status == "infeasible":
        return None
    baseline_has_incumbent = baseline_built["status_code"] in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    if baseline_status not in ("optimal", "feasible", "timeout") or not baseline_has_incumbent:
        return ()
    if len(ids) > max_anchors:
        return ()
    for removal_count in range(1, len(ids) + 1):
        found: list[tuple[tuple[str, ...], int | None]] = []
        for removed in combinations(ids, removal_count):
            removed_set = set(removed)
            states = {anchor_id: anchor_id not in removed_set for anchor_id in ids}
            status, solver, built = _solve_once(problem, time_limit_seconds, states)
            if status == "infeasible":
                continue
            cp_model, _ = _load_cp_model()
            if status not in ("optimal", "feasible", "timeout") or built["status_code"] not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                # A timed-out subset test cannot support a minimality claim.
                return ()
            solution = _extract_solution(built, solver)
            relaxed_problem = replace(
                problem,
                anchors=tuple(anchor for anchor in problem.anchors if anchor.anchor_id not in removed_set),
            )
            errors = check_solution(relaxed_problem, solution)
            if errors:
                raise RuntimeError(
                    "CP-SAT anchor-removal suggestion failed independent checker: " + "; ".join(errors)
                )
            objective = evaluate_objective(relaxed_problem, solution)
            found.append((tuple(removed), objective))
        if found:
            return tuple(found)
    return ()


def solve_problem(
    problem: Problem,
    time_limit_seconds: float | None = 10.0,
    analyze_infeasible: bool = True,
    *,
    canonical_order: bool = True,
    order_seed: int | None = None,
    encoding: str = "legacy",
    tie_break: bool = True,
) -> Result:
    """Solve a problem with CP-SAT and return its unperturbed objective.

    The CP-SAT objective scales the real integer objective by more than the
    maximum possible sum of keyed tie coefficients. Thus no tie-break can
    compensate for a one-unit increase in the real objective.
    """
    status, solver, built = _solve_once(problem, time_limit_seconds, canonical_order=canonical_order, order_seed=order_seed, encoding=encoding, tie_break=tie_break)
    if status == "infeasible":
        explanation: list[str] = []
        core_literals = solver.SufficientAssumptionsForInfeasibility()
        index_to_id = {literal.Index(): anchor_id for anchor_id, literal in built["anchor_lits"].items()}
        core = tuple(sorted(index_to_id[index] for index in core_literals if index in index_to_id))
        minimal: bool | None = None
        if core:
            core, conclusive = _minimal_conflict_core(problem, core, time_limit_seconds)
            minimal = conclusive
            if core:
                explanation.append("CP-SAT conflicting anchor subset: " + ", ".join(core))
                explanation.append(
                    "Conflict subset is subset-minimal under deletion checks."
                    if conclusive else
                    "Conflict subset minimality is inconclusive because a deletion check did not finish."
                )
        else:
            explanation.append("CP-SAT proved infeasibility but returned no anchor-only sufficient core.")
        if analyze_infeasible:
            relaxations = smallest_anchor_removals(problem, time_limit_seconds=time_limit_seconds)
            if relaxations is None:
                explanation.append("Finding: infeasible independent of anchors; the model remains infeasible with all non-soft anchors disabled.")
            elif relaxations:
                sets_text = "; ".join(
                    "{" + ", ".join(ids) + f"}} (resulting objective {objective})"
                    for ids, objective in relaxations
                )
                explanation.append(
                    f"Exploratory smallest anchor-removal set(s): {sets_text}. "
                    "Minimality evidence: all smaller removal sets were tested and remained infeasible; "
                    "this is an authorial intervention suggestion, not an automatic edit."
                )
            else:
                explanation.append(
                    "No feasible anchor-removal set was found within the configured search bound; "
                    "this is inconclusive if the anchor count exceeded the search limit or a solve timed out."
                )
        return Result(
            "infeasible", explanation=tuple(explanation), backend="ortools-cp-sat",
            backend_version=built["version"], conflict_minimal=minimal,
            model_variables=built["model_variables"], model_constraints=built["model_constraints"],
        )
    if status in ("unknown", "model_invalid"):
        return Result(
            "unknown", explanation=(f"CP-SAT status: {status}",),
            backend="ortools-cp-sat", backend_version=built["version"],
            model_variables=built["model_variables"], model_constraints=built["model_constraints"],
        )

    if status == "timeout" and built["status_code"] != _load_cp_model()[0].FEASIBLE:
        return Result(
            "timeout", explanation=("CP-SAT time limit reached without an incumbent.",),
            backend="ortools-cp-sat", backend_version=built["version"],
            model_variables=built["model_variables"], model_constraints=built["model_constraints"],
        )

    solution = _extract_solution(built, solver)
    objective = sum(solver.Value(variable) * coefficient for variable, coefficient in built["real_terms"])
    errors = check_solution(problem, solution)
    if errors:
        return Result(
            "unknown", solution=solution, objective=objective,
            explanation=("independent checker rejected CP-SAT output: " + "; ".join(errors),),
            backend="ortools-cp-sat", backend_version=built["version"],
            model_variables=built["model_variables"], model_constraints=built["model_constraints"],
        )
    return Result(
        "solved" if status == "optimal" else status,
        solution=solution,
        objective=objective,
        explanation=() if status == "optimal" else ("CP-SAT returned a feasible incumbent but did not prove optimality.",),
        backend="ortools-cp-sat",
        backend_version=built["version"],
        model_variables=built["model_variables"], model_constraints=built["model_constraints"],
    )
