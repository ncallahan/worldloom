"""Experimental ASP adapter for anchored succession reconciliation.

The ASP encoding is intentionally local to this experiment.  It mirrors the
solver-neutral Problem/Result contract and validates every returned model
with the independent checker and objective evaluator.
"""
from __future__ import annotations

from dataclasses import replace
from itertools import combinations
import json
import random
from threading import Event, Timer
from time import perf_counter
from typing import Any

from .tie_break import clingo_tie_weight

from .checker import check_solution
from .model import Problem, Reign, Result, Solution
from .objective import evaluate_objective


def _load_clingo() -> tuple[Any, str]:
    try:
        import clingo
    except ImportError as exc:
        raise RuntimeError("clingo backend requires the optional 'clingo' extra") from exc
    return clingo, getattr(clingo, "__version__", "unknown")


def _asp_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _layers(layer: str) -> tuple[str, ...]:
    return ("titular", "effective") if layer == "both" else (layer,)


def _ruler_at(reigns: tuple[Reign, ...], year: int) -> str | None:
    return next((reign.ruler for reign in reigns if reign.start <= year <= reign.end), None)


def _sum_numbers(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, dict):
        return sum(_sum_numbers(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return sum(_sum_numbers(item) for item in value)
    return 0


def _ground_rule_count(lp_stats: dict[str, Any]) -> int:
    """Count grounded rules across clingo's per-kind statistics."""
    rules = lp_stats.get("rules")
    if rules is not None:
        return _sum_numbers(rules)
    return sum(
        _sum_numbers(value)
        for key, value in lp_stats.items()
        if key.startswith("rules_")
    )

class _GroundingCounter:
    """Count grounded normal and choice rules using clingo's observer API."""

    def __init__(self) -> None:
        self.rules = 0

    def rule(self, choice: bool, head: list[int], body: list[int]) -> None:
        self.rules += 1

    def weight_rule(self, choice: bool, head: list[int], lower: int, body: list[tuple[int, int]]) -> None:
        self.rules += 1

def _program(
    problem: Problem, *, canonical_order: bool = True, order_seed: int | None = None,
    encoding: str = "legacy",
) -> tuple[str, tuple[str, ...]]:
    if encoding not in ("legacy", "aggregate-successor"):
        raise ValueError(f"unknown clingo succession encoding: {encoding}")
    rules = problem.rules
    years = tuple(range(rules.horizon_start, rules.horizon_end + 1))
    people = list(problem.people)
    anchors = list(problem.anchors)
    parents = [(child.person_id, parent) for child in people for parent in child.parents]
    if canonical_order:
        people.sort(key=lambda item: item.person_id)
        anchors.sort(key=lambda item: item.anchor_id)
        parents.sort()
    else:
        order_rng = random.Random(problem.seed if order_seed is None else order_seed)
        order_rng.shuffle(people)
        order_rng.shuffle(anchors)
        order_rng.shuffle(parents)

    facts: list[str] = []
    facts.extend(f"year({year})." for year in years)
    facts.extend(('layer(titular).', 'layer(effective).'))
    facts.extend(
        f"person({_asp_string(person.person_id)},{person.birth},{person.death})."
        for person in people
    )
    facts.extend(
        f"parent({_asp_string(child)},{_asp_string(parent)})."
        for child, parent in parents
    )
    facts.extend((
        f"min_age({rules.min_accession_age}).",
        f"min_reign({rules.min_reign}).",
        f"max_reign({rules.max_reign}).",
        f"preferred_reign({rules.preferred_reign}).",
        f"child_weight({rules.child_preference_weight}).",
        f"stability_weight({rules.stability_weight}).",
        f"horizon_length({len(years)}).",
    ))
    for layer_name in ("titular", "effective"):
        for person in people:
            for year in years:
                weight = clingo_tie_weight(
                    problem.seed, problem.generator_id, problem.generator_version,
                    layer_name, person.person_id, year,
                )
                facts.append(
                    f"tie_weight({layer_name},{_asp_string(person.person_id)},{year},{weight})."
                )

    externals = [
        f"{{ active({_asp_string(anchor.anchor_id)}) }}."
        for anchor in anchors if anchor.kind != "soft"
    ]
    reveal_facts = [
        f"reveal_period({_asp_string(anchor.anchor_id)},{anchor.start},{anchor.end})."
        for anchor in anchors
        if anchor.kind == "reveal" and anchor.start is not None and anchor.end is not None
    ]
    soft_facts: list[str] = []
    for anchor in anchors:
        if anchor.kind != "soft":
            continue
        for layer_name in _layers(anchor.layer):
            soft_facts.append(
                f"soft_anchor({_asp_string(anchor.anchor_id)},{_asp_string(anchor.person_id)},"
                f"{anchor.start},{anchor.tolerance},{anchor.weight},{layer_name})."
            )

    dynamic: list[str] = []
    interval_anchors = [
        anchor for anchor in anchors
        if anchor.kind in ("hard", "record") and anchor.start is not None and anchor.end is not None
    ]
    for anchor in anchors:
        if anchor.kind == "soft":
            continue
        active = f"active({_asp_string(anchor.anchor_id)})"
        if anchor.kind in ("hard", "record"):
            if anchor.start is not None and anchor.end is not None:
                if (
                    anchor.start > anchor.end
                    or anchor.start < rules.horizon_start
                    or anchor.end > rules.horizon_end
                ):
                    dynamic.append(f":- {active}.")
                else:
                    for layer_name in _layers(anchor.layer):
                        for year in range(anchor.start, anchor.end + 1):
                            dynamic.append(
                                f":- {active}, not present({layer_name},"
                                f"{_asp_string(anchor.person_id)},{year})."
                            )
            if anchor.lower is not None and anchor.upper is not None:
                for layer_name in _layers(anchor.layer):
                    dynamic.append(
                        f":- {active}, #count {{ Y : start({layer_name},"
                        f"{_asp_string(anchor.person_id)},Y), Y >= {anchor.lower}, "
                        f"Y <= {anchor.upper} }} != 1."
                    )
        elif anchor.kind == "reveal":
            if (
                anchor.start is None or anchor.end is None
                or anchor.start > anchor.end
                or anchor.start < rules.horizon_start
                or anchor.end > rules.horizon_end
            ):
                dynamic.append(f":- {active}.")
            else:
                for year in range(anchor.start, anchor.end + 1):
                    dynamic.append(
                        f":- {active}, not present(effective,{_asp_string(anchor.person_id)},{year})."
                    )
                    dynamic.append(
                        f":- {active}, present(titular,{_asp_string(anchor.person_id)},{year})."
                    )

    for index, left in enumerate(interval_anchors):
        for right in interval_anchors[index:]:
            first = min(left.start, right.start)
            last = max(left.end, right.end)
            active_terms = [f"active({_asp_string(left.anchor_id)})"]
            if right.anchor_id != left.anchor_id:
                active_terms.append(f"active({_asp_string(right.anchor_id)})")
            for year in range(max(first, rules.horizon_start), min(last, rules.horizon_end) + 1):
                for layer_name in ("titular", "effective"):
                    dynamic.append(
                        f":- {', '.join(active_terms)}, not occupied({layer_name},{year})."
                    )

    for record in anchors:
        if (
            record.kind != "record" or record.marked_reveal
            or record.start is None or record.end is None
        ):
            continue
        for reveal in anchors:
            if (
                reveal.kind != "reveal" or reveal.start is None or reveal.end is None
                or record.person_id == reveal.person_id
            ):
                continue
            if max(record.start, reveal.start) <= min(record.end, reveal.end):
                dynamic.append(
                    f":- active({_asp_string(record.anchor_id)}), "
                    f"active({_asp_string(reveal.anchor_id)})."
                )

    if not canonical_order:
        order_rng = random.Random(problem.seed if order_seed is None else order_seed)
        order_rng.shuffle(facts)
        order_rng.shuffle(externals)
        order_rng.shuffle(reveal_facts)
        order_rng.shuffle(soft_facts)
        order_rng.shuffle(dynamic)

    starts_rule = (
        ":- start(L,P,Y), start(L,P,Z), Y < Z."
        if encoding == "legacy"
        else ":- person(P,_,_), layer(L), #count { Y : start(L,P,Y) } > 1."
    )
    succession_rule = (
        ":- present(L,P,Y), present(L,Q,Z), Z = Y+1, P != Q, not parent(Q,P), not sibling(P,Q)."
        if encoding == "legacy"
        else ":- end(L,P,Y), occupied(L,Y+1), #count { Q : present(L,Q,Y+1), succ(P,Q) } = 0."
    )
    core_rules = r"""
0 { present(L,P,Y) : person(P,_,_) } 1 :- layer(L), year(Y).
:- present(L,P,Y), person(P,B,_), min_age(A), Y < B + A.
:- present(L,P,Y), person(P,_,D), Y > D.
occupied(L,Y) :- present(L,_,Y).
start(L,P,Y) :- present(L,P,Y), not present(L,P,Y-1).
end(L,P,Y) :- present(L,P,Y), not present(L,P,Y+1).
start_occ(L,Y) :- occupied(L,Y), not occupied(L,Y-1).
end_occ(L,Y) :- occupied(L,Y), not occupied(L,Y+1).
:- layer(L), #count { Y : start_occ(L,Y) } != 1.
:- layer(L), #count { Y : end_occ(L,Y) } != 1.
used(L,P) :- present(L,P,_).
__STARTS_RULE__
duration(L,P,N) :- used(L,P), N = #count { Y : present(L,P,Y) }.
:- duration(L,P,N), min_reign(M), N < M.
:- duration(L,P,N), max_reign(M), N > M.
sibling(P,Q) :- parent(P,A), parent(Q,A), P != Q.
succ(P,Q) :- parent(Q,P).
succ(P,Q) :- sibling(P,Q), not parent(Q,P).
__SUCCESSION_RULE__
reveal_active(Y) :- active(ID), reveal_period(ID,S,E), year(Y), Y >= S, Y <= E.
:- present(titular,P,Y), not present(effective,P,Y), not reveal_active(Y).
:- present(effective,P,Y), not present(titular,P,Y), not reveal_active(Y).
real_cost(C,key(duration,L,P)) :- duration(L,P,N), preferred_reign(T), N >= T, C = N-T, C > 0.
real_cost(C,key(duration,L,P)) :- duration(L,P,N), preferred_reign(T), N < T, C = T-N.
real_cost(C,key(soft,ID,L)) :- soft_anchor(ID,P,T,Tol,W,L), start(L,P,S), S >= T, D = S-T, D > Tol, C = (D-Tol)*W.
real_cost(C,key(soft,ID,L)) :- soft_anchor(ID,P,T,Tol,W,L), start(L,P,S), S < T, D = T-S, D > Tol, C = (D-Tol)*W.
real_cost(0,key(soft,ID,L)) :- soft_anchor(ID,P,T,Tol,_,L), start(L,P,S), S >= T, S-T <= Tol.
real_cost(0,key(soft,ID,L)) :- soft_anchor(ID,P,T,Tol,_,L), start(L,P,S), S < T, T-S <= Tol.
real_cost(C,key(soft_missing,ID,L)) :- soft_anchor(ID,P,_,_,W,L), not used(L,P), horizon_length(H), C = H*W.
real_cost(W,key(sibling,L,P,Q,Y)) :- present(L,P,Y), present(L,Q,Z), Z = Y+1, P != Q, sibling(P,Q), not parent(Q,P), child_weight(W).
real_cost(W,key(stability,Y)) :- stability_weight(W), W > 0, reference_at(Y,P), not present(titular,P,Y).
real_cost(W,key(stability,Y)) :- stability_weight(W), W > 0, reference_empty(Y), occupied(titular,Y).
tie_cost(W,key(tie,L,P,Y)) :- tie_weight(L,P,Y,W), present(L,P,Y).
#minimize { C@2,K : real_cost(C,K); W@1,K : tie_cost(W,K) }.
#show present/3.
#show real_cost/2.
"""
    core_rules = core_rules.replace("__STARTS_RULE__", starts_rule).replace("__SUCCESSION_RULE__", succession_rule)
    reference_facts: list[str] = []
    if problem.stability_reference:
        for year in years:
            ruler = _ruler_at(problem.stability_reference, year)
            if ruler is None:
                reference_facts.append(f"reference_empty({year}).")
            else:
                reference_facts.append(f"reference_at({year},{_asp_string(ruler)}).")
    source = "\n".join(
        facts + externals + reveal_facts + soft_facts + reference_facts + [core_rules] + dynamic
    )
    return source, tuple(anchor.anchor_id for anchor in anchors if anchor.kind != "soft")


def _solve_once(
    problem: Problem,
    time_limit_seconds: float | None,
    assumption_states: dict[str, bool] | None = None,
    *,
    canonical_order: bool = True,
    order_seed: int | None = None,
    encoding: str = "legacy",
) -> tuple[str, Solution | None, int | None, dict[str, Any], tuple[str, ...]]:
    clingo, version = _load_clingo()
    source, anchor_ids = _program(
        problem, canonical_order=canonical_order, order_seed=order_seed, encoding=encoding
    )
    ctl = clingo.Control(["0", "--stats=2"])
    grounding_counter = _GroundingCounter()
    ctl.register_observer(grounding_counter)
    ctl.configuration.solve.models = 0
    ctl.configuration.solve.opt_mode = "opt"
    ctl.configuration.stats = "2"
    ctl.add("base", [], source)
    ground_start = perf_counter()
    ctl.ground([("base", [])])
    grounding_time = perf_counter() - ground_start
    stats = ctl.statistics
    problem_stats = stats.get("problem", {}).get("lp", {})
    metadata: dict[str, Any] = {
        "version": version,
        "ground_atoms": len(ctl.symbolic_atoms),
        "ground_rules": max(grounding_counter.rules, _ground_rule_count(problem_stats)),
        "grounding_time_seconds": round(grounding_time, 6),
        "solve_time_seconds": 0.0,
    }

    assumptions = []
    for anchor_id in anchor_ids:
        symbol = clingo.Function("active", [clingo.String(anchor_id)])
        state = True if assumption_states is None else assumption_states.get(anchor_id, True)
        assumptions.append((symbol, state))
    core_literals: list[int] = []
    best_symbols: tuple[Any, ...] | None = None
    best_optimal = False
    timed_out = Event()

    def on_core(literals: list[int]) -> None:
        core_literals.extend(literals)

    timer = None
    if time_limit_seconds is not None:
        def interrupt() -> None:
            timed_out.set()
            ctl.interrupt()
        timer = Timer(max(0.001, time_limit_seconds), interrupt)
        timer.daemon = True
        timer.start()
    solve_start = perf_counter()
    first_solution_time: float | None = None
    proven_optimal_time: float | None = None
    try:
        with ctl.solve(
            assumptions=assumptions, yield_=True, on_core=on_core
        ) as handle:
            for model in handle:
                elapsed = perf_counter() - solve_start
                if first_solution_time is None:
                    first_solution_time = elapsed
                best_symbols = tuple(model.symbols(shown=True))
                best_optimal = bool(model.optimality_proven)
                if best_optimal:
                    proven_optimal_time = elapsed
            if best_symbols is None:
                try:
                    core_literals.extend(handle.core())
                except (AttributeError, RuntimeError):
                    pass
            result = handle.get()
    finally:
        if timer is not None:
            timer.cancel()
    metadata["solve_time_seconds"] = round(perf_counter() - solve_start, 6)
    metadata["time_to_first_solution_seconds"] = (
        round(first_solution_time, 6) if first_solution_time is not None else None
    )
    metadata["time_to_proven_optimal_seconds"] = (
        round(proven_optimal_time, 6)
        if proven_optimal_time is not None and result.exhausted and result.satisfiable and not result.interrupted
        else None
    )
    metadata["ground_atoms"] = len(ctl.symbolic_atoms)
    metadata["ground_rules"] = max(grounding_counter.rules, _ground_rule_count(ctl.statistics.get("problem", {}).get("lp", {})))
    if best_symbols is None:
        if result.unsatisfiable:
            literals_by_id: dict[int, str] = {}
            for anchor_id in anchor_ids:
                symbol = clingo.Function("active", [clingo.String(anchor_id)])
                atom = ctl.symbolic_atoms[symbol]
                if atom is not None:
                    literals_by_id[atom.literal] = anchor_id
            core_ids = tuple(sorted(
                anchor_id for literal, anchor_id in literals_by_id.items()
                if literal in core_literals or -literal in core_literals
            ))
            return "infeasible", None, None, metadata, core_ids
        return ("timeout" if timed_out.is_set() and result.interrupted else "unknown",
                None, None, metadata, ())

    if best_symbols is not None:
        best_optimal = bool(result.exhausted and result.satisfiable and not result.interrupted)
    solution = _solution_from_symbols(best_symbols)
    asp_objective = sum(
        int(symbol.arguments[0].number)
        for symbol in best_symbols
        if symbol.name == "real_cost"
    )
    validation_problem = problem
    if assumption_states is not None:
        validation_problem = replace(
            problem,
            anchors=tuple(
                anchor for anchor in problem.anchors
                if anchor.kind == "soft" or assumption_states.get(anchor.anchor_id, True)
            ),
        )
    checker_errors = check_solution(validation_problem, solution)
    if checker_errors:
        raise RuntimeError("clingo solution failed independent checker: " + "; ".join(checker_errors))
    evaluated = evaluate_objective(validation_problem, solution)
    if evaluated != asp_objective:
        raise RuntimeError(
            f"clingo unperturbed objective mismatch: ASP={asp_objective}, evaluator={evaluated}"
        )
    if timed_out.is_set() and result.interrupted:
        return "timeout", solution, asp_objective, metadata, ()
    return ("solved" if best_optimal else "feasible"), solution, asp_objective, metadata, ()


def _solution_from_symbols(symbols: tuple[Any, ...]) -> Solution:
    occupants: dict[str, dict[int, str]] = {"titular": {}, "effective": {}}
    for symbol in symbols:
        if symbol.name != "present":
            continue
        layer = symbol.arguments[0].name
        person = symbol.arguments[1].string
        year = symbol.arguments[2].number
        occupants[layer][year] = person

    sequences: dict[str, tuple[Reign, ...]] = {}
    for layer, by_year in occupants.items():
        reigns: list[Reign] = []
        for year in sorted(by_year):
            person = by_year[year]
            if reigns and reigns[-1].ruler == person and reigns[-1].end + 1 == year:
                previous = reigns[-1]
                reigns[-1] = Reign(previous.ruler, previous.start, year)
            else:
                reigns.append(Reign(person, year, year))
        sequences[layer] = tuple(reigns)
    return Solution(sequences["titular"], sequences["effective"])


def _minimal_conflict_core(
    problem: Problem, initial_core: tuple[str, ...], time_limit_seconds: float | None,
    *, encoding: str = "legacy",
) -> tuple[tuple[str, ...], bool]:
    core = list(initial_core)
    conclusive = True
    for anchor_id in tuple(core):
        candidate = [item for item in core if item != anchor_id]
        states = {
            anchor.anchor_id: anchor.anchor_id in candidate
            for anchor in problem.anchors if anchor.kind != "soft"
        }
        status, _, _, _, _ = _solve_once(problem, time_limit_seconds, states, encoding=encoding)
        if status == "infeasible":
            core = candidate
        elif status not in ("solved", "feasible"):
            conclusive = False
    return tuple(core), conclusive


def smallest_anchor_removals(
    problem: Problem, max_anchors: int = 12, time_limit_seconds: float | None = 5.0,
    *, encoding: str = "legacy",
) -> tuple[tuple[tuple[str, ...], int | None], ...] | None:
    """Return exploratory smallest removal sets; None means anchor-independent infeasibility."""
    ids = tuple(sorted(anchor.anchor_id for anchor in problem.anchors if anchor.kind != "soft"))
    all_disabled = {anchor_id: False for anchor_id in ids}
    baseline_status, baseline_solution, _, _, _ = _solve_once(
        problem, time_limit_seconds, all_disabled, encoding=encoding
    )
    if baseline_status == "infeasible":
        return None
    if baseline_status not in ("solved", "feasible", "timeout") or baseline_solution is None:
        return ()
    if len(ids) > max_anchors:
        return ()
    for count in range(1, len(ids) + 1):
        found: list[tuple[tuple[str, ...], int | None]] = []
        for removed in combinations(ids, count):
            removed_set = set(removed)
            states = {anchor_id: anchor_id not in removed_set for anchor_id in ids}
            status, solution, _, _, _ = _solve_once(problem, time_limit_seconds, states, encoding=encoding)
            if status == "infeasible":
                continue
            if status not in ("solved", "feasible", "timeout") or solution is None:
                return ()
            relaxed = replace(
                problem,
                anchors=tuple(anchor for anchor in problem.anchors if anchor.anchor_id not in removed_set),
            )
            errors = check_solution(relaxed, solution)
            if errors:
                raise RuntimeError("anchor-removal suggestion failed independent checker: " + "; ".join(errors))
            found.append((tuple(removed), evaluate_objective(relaxed, solution)))
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
) -> Result:
    status, solution, objective, metadata, core_ids = _solve_once(
        problem, time_limit_seconds, canonical_order=canonical_order, order_seed=order_seed, encoding=encoding
    )
    explanation: list[str] = []
    minimal: bool | None = None
    if status == "infeasible":
        if core_ids:
            core_ids, conclusive = _minimal_conflict_core(problem, core_ids, time_limit_seconds, encoding=encoding)
            minimal = conclusive
            explanation.append("clingo conflicting anchor subset: " + ", ".join(core_ids))
            explanation.append(
                "Conflict subset is subset-minimal under deletion checks."
                if conclusive else
                "Conflict subset minimality is inconclusive because a deletion check did not finish."
            )
        else:
            explanation.append("clingo proved infeasibility but returned no anchor-assumption core.")
        if analyze_infeasible:
            removals = smallest_anchor_removals(problem, time_limit_seconds=time_limit_seconds, encoding=encoding)
            if removals is None:
                explanation.append(
                    "Finding: infeasible independent of anchors; disabling all non-soft anchors remains infeasible."
                )
            elif removals:
                rendered = "; ".join(
                    "{" + ", ".join(ids) + f"}} (resulting objective {cost})"
                    for ids, cost in removals
                )
                explanation.append(
                    f"Exploratory smallest anchor-removal set(s): {rendered}. "
                    "All smaller removal sets were checked; this is authorial decision support, not an automatic edit."
                )
            else:
                explanation.append(
                    "No smallest anchor-removal set was established; search bound or solver timeout makes this inconclusive."
                )
    return Result(
        status,
        solution=solution,
        objective=objective,
        explanation=tuple(explanation),
        backend="clingo-asp",
        backend_version=metadata["version"],
        conflict_minimal=minimal,
        ground_atoms=metadata["ground_atoms"],
        ground_rules=metadata["ground_rules"],
        grounding_time_seconds=metadata["grounding_time_seconds"],
        solve_time_seconds=metadata["solve_time_seconds"],
    )
