"""Emit CP-SAT model-proto sizes for the five small experiment scenarios."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from importlib.metadata import version as distribution_version

from experiments.anchored_succession.cp_sat import _build_model
from experiments.anchored_succession.scenarios import stage3_scenarios



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = {}
    for name, problem in stage3_scenarios().items():
        built = _build_model(problem)
        rows[name] = {
            "variables": built["model_variables"],
            "constraints": built["model_constraints"],
            "count_source": "CpModel.Proto().variables and CpModel.Proto().constraints",
        }
    args.output.write_text(json.dumps({
        "backend": "ortools-cp-sat",
        "version": distribution_version("ortools"),
        "scenarios": rows,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
