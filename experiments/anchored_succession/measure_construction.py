"""Guarded construction-only size measurements; never invokes either solver."""
from __future__ import annotations
import argparse, json, os, resource, subprocess, sys, tempfile
from pathlib import Path
from time import perf_counter
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SIZES = (12, 30, 100)
HORIZON_YEARS = 300
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

def _worker(size: int, backend: str, horizon_years: int) -> dict[str, object]:
    problem = _problem(size, horizon_years)
    started = perf_counter()
    if backend == "cp-sat":
        from experiments.anchored_succession.cp_sat import _build_model
        built = _build_model(problem); elapsed = perf_counter() - started
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
        return {"people":size,"horizon_years":horizon_years,"backend":backend,"status":"measured",
          "build_time_seconds":elapsed,"model_variables":len(proto.variables),
          "model_constraints":len(proto.constraints),"constraints_by_type":dict(sorted(breakdown.items())),
          "model_proto_bytes":proto_bytes,
          "succession_constraint_count_analytic":2*(years-1)*_non_kin_ordered_pairs(problem),
          "succession_constraint_count_basis":"analytic: layers x (years-1) x ordered non-kin pairs",
          "peak_rss_bytes":_peak_rss_bytes(),"solve_invoked":False}
    import clingo
    from experiments.anchored_succession.clingo_backend import _GroundingCounter, _program
    program,_ = _program(problem); program_bytes=len(program.encode("utf-8")); ground_started=perf_counter()
    counter=_GroundingCounter(); control=clingo.Control(["--warn=none"])
    control.register_observer(counter,replace=True); control.add("base",[],program); control.ground([("base",[])])
    years=problem.rules.horizon_end-problem.rules.horizon_start+1
    return {"people":size,"horizon_years":horizon_years,"backend":backend,"status":"measured",
      "program_build_time_seconds":ground_started-started,"grounding_time_seconds":perf_counter()-ground_started,
      "ground_atoms":len(control.symbolic_atoms),"ground_rules":counter.rules,"program_bytes":program_bytes,
      "succession_constraint_count_analytic":2*(years-1)*_non_kin_ordered_pairs(problem),
      "succession_constraint_count_basis":"analytic: layers x (years-1) x ordered non-kin pairs",
      "peak_rss_bytes":_peak_rss_bytes(),"solve_invoked":False}

def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path); parser.add_argument("--worker",action="store_true")
    parser.add_argument("--size",type=int,choices=SIZES); parser.add_argument("--backend",choices=("cp-sat","clingo"))
    parser.add_argument("--horizon-years",type=int,default=HORIZON_YEARS); args=parser.parse_args()
    if args.worker:
        if args.size is None or args.backend is None: parser.error("--worker requires --size and --backend")
        print(json.dumps(_worker(args.size,args.backend,args.horizon_years))); return
    rows=[]
    for size in SIZES:
      for backend in ("cp-sat","clingo"):
        command=[sys.executable,"-m","experiments.anchored_succession.measure_construction","--worker",
                 "--size",str(size),"--backend",backend,"--horizon-years",str(HORIZON_YEARS)]
        started=perf_counter()
        try:
          completed=subprocess.run(command,check=False,capture_output=True,text=True,timeout=WALL_LIMIT_SECONDS,
                                   cwd=REPOSITORY_ROOT,preexec_fn=_limits if os.name=="posix" else None)
        except subprocess.TimeoutExpired:
          rows.append({"people":size,"backend":backend,"status":"wall_clock_guard_hit",
                       "wall_time_seconds":WALL_LIMIT_SECONDS,"solve_invoked":False}); continue
        elapsed=perf_counter()-started
        if completed.returncode==0:
          try: row=json.loads(completed.stdout.strip().splitlines()[-1])
          except (IndexError,json.JSONDecodeError) as exc: raise RuntimeError(f"{backend} size={size} worker returned invalid JSON") from exc
          row["wall_time_seconds"]=elapsed; rows.append(row); continue
        stderr=completed.stderr[-4000:]
        if any(x in stderr for x in ("MemoryError","Cannot allocate memory","std::bad_alloc")):
          rows.append({"people":size,"backend":backend,"status":"memory_guard_hit","wall_time_seconds":elapsed,
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
