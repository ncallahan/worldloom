"""Execution of declarative Worldloom runs."""

from __future__ import annotations


from worldloom.config import ModuleInstanceConfig, OutputConfig, RunConfig
from worldloom.core import WorldState
from worldloom.simulation import SimulationEngine


def _resolve_module_class(name: str) -> type:
    """Resolve a built-in module by its Worldloom contract name."""
    from worldloom.modules import get_module_class

    try:
        return get_module_class(name)
    except KeyError as exc:
        raise ValueError(f"Unknown Worldloom module: {name}") from exc


def _instantiate_module(instance: ModuleInstanceConfig):
    module_class = _resolve_module_class(instance.module)
    config = dict(instance.config)

    from_config = getattr(module_class, "from_config", None)
    if from_config is not None:
        return from_config(config)

    return module_class(**config)


def _resolve_output_adapter(name: str):
    from worldloom.adapters import get_output_adapter

    try:
        return get_output_adapter(name)
    except KeyError as exc:
        raise ValueError(f"Unknown Worldloom output adapter: {name}") from exc


def execute_run(config: RunConfig) -> WorldState:
    """Execute a configured run and produce its requested outputs."""
    modules = tuple(_instantiate_module(instance) for instance in config.modules)
    world = WorldState()
    engine = SimulationEngine(modules, config.simulation)
    engine.run(
        world,
        until=config.end_time,
        context=None if config.seed is None else _seeded_context(config.seed, config.simulation),
    )

    for output in config.outputs:
        _write_output(world, output)

    return world


def _seeded_context(seed: int, simulation):
    from worldloom.interfaces import SimulationContext

    return SimulationContext(time=simulation.start_time, seed=seed)


def _write_output(world: WorldState, output: OutputConfig) -> None:
    adapter = _resolve_output_adapter(output.adapter)
    adapter(world, output.path, output.config)
