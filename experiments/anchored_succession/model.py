"""Solver-neutral experiment-local problem and result records."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

Status = Literal["solved", "infeasible", "unknown", "timeout"]
AnchorKind = Literal["hard", "soft", "record", "reveal"]
AnchorLayer = Literal["titular", "effective", "both"]

@dataclass(frozen=True)
class Person:
    person_id: str
    birth: int
    death: int
    parents: tuple[str, ...] = ()

@dataclass(frozen=True)
class Anchor:
    anchor_id: str
    kind: AnchorKind
    person_id: str
    start: int | None = None
    end: int | None = None
    lower: int | None = None
    upper: int | None = None
    tolerance: int = 0
    weight: int = 1
    source: str = "fixture"
    marked_reveal: bool = False
    layer: AnchorLayer | None = None

    def __post_init__(self) -> None:
        if self.layer is None:
            default_layer: AnchorLayer = {
                "hard": "both",
                "record": "titular",
                "reveal": "effective",
                "soft": "titular",
            }[self.kind]
            object.__setattr__(self, "layer", default_layer)
        if self.layer not in ("titular", "effective", "both"):
            raise ValueError("anchor layer must be titular, effective, or both")
        if self.kind == "reveal" and self.layer != "effective":
            raise ValueError("reveal anchor layer must be effective")
        if self.kind == "soft":
            if self.start is None:
                raise ValueError("soft anchor requires start")
            if self.lower is not None or self.upper is not None:
                raise ValueError("soft anchor does not support lower/upper bounds")

@dataclass(frozen=True)
class Rules:
    min_accession_age: int = 16
    min_reign: int = 3
    max_reign: int = 45
    preferred_reign: int = 20
    horizon_start: int = 0
    horizon_end: int = 300
    child_preference_weight: int = 1
    stability_weight: int = 0

@dataclass(frozen=True)
class Problem:
    people: tuple[Person, ...]
    anchors: tuple[Anchor, ...] = ()
    rules: Rules = field(default_factory=Rules)
    seed: int = 20261013
    generator_id: str = "worldloom.anchored_succession"
    generator_version: str = "1"
    stability_reference: tuple[Reign, ...] = ()

@dataclass(frozen=True)
class Reign:
    ruler: str
    start: int
    end: int

@dataclass(frozen=True)
class Solution:
    titular: tuple[Reign, ...]
    effective: tuple[Reign, ...]

@dataclass(frozen=True)
class Result:
    status: Status
    solution: Solution | None = None
    objective: int | None = None
    explanation: tuple[str, ...] = ()
    backend: str = "oracle"
    backend_version: str = "experiment-1"
    conflict_minimal: bool | None = None

def canonical_problem_data(problem: Problem) -> dict[str, object]:
    """Canonical semantic input; excludes generation metadata and stability reference."""
    return {
        "people": [
            {"id": p.person_id, "birth": p.birth, "death": p.death, "parents": sorted(p.parents)}
            for p in sorted(problem.people, key=lambda item: item.person_id)
        ],
        "anchors": [
            {
                "id": a.anchor_id, "kind": a.kind, "person": a.person_id,
                "start": a.start, "end": a.end, "lower": a.lower, "upper": a.upper,
                "tolerance": a.tolerance, "weight": a.weight, "source": a.source,
                "marked_reveal": a.marked_reveal, "layer": a.layer,
            }
            for a in sorted(problem.anchors, key=lambda item: item.anchor_id)
        ],
        "rules": {
            "min_accession_age": problem.rules.min_accession_age,
            "min_reign": problem.rules.min_reign,
            "max_reign": problem.rules.max_reign,
            "preferred_reign": problem.rules.preferred_reign,
            "horizon_start": problem.rules.horizon_start,
            "horizon_end": problem.rules.horizon_end,
            "child_preference_weight": problem.rules.child_preference_weight,
            "stability_weight": problem.rules.stability_weight,
        },
    }
