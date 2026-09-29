"""Small end-to-end modules used to exercise Worldloom's architecture.

These are intentionally toy models. They exist to validate state exchange,
persistent facts, events, and provenance before specialist models are added.
"""

from __future__ import annotations

from math import hypot

from worldloom.core import Event, Provenance, WorldState
from worldloom.interfaces import DataKind, InputSpec, ModuleSpec, OutputSpec, SimulationContext


class TerrainModule:
    spec = ModuleSpec(
        name="prototype.terrain",
        version="0.1",
        outputs=(OutputSpec("field:terrain.elevation", DataKind.STATE),),
        spatial_resolution="10x10 cells",
        temporal_interval=None,
        uncertainty="deterministic",
    )

    def run(self, world: WorldState, context: SimulationContext) -> None:
        size = 10
        elevation = [
            [float((x - 4.5) ** 2 + (y - 4.5) ** 2) for x in range(size)]
            for y in range(size)
        ]
        world.set_field(
            "terrain.elevation",
            elevation,
            Provenance(self.spec.name, configuration={"size": size}, time=context.time),
        )


class HydrologyModule:
    spec = ModuleSpec(
        name="prototype.hydrology",
        version="0.1",
        inputs=(InputSpec("field:terrain.elevation", DataKind.STATE),),
        outputs=(OutputSpec("field:hydrology.water", DataKind.STATE),),
        spatial_resolution="10x10 cells",
        temporal_interval=1.0,
        dependencies=("prototype.terrain",),
        uncertainty="deterministic",
    )

    def run(self, world: WorldState, context: SimulationContext) -> None:
        elevation = world.fields["terrain.elevation"]
        water = [[value <= 5.0 for value in row] for row in elevation]
        world.set_field(
            "hydrology.water",
            water,
            Provenance(self.spec.name, inputs=("field:terrain.elevation",), time=context.time),
        )


class SettlementSuitabilityModule:
    spec = ModuleSpec(
        name="prototype.settlement_suitability",
        version="0.1",
        inputs=(
            InputSpec("field:terrain.elevation", DataKind.STATE),
            InputSpec("field:hydrology.water", DataKind.STATE),
        ),
        outputs=(OutputSpec("observation:settlement.suitability", DataKind.OBSERVATION),),
        spatial_resolution="10x10 cells",
        temporal_interval=1.0,
        dependencies=("prototype.terrain", "prototype.hydrology"),
        uncertainty="deterministic",
    )

    def run(self, world: WorldState, context: SimulationContext) -> None:
        elevation = world.fields["terrain.elevation"]
        water = world.fields["hydrology.water"]
        size = len(elevation)

        scores: dict[tuple[int, int], float] = {}
        water_cells = [
            (x, y)
            for y in range(size)
            for x in range(size)
            if water[y][x]
        ]

        for y in range(size):
            for x in range(size):
                if water[y][x]:
                    continue
                distance = min(hypot(x - wx, y - wy) for wx, wy in water_cells)
                elevation_penalty = abs(elevation[y][x] - 4.0) / 10.0
                scores[(x, y)] = max(0.0, 1.0 - distance / 5.0 - elevation_penalty)

        world.set_observation(
            "settlement.suitability",
            scores,
            Provenance(
                self.spec.name,
                inputs=("field:terrain.elevation", "field:hydrology.water"),
                time=context.time,
            ),
        )


class SettlementResolutionModule:
    spec = ModuleSpec(
        name="prototype.settlement_resolution",
        version="0.1",
        inputs=(InputSpec("observation:settlement.suitability", DataKind.OBSERVATION),),
        outputs=(
            OutputSpec("entity:settlement", DataKind.STATE),
            OutputSpec("event:settlement.founded", DataKind.EVENT),
        ),
        spatial_resolution="entity location",
        temporal_interval=10.0,
        dependencies=("prototype.settlement_suitability",),
        uncertainty="resolves selection to persistent fact",
    )

    def run(self, world: WorldState, context: SimulationContext) -> None:
        scores = world.observations["settlement.suitability"]
        if not scores:
            return

        location, score = max(scores.items(), key=lambda item: item[1])
        entity_id = "settlement:001"

        if entity_id not in world.entities:
            world.add_entity(
                entity_id,
                {
                    "type": "settlement",
                    "location": location,
                    "population": 100,
                    "suitability": score,
                },
                Provenance(
                    self.spec.name,
                    inputs=("observation:settlement.suitability",),
                    configuration={"resolution": "highest-suitability"},
                    time=context.time,
                ),
            )
            world.record_event(
                Event(
                    kind="settlement.founded",
                    time=context.time,
                    data={"entity_id": entity_id, "location": location},
                )
            )
