"""Shared small scenarios for anchored-succession solver comparisons."""
from __future__ import annotations

from .model import Anchor, Person, Problem, Reign, Rules


def small_rules() -> Rules:
    return Rules(
        min_accession_age=16,
        min_reign=3,
        max_reign=8,
        preferred_reign=4,
        horizon_start=0,
        horizon_end=30,
        child_preference_weight=1,
        stability_weight=0,
    )


def three_person_problem(include_soft: bool = False) -> Problem:
    anchors = [Anchor("pin-A", "hard", "A", start=16, end=19)]
    if include_soft:
        anchors.append(Anchor("prefer-B", "soft", "B", start=20, tolerance=0, weight=1))
    return Problem(
        (
            Person("A", 0, 30),
            Person("B", 2, 30, ("A",)),
            Person("C", 3, 30, ("A",)),
        ),
        tuple(anchors),
        small_rules(),
        seed=20261013,
    )


def stage3_scenarios() -> dict[str, Problem]:
    rules = small_rules()
    people = (
        Person("A", 0, 30),
        Person("B", 2, 30, ("A",)),
        Person("C", 3, 30, ("A",)),
    )
    return {
        "scenario_1_hard_anchors_only": three_person_problem(),
        "scenario_2_conflicting_hard_anchors": Problem(
            (Person("A", 0, 30), Person("B", 0, 30)),
            (
                Anchor("pin-A", "hard", "A", start=16, end=19),
                Anchor("pin-B", "hard", "B", start=16, end=19),
            ),
            rules,
        ),
        "scenario_3_soft_tolerance": Problem(
            (Person("A", 0, 30),),
            (Anchor("prefer-A", "soft", "A", start=18, tolerance=2, weight=10),),
            rules,
        ),
        "scenario_4_reveal_only": Problem(
            (Person("A", 0, 30), Person("B", 0, 30, ("A",))),
            (Anchor("reveal-B", "reveal", "B", start=16, end=19),),
            rules,
        ),
        "scenario_5_repeatability": Problem(
            people,
            (
                Anchor("pin-A", "hard", "A", start=16, end=19),
                Anchor("prefer-B", "soft", "B", start=20, tolerance=0, weight=1),
            ),
            rules,
            seed=20261013,
        ),
    }


def cross_backend_problems() -> dict[str, Problem]:
    rules = small_rules()
    return {
        "hard_anchors": three_person_problem(),
        "reveal_only": stage3_scenarios()["scenario_4_reveal_only"],
        "soft_tolerance": stage3_scenarios()["scenario_3_soft_tolerance"],
        "conflicting_anchors": stage3_scenarios()["scenario_2_conflicting_hard_anchors"],
        "marked_record_reveal": Problem(
            (Person("A", 0, 30), Person("B", 0, 30, ("A",))),
            (
                Anchor("record-A", "record", "A", start=16, end=19, marked_reveal=True),
                Anchor("reveal-B", "reveal", "B", start=16, end=19),
            ),
            rules,
        ),
        "sibling_and_stability_costs": Problem(
            (
                Person("P", 0, 30),
                Person("A", 0, 30, ("P",)),
                Person("B", 0, 30, ("P",)),
            ),
            (
                Anchor("pin-A", "hard", "A", start=16, end=19),
                Anchor("pin-B-start", "hard", "B", lower=20, upper=20),
            ),
            Rules(
                min_accession_age=16, min_reign=3, max_reign=8, preferred_reign=4,
                horizon_start=0, horizon_end=30, child_preference_weight=1, stability_weight=3,
            ),
            stability_reference=(Reign("A", 20, 23),),
        ),
    }
