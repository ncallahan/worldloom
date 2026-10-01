"""Dependency-aware, deterministic simulation engine."""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose

from worldloom.core import WorldState
from worldloom.interfaces import DataKind, Module, OutputPolicy, SimulationConfig, SimulationContext


@dataclass
class SimulationEngine:
    """Runs modules in deterministic dependency order and temporal cadence."""

    modules: tuple[Module, ...]
    config: SimulationConfig
    enforce_declared_outputs: bool = False

    def _validate_output_ownership(self) -> None:
        outputs: dict[str, list[tuple[Module, object]]] = {}

        for module in self.modules:
            for output in module.spec.outputs:
                if output.kind is DataKind.EVENT:
                    continue
                outputs.setdefault(output.name, []).append((module, output))

        refines: dict[str, str] = {}

        for name, producers in outputs.items():
            policies = {output.policy for _, output in producers}
            if len(policies) > 1:
                modules = ", ".join(module.spec.name for module, _ in producers)
                raise ValueError(
                    f"Output '{name}' has mixed ownership policies from modules: {modules}"
                )

            policy = next(iter(policies))
            if policy in {OutputPolicy.EXCLUSIVE, OutputPolicy.REFINES} and len(producers) > 1:
                modules = ", ".join(module.spec.name for module, _ in producers)
                raise ValueError(
                    f"Output '{name}' has multiple {policy.value.upper()} producers: {modules}"
                )

            if policy is OutputPolicy.OVERLAY:
                layers: set[str] = set()
                priorities: set[int] = set()
                for module, output in producers:
                    if output.layer is None:
                        raise ValueError(
                            f"OVERLAY output '{name}' from module '{module.spec.name}' "
                            "must declare a layer"
                        )
                    if isinstance(output.priority, bool) or not isinstance(output.priority, int):
                        raise ValueError(
                            f"OVERLAY output '{name}' from module '{module.spec.name}' "
                            "must declare an integer priority"
                        )
                    if output.layer in layers:
                        raise ValueError(
                            f"OVERLAY output '{name}' has duplicate layer '{output.layer}'"
                        )
                    if output.priority in priorities:
                        raise ValueError(
                            f"OVERLAY output '{name}' has duplicate priority {output.priority}"
                        )
                    layers.add(output.layer)
                    priorities.add(output.priority)

            for module, output in producers:
                if output.policy is OutputPolicy.REFINES:
                    if output.refines is None:
                        raise ValueError(
                            f"REFINES output '{name}' from module '{module.spec.name}' "
                            "must declare a parent"
                        )
                    parent_producers = outputs.get(output.refines)
                    if not parent_producers:
                        raise ValueError(
                            f"REFINES output '{name}' from module '{module.spec.name}' "
                            f"references missing parent '{output.refines}'"
                        )
                    if any(parent_module is module for parent_module, _ in parent_producers):
                        raise ValueError(
                            f"REFINES output '{name}' from module '{module.spec.name}' "
                            "cannot reference its own output"
                        )
                    refines[name] = output.refines

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(name: str) -> None:
            if name in visiting:
                raise ValueError(f"Cyclic REFINES declarations detected at '{name}'")
            if name in visited:
                return
            visiting.add(name)
            parent = refines.get(name)
            if parent is not None:
                visit(parent)
            visiting.remove(name)
            visited.add(name)

        for name in refines:
            visit(name)

    def _register_overlays(self, world: WorldState) -> None:
        """Register validated overlay layers before module execution."""
        registrations: dict[str, dict[str, int]] = {}
        for module in self.modules:
            for output in module.spec.outputs:
                if output.policy is not OutputPolicy.OVERLAY:
                    continue
                assert output.layer is not None
                assert output.priority is not None
                registrations.setdefault(output.name, {})[output.layer] = output.priority

        for name, layers in registrations.items():
            world.register_overlay(name, layers)

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

    def _run_module(self, module: Module, world: WorldState, context: SimulationContext) -> None:
        if not self.enforce_declared_outputs:
            module.run(world, context)
            return

        world._begin_module_execution(module.spec.name, module.spec.outputs)
        try:
            module.run(world, context)
        finally:
            world._end_module_execution()

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
        self._validate_output_ownership()
        self._register_overlays(world)

        if until is None:
            for module in ordered:
                self._run_module(module, world, context)
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
                )
            ]

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
                self._run_module(
                    module,
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
