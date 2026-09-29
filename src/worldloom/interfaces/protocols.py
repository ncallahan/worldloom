"""Core protocol interfaces for Worldloom."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class SimulationContext:
    """Execution metadata available to a simulation step."""

    step: int = 0
    time: float = 0.0
    seed: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModuleSpec:
    """Declarative contract describing a simulation module."""

    name: str
    version: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    spatial_resolution: str | None = None
    temporal_resolution: str | None = None
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
