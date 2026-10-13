"""Guarded construction-only size measurements; never invokes either solver."""
from __future__ import annotations

import argparse
import json
import os
import resource
import subprocess
import sys
from pathlib import Path
from time import perf_counter


def _limits() -> None:
    # Each isolated build is capped at 2 GiB virtual address space and 60 CPU seconds.
    limit = 2 * 1024 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))


def _problem(size: int):
    from experiments.anchored_succession.model import Anchor, Person, Problem, Rules

    people = tuple(
        Person(f"P{i:03d}", max(0, i * 2), 299, (() if i == 0 else (f"P{i-1:03d}",)))
        for i in range(size)
    )
    # Same small, fixed anchor set for each pool size; these are construction inputs,
    # not a claim that the full problem is feasible.
    anchors = tuple(
        Anchor(f"scale-pin-{i}", "hard", f"P{i:03d}", start=year, end=year + 3)
        for i, year in enumerate((50, 150, 250))
    )
    rules = Rules(
        min_accession_age=16, min_reign=3, max_reign=45, preferred_reign=20,
        horizon_start=0, horizon_end=299, child_preference_weight=1, stability_weight=0,
    )
    return Problem(people, anchors, rules, seed=20261013)


def _worker(size: int, backend: str) -> dict[str, object]:
    problem = _problem(size)
    started = perf_counter()
    if backend == "cp-sat":
        from experiments.anchored_succession.cp_sat import _build_model

        built = _build_model(problem)
        proto = built["model"].Proto()
        return {
            "people": size, "backend": backend, "status": "measured",
            "build_time_seconds": perf_counter() - started,
            "model_variables": len(proto.variables),
            "model_constraints": len(proto.constraints),
            "model_proto_bytes": len(proto.SerializeToString()),
            "solve_invoked": False,
        }

    import clingo
    from experiments.anchored_succession.clingo_backend import _GroundingCounter, _program

    program, _ = _program(problem)
    counter = _GroundingCounter()
    control = clingo.Control(["--warn=none"])
    control.register_observer(counter, replace=True)
    control.add("base", [], program)
    control.ground([("base", [])])
    return {
        "people": size, "backend": backend, "status": "measured",
        "build_ground_time_seconds": perf_counter() - started,
        "ground_atoms": len(control.symbolic_atoms),
        "ground_rules": counter.rules,
        "program_bytes": len(program.encode("utf-8")),
        "solve_invoked": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--size", type=int, choices=(12, 30, 100))
    parser.add_argument("--backend", choices=("cp-sat", "clingo"))
    args = parser.parse_args()
    if args.worker:
        if args.size is None or args.backend is None:
            parser.error("--worker requires --size and --backend")
        print(json.dumps(_worker(args.size, args.backend)))
        return

    rows = []
    for size in (12, 30, 100):
        for backend in ("cp-sat", "clingo"):
            command = [sys.executable, str(Path(__file__).resolve()), "--worker",
                       "--size", str(size), "--backend", backend]
            started = perf_counter()
            try:
                completed = subprocess.run(
                    command, check=False, capture_output=True, text=True, timeout=70,
                    preexec_fn=_limits if os.name == "posix" else None,
                )
                elapsed = perf_counter() - started
                if completed.returncode == 0:
                    row = json.loads(completed.stdout.strip().splitlines()[-1])
                    row["wall_time_seconds"] = elapsed
                    rows.append(row)
                else:
                    rows.append({
                        "people": size, "backend": backend, "status": "build_failed_or_resource_guard",
                        "wall_time_seconds": elapsed, "return_code": completed.returncode,
                        "stderr_tail": completed.stderr[-2000:], "solve_invoked": False,
                    })
            except subprocess.TimeoutExpired:
                rows.append({
                    "people": size, "backend": backend, "status": "time_guard_exceeded",
                    "wall_time_seconds": 70, "solve_invoked": False,
                })
    report = {
        "horizon_years": 300,
        "anchor_count": 3,
        "resource_guard": {"virtual_memory_bytes": 2147483648, "cpu_seconds": 60, "wall_seconds": 70},
        "note": "Construction/grounding only. No solver search or optimization was invoked.",
        "rows": rows,
    }
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload)
    else:
        print(payload)


if __name__ == "__main__":
    main()
