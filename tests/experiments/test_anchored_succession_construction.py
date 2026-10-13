from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("backend,distribution", [("cp-sat", "ortools"), ("clingo", "clingo")])
def test_construction_worker_runs_as_module_for_size_12_tiny_horizon(backend, distribution):
    pytest.importorskip(distribution)
    completed = subprocess.run(
        [
            sys.executable, "-m", "experiments.anchored_succession.measure_construction",
            "--worker", "--size", "12", "--backend", backend, "--horizon-years", "31",
        ],
        cwd=ROOT, check=False, capture_output=True, text=True, timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["status"] == "measured"
    assert result["people"] == 12
    assert result["horizon_years"] == 31
    assert result["solve_invoked"] is False
    assert result["peak_rss_bytes"] > 0
    if backend == "cp-sat":
        assert result["model_variables"] > 0
        assert result["model_constraints"] > 0
        assert result["model_proto_bytes"] > 0
        assert result["constraints_by_type"]
    else:
        assert result["ground_atoms"] > 0
        assert result["ground_rules"] > 0
        assert result["program_bytes"] > 0
