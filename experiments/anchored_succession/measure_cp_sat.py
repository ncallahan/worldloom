"""Emit CP-SAT model-proto sizes for the five small experiment scenarios."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.anchored_succession.cp_sat import _build_model
from experiments.anchored_succession.model import Anchor, Person, Problem, Rules


def rules() -> Rules:
    return Rules(
        min_accession_age=16, min_reign=3, max_reign=8, preferred_reign=4,
        horizon_start=0, horizon_end=30, child_preference_weight=1, stability_weight=0,
    )


def scenarios() -> dict[str, Problem]:
    people = (Person("A", 0, 30), Person("B", 2, 30, ("A",)), Person("C", 3, 30, ("A",)))
    return {
        "scenario_1_hard_anchors_only": Problem(
            people, (Anchor("pin-A", "hard", "A", start=16, end=19),), rules(), seed=20261013
        ),
        "scenario_2_conflicting_hard_anchors": Problem(
            (Person("A", 0, 30), Person("B", 0, 30)),
            (Anchor("pin-A", "hard", "A", start=16, end=19),
             Anchor("pin-B", "hard", "B", start=16, end=19)),
            rules(),
        ),
        "scenario_3_soft_tolerance": Problem(
            (Person("A", 0, 30),),
            (Anchor("prefer-A", "soft", "A", start=18, tolerance=2, weight=10),),
            rules(),
        ),
        "scenario_4_reveal_only": Problem(
            (Person("A", 0, 30), Person("B", 0, 30, ("A",))),
            (Anchor("reveal-B", "reveal", "B", start=16, end=19),),
            rules(),
        ),
        "scenario_5_repeatability": Problem(
            people,
            (Anchor("pin-A", "hard", "A", start=16, end=19),
             Anchor("prefer-B", "soft", "B", start=20, tolerance=0, weight=1)),
            rules(), seed=20261013,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = {}
    for name, problem in scenarios().items():
        built = _build_model(problem)
        rows[name] = {
            "variables": built["model_variables"],
            "constraints": built["model_constraints"],
            "count_source": "CpModel.Proto().variables and CpModel.Proto().constraints",
        }
    args.output.write_text(json.dumps({
        "backend": "ortools-cp-sat",
        "version": "9.15.6755",
        "scenarios": rows,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
