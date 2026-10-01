"""Core protocol interfaces for Worldloom."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class SimulationContext:
    """Execution metadata available to a simulation step."""

    step: int = 0
    time: float = 0.0
    delta: float = 0.0
    seed: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration for numeric simulation time."""

    time_unit: str
    start_time: float = 0.0


class DataKind(str, Enum):
    """Semantic category of data flowing through the simulation."""

    STATE = "state"
    OBSERVATION = "observation"
    EVENT = "event"


@dataclass(frozen=True)
class InputSpec:
    """Declarative description of one module input."""

    name: str
    kind: DataKind


@dataclass(frozen=True)
class OutputSpec:
    """Provisional declarative description of one module output."""

    name: str
    kind: DataKind
    policy: "OutputPolicy" = field(default_factory=lambda: OutputPolicy.EXCLUSIVE)
    refines: str | None = None
    layer: str | None = None
    priority: int | None = None


class OutputPolicy(str, Enum):
    """Provisional ownership policy for a module output."""

    EXCLUSIVE = "exclusive"
    REFINES = "refines"
    OVERLAY = "overlay"


@dataclass(frozen=True)
class ModuleSpec:
    """Declarative contract describing a simulation module."""

    name: str
    version: str
    inputs: tuple[InputSpec, ...] = ()
    outputs: tuple[OutputSpec, ...] = ()
    spatial_resolution: str | None = None
    temporal_interval: float | None = None
    dependencies: tuple[str, ...] = ()
    uncertainty: str | None = None


class Module(Protocol):
    """A simulation component with a declarative contract."""

    spec: ModuleSpec

    def run(self, world: World, context: SimulationContext) -> None: ...


class World(Protocol):
    """Authoritative state of a simulated world."""

    def initialize(self, context: SimulationContext) -> None: ...

    def snapshot(self) -> Any: ...

    def restore(self, snapshot: Any) -> None: ...


class Dynamics(Protocol):
    """Defines how a world advances."""

    def step(self, world: World, context: SimulationContext) -> None: ...


class Observer(Protocol):
    """Extracts derived measurements from a world."""

    def observe(self, world: World, context: SimulationContext) -> Mapping[str, Any]: ...
