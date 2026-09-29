"""Dependency-aware simulation engine."""

from __future__ import annotations

from dataclasses import dataclass

from worldloom.core import WorldState
from worldloom.interfaces import Module, SimulationContext


@dataclass
class SimulationEngine:
    """Runs modules in deterministic dependency order."""

    modules: tuple[Module, ...]

    def _ordered_modules(self) -> tuple[Module, ...]:
        modules_by_name = {module.spec.name: module for module in self.modules}

        if len(modules_by_name) != len(self.modules):
            raise ValueError("Module names must be unique")

        for module in self.modules:
            for dependency in module.spec.dependencies:
                if dependency not in modules_by_name:
                    raise ValueError(
                        f"Module '{module.spec.name}' depends on missing module "
                        f"'{dependency}'"
                    )

        remaining = {module.spec.name: set(module.spec.dependencies) for module in self.modules}
        ordered: list[Module] = []
        input_order = [module.spec.name for module in self.modules]

        while remaining:
            ready = [name for name in input_order if name in remaining and not remaining[name]]
            if not ready:
                cycle = ", ".join(name for name in input_order if name in remaining)
                raise ValueError(f"Cyclic module dependencies detected: {cycle}")

            for name in ready:
                ordered.append(modules_by_name[name])
                del remaining[name]

            for dependencies in remaining.values():
                dependencies.difference_update(ready)

        return tuple(ordered)

    def run(self, world: WorldState, context: SimulationContext | None = None) -> None:
        context = context or SimulationContext()
        for module in self._ordered_modules():
            module.run(world, context)
