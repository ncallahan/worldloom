"""Minimal sequential simulation engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from worldloom.core import WorldState
from worldloom.interfaces import SimulationContext


class RunnableModule(Protocol):
    name: str

    def run(self, world: WorldState, context: SimulationContext) -> None: ...


@dataclass
class SimulationEngine:
    """Runs a declared module pipeline against canonical world state."""

    modules: tuple[RunnableModule, ...]

    def run(self, world: WorldState, context: SimulationContext | None = None) -> None:
        context = context or SimulationContext()
        for module in self.modules:
            module.run(world, context)
