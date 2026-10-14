"""Guarded construction-only size measurements; never invokes either solver."""
from __future__ import annotations
import argparse, json, os, resource, subprocess, sys, tempfile
from pathlib import Path
from time import perf_counter
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SIZES = (12, 30, 100)
HORIZON_YEARS = 300
SOLVE_HORIZON_YEARS = 250
WALL_LIMIT_SECONDS = 70
DATA_LIMIT_BYTES = 6 * 1024 * 1024 * 1024

def _limits() -> None:
    # Generous data-segment cap; unlike RLIMIT_AS this does not cap all virtual mappings.
    resource.setrlimit(resource.RLIMIT_DATA, (DATA_LIMIT_BYTES, DATA_LIMIT_BYTES))

def _problem(size: int, horizon_years: int):
    from dataclasses import replace
    from experiments.anchored_succession.fixtures import generated_pool
    from experiments.anchored_succession.model import Anchor
    if horizon_years < 12: raise ValueError("horizon_years must be at least 12")
    generated = generated_pool(size)
    end = horizon_years - 1
    problem = replace(generated, rules=replace(generated.rules, horizon_start=0, horizon_end=end), anchors=())
    years = (max(0, end // 6), end // 2, (end * 5) // 6)
    anchors = tuple(Anchor(f"scale-pin-{i}", "hard", f"P{i}", start=year, end=year + 2)
                    for i, year in enumerate(years))
    return replace(problem, anchors=anchors)

def _non_kin_ordered_pairs(problem) -> int:
    count = 0
    for previous in problem.people:
        for current in problem.people:
            if previous.person_id == current.person_id: continue
            child = previous.person_id in current.parents
            sibling = bool(set(previous.parents) & set(current.parents))
            if not child and not sibling: count += 1
    return count

def _constraint_type(constraint) -> str:
    if hasattr(constraint, "WhichOneof"):
        return constraint.WhichOneof("constraint") or "unknown"
    # OR-Tools 9.15 exposes a pybind ConstraintProto without protobuf's WhichOneof.
    for kind in (
        "linear", "bool_or", "bool_and", "at_most_one", "exactly_one", "bool_xor",
        "int_div", "int_mod", "int_prod", "lin_max", "int_max", "int_min",
        "all_diff", "element", "circuit", "routes", "table", "automaton", "inverse",
        "reservoir", "interval", "no_overlap", "no_overlap_2d", "cumulative",
    ):
        has_kind = getattr(constraint, f"has_{kind}", None)
        if callable(has_kind) and has_kind():
            return kind
    raise RuntimeError(f"unable to classify CP-SAT constraint proto of type {type(constraint).__name__}")


def _peak_rss_bytes() -> int:
    # Linux reports ru_maxrss in KiB.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)

def _worker(size: int, backend: str, horizon_years: int, encoding: str = "legacy") -> dict[str, object]:
    problem = _problem(size, horizon_years)
    started = perf_counter()
    if backend == "cp-sat":
        from experiments.anchored_succession.cp_sat import _build_model
        built = _build_model(problem, encoding=encoding); elapsed = perf_counter() - started
        proto = built["model"].Proto(); breakdown = {}
        for constraint in proto.constraints:
            kind = _constraint_type(constraint)
            breakdown[kind] = breakdown.get(kind, 0) + 1
        years = problem.rules.horizon_end - problem.rules.horizon_start + 1
        with tempfile.TemporaryDirectory() as temp_dir:
            proto_path = Path(temp_dir) / "model.pb"
            if not built["model"].export_to_file(str(proto_path)):
                raise RuntimeError("CP-SAT failed to export its model proto")
            proto_bytes = proto_path.stat().st_size
        return {"people":size,"horizon_years":horizon_years,"backend":backend,"encoding":encoding,"status":"measured",
          "build_time_seconds":elapsed,"model_variables":len(proto.variables),
          "model_constraints":len(proto.constraints),"constraints_by_type":dict(sorted(breakdown.items())),
          "model_proto_bytes":proto_bytes,
          "succession_constraint_count_analytic":2*(years-1)*_non_kin_ordered_pairs(problem),
          "succession_constraint_count_basis":"analytic: layers x (years-1) x ordered non-kin pairs",
          "succession_family_size_analytic": (2*(years-1)*_non_kin_ordered_pairs(problem) if encoding == "legacy" else 2*(years-1)*len(problem.people)),
          "peak_rss_bytes":_peak_rss_bytes(),"solve_invoked":False}
    import clingo
    from experiments.anchored_succession.clingo_backend import _GroundingCounter, _program
    clingo_encoding = "legacy" if encoding == "legacy" else "aggregate-successor"
    program,_ = _program(problem, encoding=clingo_encoding); program_bytes=len(program.encode("utf-8")); ground_started=perf_counter()
    counter=_GroundingCounter(); control=clingo.Control(["--warn=none"])
    control.register_observer(counter,replace=True); control.add("base",[],program); control.ground([("base",[])])
    years=problem.rules.horizon_end-problem.rules.horizon_start+1
    return {"people":size,"horizon_years":horizon_years,"backend":backend,"encoding":encoding,"status":"measured",
      "program_build_time_seconds":ground_started-started,"grounding_time_seconds":perf_counter()-ground_started,
      "ground_atoms":len(control.symbolic_atoms),"ground_rules":counter.rules,"program_bytes":program_bytes,
      "succession_constraint_count_analytic":2*(years-1)*_non_kin_ordered_pairs(problem),
      "succession_constraint_count_basis":"legacy analytical pair count; improved uses one aggregate rule per (layer, person, year)",
      "succession_family_size_analytic": (2*(years-1)*_non_kin_ordered_pairs(problem) if encoding == "legacy" else 2*(years-1)*len(problem.people)),
      "peak_rss_bytes":_peak_rss_bytes(),"solve_invoked":False}



def succession_chain_problem(size: int, horizon_years: int = 250, seed: int = 20261014,
                              include_soft_anchors: bool = False):
    """Build and independently validate a planted long-chain scale instance.

    Start with generated_pool(size) for stable pool identities, then use a
    purpose-built sibling group so five eligible rulers can cover a 250-year
    anchored span. The benchmark rules deliberately allow 50-year reigns;
    this makes the lower bound transparent: a 250-year occupied span cannot
    be covered by fewer than five rulers.
    """
    from dataclasses import replace
    from math import ceil
    from experiments.anchored_succession.checker import check_solution
    from experiments.anchored_succession.fixtures import generated_pool
    from experiments.anchored_succession.model import Anchor, Person, Reign, Rules, Solution

    if size < 6:
        raise ValueError("succession-chain fixture requires at least six people")
    if horizon_years < 250:
        raise ValueError("succession-chain fixture requires a horizon of at least 250 years")
    base = generated_pool(size, seed=seed)
    end = horizon_years - 1
    people = [Person("P0", -100, end)]
    for index in range(1, size):
        # P1..P5 are eligible siblings for the planted chain. Other generated
        # identities are deliberately ineligible for a minimum-length reign.
        death = end if index <= 5 else 1
        people.append(Person(f"P{index}", -30, death, ("P0",)))
    rules = Rules(
        min_accession_age=16, min_reign=3, max_reign=50, preferred_reign=50,
        horizon_start=0, horizon_end=end, child_preference_weight=0, stability_weight=0,
    )
    anchors = [
        Anchor("chain-first", "hard", "P1", start=0, end=4),
        Anchor("chain-last", "hard", "P5", start=end - 4, end=end),
    ]
    if include_soft_anchors:
        anchors.append(Anchor("chain-mid-soft", "soft", "P3", start=100, tolerance=5, weight=1))
    problem = replace(base, people=tuple(people), rules=rules, anchors=tuple(anchors))
    planted = Solution(
        tuple(Reign(f"P{i}", (i - 1) * 50, i * 50 - 1) for i in range(1, 6)),
        tuple(Reign(f"P{i}", (i - 1) * 50, i * 50 - 1) for i in range(1, 6)),
    )
    errors = check_solution(problem, planted)
    if errors:
        raise RuntimeError("planted succession-chain fixture failed independent checker: " + "; ".join(errors))
    span = end + 1
    lower_bound = ceil(span / rules.max_reign)
    if len(planted.titular) < 5 or lower_bound < 5:
        raise RuntimeError("succession-chain fixture did not establish the required five-ruler lower bound")
    return problem, planted, lower_bound

def _solve_worker(size: int, backend: str, time_limit_seconds: float, seed: int) -> dict[str, object]:
    from experiments.anchored_succession.checker import check_solution
    from experiments.anchored_succession.clingo_backend import solve_problem as solve_clingo
    from experiments.anchored_succession.cp_sat import solve_problem as solve_cp_sat
    from experiments.anchored_succession.objective import evaluate_objective

    problem, planted, ruler_lower_bound = succession_chain_problem(
        size, horizon_years=SOLVE_HORIZON_YEARS, seed=seed, include_soft_anchors=True
    )
    started = perf_counter()
    if backend == "cp-sat":
        result = solve_cp_sat(
            problem, time_limit_seconds=time_limit_seconds,
            encoding="linear-successor", tie_break=True,
        )
        diagnostic_started = perf_counter()
        without_tie = solve_cp_sat(
            problem, time_limit_seconds=time_limit_seconds,
            encoding="linear-successor", tie_break=False,
        )
        tie_diagnostic = {
            "status": without_tie.status, "objective": without_tie.objective,
            "wall_time_seconds": perf_counter() - diagnostic_started,
            "solution_present": without_tie.solution is not None,
            "returned_ruler_count": len(without_tie.solution.titular) if without_tie.solution else None,
            "time_limit_seconds": time_limit_seconds,
        }
    else:
        result = solve_clingo(
            problem, time_limit_seconds=time_limit_seconds, encoding="aggregate-successor"
        )
        tie_diagnostic = None
    elapsed = perf_counter() - started
    checker_errors = check_solution(problem, result.solution) if result.solution is not None else ()
    return {
        "people": size, "horizon_years": SOLVE_HORIZON_YEARS, "backend": backend,
        "encoding": "linear-successor" if backend == "cp-sat" else "aggregate-successor",
        "benchmark_type": "planted succession chain; long anchored span",
        "status": result.status, "objective": result.objective,
        "returned_ruler_count": len(result.solution.titular) if result.solution else None,
        "checker_errors": list(checker_errors), "checker_valid": not checker_errors and result.solution is not None,
        "planted_ruler_count": len(planted.titular), "minimum_rulers_required_by_span": ruler_lower_bound,
        "wall_time_seconds": elapsed, "time_limit_seconds": time_limit_seconds,
        "peak_rss_bytes": _peak_rss_bytes(),
        "anchor_count": len(problem.anchors),
        "anchors": [{"person_id": a.person_id, "start": a.start, "end": a.end, "kind": a.kind} for a in problem.anchors],
        "grounding_time_seconds": result.grounding_time_seconds,
        "solve_time_seconds": result.solve_time_seconds,
        "ground_atoms": result.ground_atoms, "ground_rules": result.ground_rules,
        "solution_present": result.solution is not None, "solve_invoked": True,
        "anchor_sampling": "deterministic planted first/last hard anchors; optional mid-chain soft anchor",
        "cp_sat_tie_break_diagnostic": tie_diagnostic,
    }

def _anchor_interval_legal(person, start: int, end: int, rules) -> bool:
    return (
        rules.horizon_start <= start <= end <= rules.horizon_end
        and person.birth + rules.min_accession_age <= start
        and person.death >= end
        and end - start + 1 >= rules.min_reign
    )


def _kin_bridge_possible(problem, earlier, later) -> bool:
    """Coarse graph reachability only; ignores exact reign-duration scheduling."""
    people = {person.person_id: person for person in problem.people}
    low, high = earlier.start, later.end
    def available(person):
        first = max(low, problem.rules.horizon_start, person.birth + problem.rules.min_accession_age)
        last = min(high, problem.rules.horizon_end, person.death)
        return last - first + 1 >= problem.rules.min_reign
    def allowed(previous_id, current_id):
        previous, current = people[previous_id], people[current_id]
        return (
            previous_id in current.parents
            or bool(set(previous.parents) & set(current.parents))
        )
    start_id, target_id = earlier.person_id, later.person_id
    queue = [start_id]
    visited = {start_id}
    while queue:
        previous_id = queue.pop(0)
        if previous_id == target_id:
            return True
        for current_id, person in people.items():
            if current_id in visited or not available(person):
                continue
            if allowed(previous_id, current_id):
                visited.add(current_id)
                queue.append(current_id)
    return False


def _pair_worker(size: int, backend: str, time_limit_seconds: float,
                 sampler: str = "adversarial") -> dict[str, object]:
    from dataclasses import replace
    from experiments.anchored_succession.fixtures import generated_pool
    from experiments.anchored_succession.model import Anchor
    from worldloom.core import Address, rng_for

    if sampler not in ("adversarial", "eligible-gap"):
        raise ValueError(f"unknown anchor-pair sampler: {sampler}")
    rows = []
    for seed in (20261014, 20261015, 20261016):
        base = generated_pool(size, seed=seed)
        rules = replace(base.rules, horizon_start=0, horizon_end=HORIZON_YEARS - 1)
        pool = list(base.people)
        for pair_index in range(3):
            rng = rng_for(
                seed, "worldloom.anchored_succession.anchor_pairs", "2",
                Address(("anchored-succession", "pairs", str(size), sampler)),
                f"pair-{pair_index}",
            )
            if sampler == "adversarial":
                first_index = rng.randrange(len(pool))
                second_index = rng.randrange(len(pool) - 1)
                if second_index >= first_index:
                    second_index += 1
                first_year = rng.randrange(0, HORIZON_YEARS - 2)
                second_year = rng.randrange(0, HORIZON_YEARS - 2)
                while second_year == first_year:
                    second_year = rng.randrange(0, HORIZON_YEARS - 2)
            else:
                selected = None
                for _ in range(10000):
                    first_index = rng.randrange(len(pool))
                    second_index = rng.randrange(len(pool) - 1)
                    if second_index >= first_index:
                        second_index += 1
                    first_person, second_person = pool[first_index], pool[second_index]
                    first_min = max(0, first_person.birth + rules.min_accession_age)
                    first_max = min(HORIZON_YEARS - 3, first_person.death - 2)
                    if first_min > first_max:
                        continue
                    first_year = rng.randint(first_min, first_max)
                    gap = rng.randint(10, 80)
                    second_year = first_year + 3 + gap
                    if second_year + 2 > HORIZON_YEARS - 1:
                        continue
                    if not _anchor_interval_legal(first_person, first_year, first_year + 2, rules):
                        continue
                    if not _anchor_interval_legal(second_person, second_year, second_year + 2, rules):
                        continue
                    selected = (first_index, second_index, first_year, second_year)
                    break
                if selected is None:
                    raise RuntimeError(
                        f"eligible-gap sampler could not find legal pair: size={size}, seed={seed}, pair={pair_index}"
                    )
                first_index, second_index, first_year, second_year = selected
            anchors = (
                Anchor(f"pair-{seed}-{pair_index}-A", "hard", pool[first_index].person_id,
                       start=first_year, end=first_year + 2),
                Anchor(f"pair-{seed}-{pair_index}-B", "hard", pool[second_index].person_id,
                       start=second_year, end=second_year + 2),
            )
            problem = replace(base, rules=rules, anchors=anchors)
            anchor_diagnostics = []
            people_by_id = {person.person_id: person for person in pool}
            for anchor in anchors:
                person = people_by_id[anchor.person_id]
                anchor_diagnostics.append({
                    "anchor_id": anchor.anchor_id, "person_id": anchor.person_id,
                    "start": anchor.start, "end": anchor.end,
                    "birth": person.birth, "death": person.death,
                    "earliest_legal_year": person.birth + rules.min_accession_age,
                    "legal_for_whole_interval": _anchor_interval_legal(person, anchor.start, anchor.end, rules),
                })
            earlier, later = sorted(anchors, key=lambda item: (item.start, item.end))
            bridge_possible = _kin_bridge_possible(problem, earlier, later)
            started = perf_counter()
            if backend == "cp-sat":
                # One raw solve per sampled pair: avoid post-infeasibility analyses.
                from experiments.anchored_succession.cp_sat import _solve_once, _extract_solution
                from experiments.anchored_succession.objective import evaluate_objective
                raw_status, solver, built = _solve_once(
                    problem, time_limit_seconds, encoding="linear-successor"
                )
                solution = _extract_solution(built, solver) if raw_status in ("optimal", "feasible") else None
                status = "solved" if raw_status == "optimal" else raw_status
                objective = evaluate_objective(problem, solution) if solution is not None else None
                grounding_time = None
                solve_time = None
            else:
                from experiments.anchored_succession.clingo_backend import _solve_once
                status, solution, objective, metadata, _ = _solve_once(
                    problem, time_limit_seconds, encoding="aggregate-successor"
                )
                grounding_time = metadata.get("grounding_time_seconds")
                solve_time = metadata.get("solve_time_seconds")
            feasible = status in ("solved", "optimal", "feasible") or (status == "timeout" and solution is not None)
            row = {
                "seed": seed, "pair_index": pair_index, "people": size, "backend": backend,
                "sampler": sampler,
                "encoding": "linear-successor" if backend == "cp-sat" else "aggregate-successor",
                "status": status, "solution_present": solution is not None, "feasible": feasible,
                "proven_infeasible": status == "infeasible", "objective": objective,
                "wall_time_seconds": perf_counter() - started, "time_limit_seconds": time_limit_seconds,
                "anchors": anchor_diagnostics,
                "gap_years_between_intervals": later.start - earlier.end - 1,
                "gap_kin_bridge_possible_by_graph": bridge_possible,
                "grounding_time_seconds": grounding_time, "solve_time_seconds": solve_time,
            }
            rows.append(row)
            # Stream partial progress so the parent can preserve samples if its
            # batch guard fires before the final JSON summary is emitted.
            print(json.dumps({"partial_sample": row}), flush=True)
    decided = [row for row in rows if row["status"] in ("solved", "feasible", "infeasible")]
    both_eligible = [row for row in rows if all(a["legal_for_whole_interval"] for a in row["anchors"])]
    return {
        "mode": "pairs", "sampler": sampler, "people": size, "backend": backend,
        "encoding": "linear-successor" if backend == "cp-sat" else "aggregate-successor",
        "samples": rows, "sample_count": len(rows),
        "feasible_fraction_all_samples": sum(bool(row["feasible"]) for row in rows) / len(rows) if rows else None,
        "feasible_fraction_among_decided": (
            sum(bool(row["feasible"]) for row in decided) / len(decided) if decided else None
        ),
        "proven_infeasible_count": sum(bool(row["proven_infeasible"]) for row in rows),
        "timeout_or_unknown_count": sum(row["status"] in ("timeout", "unknown") for row in rows),
        "both_anchors_eligible_count": len(both_eligible),
        "at_least_one_anchor_ineligible_count": len(rows) - len(both_eligible),
        "kin_bridge_possible_count": sum(bool(row["gap_kin_bridge_possible_by_graph"]) for row in rows),
        "no_kin_bridge_by_graph_count": sum(not bool(row["gap_kin_bridge_possible_by_graph"]) for row in rows),
        "peak_rss_bytes": _peak_rss_bytes(),
        "note": (
            "Adversarial pairs retain the old arbitrary sampler. eligible-gap pairs constrain each "
            "anchor person to be legally alive and old enough over the full interval, with a 10–80-year "
            "inter-anchor gap. Graph reachability is a coarse necessary diagnostic, not a proof of feasibility."
        ),
    }

def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path); parser.add_argument("--worker",action="store_true"); parser.add_argument("--mode",choices=("construction","solve","pairs"),default="construction"); parser.add_argument("--time-limit-seconds",type=float,default=60.0); parser.add_argument("--seed",type=int,default=20261014); parser.add_argument("--sampler",choices=("adversarial","eligible-gap"),default="adversarial")
    parser.add_argument("--size",type=int,choices=SIZES); parser.add_argument("--backend",choices=("cp-sat","clingo"))
    parser.add_argument("--horizon-years",type=int,default=HORIZON_YEARS); parser.add_argument("--encoding",choices=("legacy","improved","both","linear-successor","aggregate-successor"),default="legacy"); args=parser.parse_args()
    if args.worker:
        if args.size is None or args.backend is None: parser.error("--worker requires --size and --backend")
        if args.mode == "solve":
            print(json.dumps(_solve_worker(args.size, args.backend, args.time_limit_seconds, args.seed))); return
        if args.mode == "pairs":
      for size in SIZES:
       for backend in ("cp-sat", "clingo"):
        improved_encoding = "linear-successor" if backend == "cp-sat" else "aggregate-successor"
        construction_command = [
            sys.executable, "-m", "experiments.anchored_succession.measure_construction",
            "--worker", "--mode", "construction", "--size", str(size), "--backend", backend,
            "--horizon-years", str(HORIZON_YEARS), "--encoding", improved_encoding,
        ]
        construction = subprocess.run(
            construction_command, check=True, capture_output=True, text=True,
            timeout=WALL_LIMIT_SECONDS, cwd=REPOSITORY_ROOT,
            preexec_fn=_limits if os.name=="posix" else None,
        )
        try:
          construction_row = json.loads(construction.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError) as exc:
          raise RuntimeError(f"{backend} grounding preflight size={size} returned invalid JSON") from exc
        measured_grounding = construction_row.get("grounding_time_seconds")
        if measured_grounding is None:
          measured_grounding = construction_row.get("build_time_seconds", 0.0)
        for sampler in ("adversarial", "eligible-gap"):
          command=[sys.executable,"-m","experiments.anchored_succession.measure_construction","--worker","--mode","pairs",
                   "--size",str(size),"--backend",backend,"--time-limit-seconds",str(args.time_limit_seconds),
                   "--sampler",sampler]
          guard_seconds = 9 * (args.time_limit_seconds + float(measured_grounding)) + 45
          started=perf_counter()
          try:
            completed=subprocess.run(command,check=False,capture_output=True,text=True,timeout=guard_seconds,
                                     cwd=REPOSITORY_ROOT,preexec_fn=_limits if os.name=="posix" else None)
          except subprocess.TimeoutExpired as exc:
            partial_text = exc.stdout or ""
            if isinstance(partial_text, bytes):
              partial_text = partial_text.decode("utf-8", errors="replace")
            partial_samples = []
            for line in partial_text.splitlines():
              try:
                parsed = json.loads(line)
              except json.JSONDecodeError:
                continue
              if "partial_sample" in parsed:
                partial_samples.append(parsed["partial_sample"])
            rows.append({
                "people":size,"backend":backend,"sampler":sampler,"status":"harness_timeout",
                "wall_time_seconds":perf_counter()-started,"guard_seconds":guard_seconds,
                "measured_grounding_seconds":measured_grounding,"partial_samples":partial_samples,
                "partial_sample_count":len(partial_samples),
                "note":"Batch guard hit; streamed per-pair rows are preserved. Missing rows are unmeasured, not infeasible.",
            })
            continue
          elapsed=perf_counter()-started
          if completed.returncode == 0:
            try: row=json.loads(completed.stdout.strip().splitlines()[-1])
            except (IndexError,json.JSONDecodeError) as exc: raise RuntimeError(f"{backend} pair report size={size} sampler={sampler} returned invalid JSON") from exc
            row["harness_wall_time_seconds"]=elapsed
            row["guard_seconds"]=guard_seconds
            row["measured_grounding_seconds_for_guard"]=measured_grounding
            rows.append(row); continue
          stderr=completed.stderr[-4000:]
          if any(x in stderr for x in ("MemoryError","Cannot allocate memory","std::bad_alloc")):
            rows.append({"people":size,"backend":backend,"sampler":sampler,"status":"memory_guard_hit",
                         "wall_time_seconds":elapsed,"stderr_tail":stderr}); continue
          raise subprocess.CalledProcessError(completed.returncode,command,output=completed.stdout,stderr=stderr)
      report={"mode":"pairs","time_limit_seconds":args.time_limit_seconds,"seeds":[20261014,20261015,20261016],
              "pairs_per_seed":3,"samplers":["adversarial","eligible-gap"],
              "resource_guard":{"formula":"pairs x (per-solve time limit + measured construction/grounding time) + 45-second margin",
              "data_segment_cap_bytes_per_child":DATA_LIMIT_BYTES},
              "note":"Timeout/unknown is inconclusive, not proof of infeasibility. Batch guard hits preserve partial rows.","rows":rows}
      payload=json.dumps(report,indent=2)+"\n"
      if args.output: args.output.write_text(payload)
      else: print(payload)
      return
    if args.mode == "solve":
      for size in SIZES:
       for backend in ("cp-sat", "clingo"):
        command=[sys.executable,"-m","experiments.anchored_succession.measure_construction","--worker","--mode","solve",
                 "--size",str(size),"--backend",backend,"--time-limit-seconds",str(args.time_limit_seconds),"--seed",str(args.seed)]
        started=perf_counter()
        try:
          completed=subprocess.run(command,check=False,capture_output=True,text=True,timeout=args.time_limit_seconds + 100,
                                   cwd=REPOSITORY_ROOT,preexec_fn=_limits if os.name=="posix" else None)
        except subprocess.TimeoutExpired:
          rows.append({"people":size,"backend":backend,"encoding":"linear-successor" if backend=="cp-sat" else "aggregate-successor",
                       "status":"harness_timeout","wall_time_seconds":perf_counter()-started,"solve_invoked":True}); continue
        elapsed=perf_counter()-started
        if completed.returncode == 0:
          try: row=json.loads(completed.stdout.strip().splitlines()[-1])
          except (IndexError,json.JSONDecodeError) as exc: raise RuntimeError(f"{backend} solve size={size} worker returned invalid JSON") from exc
          row["harness_wall_time_seconds"]=elapsed; rows.append(row); continue
        stderr=completed.stderr[-4000:]
        if any(x in stderr for x in ("MemoryError","Cannot allocate memory","std::bad_alloc")):
          rows.append({"people":size,"backend":backend,"encoding":"linear-successor" if backend=="cp-sat" else "aggregate-successor",
                       "status":"memory_guard_hit","wall_time_seconds":elapsed,"stderr_tail":stderr,"solve_invoked":True}); continue
        raise subprocess.CalledProcessError(completed.returncode,command,output=completed.stdout,stderr=stderr)
      report={"mode":"solve","horizon_years":HORIZON_YEARS,"time_limit_seconds":args.time_limit_seconds,
              "seed":args.seed,"resource_guard":{"wall_clock_seconds_per_child":args.time_limit_seconds+100,
              "data_segment_cap_bytes_per_child":DATA_LIMIT_BYTES,
              "peak_rss_method":"resource.getrusage(RUSAGE_SELF).ru_maxrss; Linux KiB converted to bytes"},
              "note":"Timeouts and unknown outcomes are findings, not harness failures; only harness errors fail the job.","rows":rows}
      payload=json.dumps(report,indent=2)+"\n"
      if args.output: args.output.write_text(payload)
      else: print(payload)
      return
    encodings = ("legacy", "improved") if args.encoding == "both" else (args.encoding,)
    for size in SIZES:
      for backend in ("cp-sat","clingo"):
       for encoding in encodings:
        backend_encoding = encoding if encoding in ("linear-successor", "aggregate-successor") else (("linear-successor" if encoding == "improved" else "legacy") if backend == "cp-sat" else ("aggregate-successor" if encoding == "improved" else "legacy"))
        command=[sys.executable,"-m","experiments.anchored_succession.measure_construction","--worker",
                 "--size",str(size),"--backend",backend,"--horizon-years",str(HORIZON_YEARS),"--encoding",backend_encoding]
        started=perf_counter()
        try:
          completed=subprocess.run(command,check=False,capture_output=True,text=True,timeout=WALL_LIMIT_SECONDS,
                                   cwd=REPOSITORY_ROOT,preexec_fn=_limits if os.name=="posix" else None)
        except subprocess.TimeoutExpired:
          rows.append({"people":size,"backend":backend,"encoding":backend_encoding,"status":"wall_clock_guard_hit",
                       "wall_time_seconds":WALL_LIMIT_SECONDS,"solve_invoked":False}); continue
        elapsed=perf_counter()-started
        if completed.returncode==0:
          try: row=json.loads(completed.stdout.strip().splitlines()[-1])
          except (IndexError,json.JSONDecodeError) as exc: raise RuntimeError(f"{backend} size={size} worker returned invalid JSON") from exc
          row["wall_time_seconds"]=elapsed; rows.append(row); continue
        stderr=completed.stderr[-4000:]
        if any(x in stderr for x in ("MemoryError","Cannot allocate memory","std::bad_alloc")):
          rows.append({"people":size,"backend":backend,"encoding":backend_encoding,"status":"memory_guard_hit","wall_time_seconds":elapsed,
                       "return_code":completed.returncode,"stderr_tail":stderr,"solve_invoked":False}); continue
        raise subprocess.CalledProcessError(completed.returncode,command,output=completed.stdout,stderr=stderr)
    report={"horizon_years":HORIZON_YEARS,"anchor_count":3,"resource_guard":{
      "wall_clock_seconds_per_child":WALL_LIMIT_SECONDS,"data_segment_cap_bytes_per_child":DATA_LIMIT_BYTES,
      "peak_rss_method":"resource.getrusage(RUSAGE_SELF).ru_maxrss; Linux KiB converted to bytes"},
      "note":"Construction/grounding only; no solver search or optimization. Non-resource failures abort the job.","rows":rows}
    payload=json.dumps(report,indent=2)+"\n"
    if args.output: args.output.write_text(payload)
    else: print(payload)
if __name__=="__main__": main()
