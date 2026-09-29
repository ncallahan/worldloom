from worldloom.core import WorldState
from worldloom.interfaces import SimulationContext
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
        )
    )


def test_pipeline_exchanges_state_through_canonical_world():
    world = WorldState()

    make_engine().run(world)

    assert "terrain.elevation" in world.fields
    assert "hydrology.water" in world.fields
    assert "settlement.suitability" in world.fields


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
