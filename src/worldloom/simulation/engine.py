"""Dependency-aware, deterministic simulation engine."""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose

from worldloom.core import WorldState
from worldloom.interfaces import Module, SimulationConfig, SimulationContext


@dataclass
class SimulationEngine:
    """Runs modules in deterministic dependency order and temporal cadence."""

    modules: tuple[Module, ...]
    config: SimulationConfig

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

    def _validate_schedule(self) -> None:
        for module in self.modules:
            interval = module.spec.temporal_interval
            if interval is None:
                continue
            if interval <= 0:
                raise ValueError(
                    f"Module '{module.spec.name}' temporal interval must be positive"
                )

    def run(
        self,
        world: WorldState,
        context: SimulationContext | None = None,
        until: float | None = None,
    ) -> None:
        """Run one scheduled simulation period."""
        context = context or SimulationContext(time=self.config.start_time)
        self._validate_schedule()
        ordered = self._ordered_modules()

        if until is None:
            for module in ordered:
                module.run(world, context)
            return

        if until < context.time:
            raise ValueError("Simulation end time cannot precede current time")

        current_time = context.time
        step = context.step
        last_run: dict[str, float] = {}

        while current_time <= until or isclose(current_time, until):
            due = [
                module
                for module in ordered
                if (
                    module.spec.name not in last_run
                    or (
                        module.spec.temporal_interval is not None
                        and (
                            current_time
                            >= last_run[module.spec.name] + module.spec.temporal_interval
                            or isclose(
                                current_time,
                                last_run[module.spec.name] + module.spec.temporal_interval,
                            )
                        )
                    )
                )            ]

            if not due:
                next_times = [
                    last_run[module.spec.name] + module.spec.temporal_interval
                    for module in ordered
                    if module.spec.temporal_interval is not None
                    and module.spec.name in last_run
                ]
                if not next_times:
                    break
                current_time = min(next_times)
                continue

            for module in due:
                previous_time = last_run.get(module.spec.name, current_time)
                module.run(
                    world,
                    SimulationContext(
                        step=step,
                        time=current_time,
                        delta=current_time - previous_time,
                        seed=context.seed,
                        metadata=context.metadata,
                    ),
                )
                last_run[module.spec.name] = current_time

            if all(module.spec.temporal_interval is None for module in ordered):
                break

            next_times = [
                last_run[module.spec.name] + module.spec.temporal_interval
                for module in ordered
                if module.spec.temporal_interval is not None
            ]
            current_time = min(next_times)
            step += 1
