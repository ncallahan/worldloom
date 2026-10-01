from worldloom.core import Provenance, WorldState
from worldloom.interfaces import SimulationConfig, SimulationContext
from worldloom.modules import (
    HydrologyModule,
    SettlementResolutionModule,
    SettlementSuitabilityModule,
    TerrainModule,
)
from worldloom.simulation import SimulationEngine


def make_engine() -> SimulationEngine:
    return SimulationEngine(
        (
            TerrainModule(),
            HydrologyModule(),
            SettlementSuitabilityModule(),
            SettlementResolutionModule(),
        ),
        SimulationConfig(time_unit="days"),
    )


def test_pipeline_exchanges_state_through_canonical_world():
    world = WorldState()

    make_engine().run(world)

    assert "terrain.elevation" in world.fields
    assert "hydrology.water" in world.fields
    assert "settlement.suitability" in world.observations
    assert "settlement.suitability" not in world.fields


def test_downstream_module_materially_uses_upstream_outputs():
    world = WorldState()

    make_engine().run(world, SimulationContext(time=12))

    scores = world.observations["settlement.suitability"]
    settlement = world.entities["settlement:001"]

    assert scores
    best_location, best_score = max(scores.items(), key=lambda item: item[1])
    assert settlement["location"] == best_location
    assert settlement["suitability"] == best_score


def test_resolution_creates_persistent_fact_and_event():
    world = WorldState()

    make_engine().run(world, SimulationContext(time=1847))

    settlement = world.entities["settlement:001"]
    assert settlement["type"] == "settlement"
    assert settlement["population"] == 100
    assert world.events[0].kind == "settlement.founded"
    assert world.events[0].time == 1847


def test_resolved_fact_is_not_resampled_on_repeat_run():
    world = WorldState()
    engine = make_engine()

    engine.run(world, SimulationContext(time=1))
    first = world.entities["settlement:001"].copy()
    first_event_count = len(world.events)

    engine.run(world, SimulationContext(time=2))

    assert world.entities["settlement:001"] == first
    assert len(world.events) == first_event_count


def test_provenance_survives_the_vertical_slice():
    world = WorldState()

    make_engine().run(world, SimulationContext(time=12))

    assert world.provenance["field:terrain.elevation"].producer == "prototype.terrain"
    assert world.provenance["entity:settlement:001"].producer == "prototype.settlement_resolution"
    assert world.provenance["entity:settlement:001"].time == 12


def test_pipeline_runs_in_dependency_order_when_modules_are_reversed():
    world = WorldState()
    engine = SimulationEngine(
        (
            SettlementResolutionModule(),
            SettlementSuitabilityModule(),
            HydrologyModule(),
            TerrainModule(),
        ),
        SimulationConfig(time_unit="days"),
    )
    engine.run(world)
    assert "settlement:001" in world.entities
    assert len(world.events) == 1


def test_missing_module_dependency_is_rejected():
    world = WorldState()
    engine = SimulationEngine((HydrologyModule(),), SimulationConfig(time_unit="days"))
    try:
        engine.run(world)
    except ValueError as exc:
        assert "depends on missing module 'prototype.terrain'" in str(exc)
    else:
        raise AssertionError("Expected missing dependency error")


def test_cyclic_module_dependencies_are_rejected():
    from dataclasses import replace

    class ModuleA:
        spec = replace(TerrainModule.spec, name="test.a", dependencies=("test.b",))

        def run(self, world, context):
            pass

    class ModuleB:
        spec = replace(TerrainModule.spec, name="test.b", dependencies=("test.a",))

        def run(self, world, context):
            pass

    try:
        SimulationEngine((ModuleA(), ModuleB()), SimulationConfig(time_unit="days")).run(WorldState())
    except ValueError as exc:
        assert "Cyclic module dependencies detected" in str(exc)
    else:
        raise AssertionError("Expected dependency cycle error")


def test_derived_observation_has_distinct_provenance_namespace():
    world = WorldState()

    make_engine().run(world, SimulationContext(time=12))

    assert "observation:settlement.suitability" in world.provenance
    assert "field:settlement.suitability" not in world.provenance


def test_observation_is_not_promoted_without_explicit_resolution():
    world = WorldState()

    make_engine().run(world)

    assert "settlement.suitability" in world.observations
    assert "settlement.suitability" not in world.fields
    assert "settlement:001" in world.entities


def test_upstream_change_propagates_through_the_full_pipeline():
    from dataclasses import replace

    class InjectedTerrainModule:
        spec = replace(TerrainModule.spec, name="prototype.terrain")

        def __init__(self, elevation):
            self.elevation = elevation

        def run(self, world, context):
            world.set_field(
                "terrain.elevation",
                self.elevation,
                Provenance(
                    self.spec.name,
                    configuration={"injected": True},
                    time=context.time,
                ),
            )

    def run_with_terrain(elevation):
        world = WorldState()
        engine = SimulationEngine(
            (
                InjectedTerrainModule(elevation),
                HydrologyModule(),
                SettlementSuitabilityModule(),
                SettlementResolutionModule(),
            ),
            SimulationConfig(time_unit="days"),
        )
        engine.run(world, SimulationContext(time=12))
        return world

    terrain_a = [[9.0] * 10 for _ in range(10)]
    terrain_a[5][5] = 4.0
    terrain_b = [[9.0] * 10 for _ in range(10)]
    terrain_b[2][2] = 4.0

    world_a = run_with_terrain(terrain_a)
    world_b = run_with_terrain(terrain_b)

    assert world_a.fields["hydrology.water"] != world_b.fields["hydrology.water"]
    assert world_a.observations["settlement.suitability"] != world_b.observations[
        "settlement.suitability"
    ]
    assert world_a.entities["settlement:001"]["location"] != world_b.entities[
        "settlement:001"
    ]["location"]
    assert world_a.events[0].data["location"] != world_b.events[0].data["location"]
