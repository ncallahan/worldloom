"""Declarative simulation run configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from worldloom.interfaces import SimulationConfig


@dataclass(frozen=True)
class ModuleInstanceConfig:
    """Configuration for one participating module instance."""

    module: str
    config: Mapping[str, Any]


@dataclass(frozen=True)
class OutputConfig:
    """Configuration for one requested output projection."""

    adapter: str
    path: str
    config: Mapping[str, Any]


@dataclass(frozen=True)
class RunConfig:
    """Complete declarative configuration for one simulation run."""

    simulation: SimulationConfig
    end_time: float | None
    modules: tuple[ModuleInstanceConfig, ...]
    outputs: tuple[OutputConfig, ...] = ()
    seed: int | None = None


def load_run_config(path: str | Path) -> RunConfig:
    """Load a JSON run configuration.

    Relative output paths are interpreted relative to the configuration file.
    """
    config_path = Path(path).resolve()
    with config_path.open("r", encoding="utf-8") as handle:
        document = json.load(handle)

    simulation_data = document.get("simulation", {})
    simulation = SimulationConfig(
        time_unit=simulation_data["time_unit"],
        start_time=float(simulation_data.get("start", simulation_data.get("start_time", 0.0))),
    )

    modules = tuple(
        ModuleInstanceConfig(
            module=item["module"],
            config=item.get("config", {}),
        )
        for item in document["modules"]
    )

    outputs = tuple(
        OutputConfig(
            adapter=item["adapter"],
            path=str((config_path.parent / item["path"]).resolve()),
            config={key: value for key, value in item.items() if key not in {"adapter", "path"}},
        )
        for item in document.get("outputs", [])
    )

    execution = document.get("execution", {})
    seed = execution.get("seed")

    return RunConfig(
        simulation=simulation,
        end_time=(
            float(simulation_data["end"])
            if "end" in simulation_data
            else (
                float(simulation_data["end_time"])
                if "end_time" in simulation_data
                else None
            )
        ),
        modules=modules,
        outputs=outputs,
        seed=seed,
    )
