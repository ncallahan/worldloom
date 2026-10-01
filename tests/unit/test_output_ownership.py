"""Unit tests for provisional canonical output ownership and enforcement."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from worldloom.adapters.raster import RasterTerrainAdapter
from worldloom.core import Event, Provenance, WorldState
from worldloom.interfaces import SimulationContext
from worldloom.modules import (
    HydrologyModule,
    SettlementResolutionModule,
    SettlementSuitabilityModule,
    TerrainModule,
)
from worldloom.interfaces import (
    DataKind,
    ModuleSpec,
    OutputPolicy,
    OutputSpec,
    SimulationConfig,
)
from worldloom.simulation import SimulationEngine


class OwnershipModule:
    def __init__(self, name, outputs, log=None):
        self.log = log if log is not None else []
        self.spec = ModuleSpec(
            name=name,
            version="ownership-experiment",
            outputs=outputs,
        )

    def run(self, world, context):
        self.log.append(self.spec.name)


def output(name, policy=OutputPolicy.EXCLUSIVE, **kwargs):
    return OutputSpec(name, DataKind.STATE, policy=policy, **kwargs)


def engine(*modules):
    return SimulationEngine(modules, SimulationConfig(time_unit="days"))


def test_duplicate_exclusive_producers_are_rejected_before_execution():
    log = []
    first = OwnershipModule("producer.a", (output("field:shared.value"),), log)
    second = OwnershipModule("producer.b", (output("field:shared.value"),), log)

    try:
        engine(first, second).run(WorldState())
    except ValueError as exc:
        message = str(exc)
        assert "field:shared.value" in message
        assert "producer.a" in message
        assert "producer.b" in message
    else:
        raise AssertionError("Expected duplicate EXCLUSIVE producer error")

    assert log == []


def test_duplicate_exclusive_producers_are_also_rejected_for_scheduled_runs():
    first = OwnershipModule("producer.a", (output("field:shared.value"),))
    second = OwnershipModule("producer.b", (output("field:shared.value"),))

    try:
        engine(first, second).run(WorldState(), until=1.0)
    except ValueError as exc:
        assert "field:shared.value" in str(exc)
    else:
        raise AssertionError("Expected duplicate EXCLUSIVE producer error")


def test_single_exclusive_producer_is_accepted():
    log = []
    module = OwnershipModule("producer", (output("field:shared.value"),), log)

    engine(module).run(WorldState())

    assert log == ["producer"]


def test_refines_requires_parent_from_another_module_in_same_run():
    refiner = OwnershipModule(
        "refiner",
        (output("field:fine.value", OutputPolicy.REFINES, refines="field:coarse.value"),),
    )
    try:
        engine(refiner).run(WorldState())
    except ValueError as exc:
        assert "field:fine.value" in str(exc)
        assert "field:coarse.value" in str(exc)
    else:
        raise AssertionError("Expected missing REFINES parent error")

    self_refiner = OwnershipModule(
        "refiner",
        (output("field:coarse.value", OutputPolicy.REFINES, refines="field:coarse.value"),),
    )
    try:
        engine(self_refiner).run(WorldState())
    except ValueError as exc:
        message = str(exc)
        assert "refiner" in message
        assert "field:coarse.value" in message
        assert "cannot reference its own output" in message
    else:
        raise AssertionError("Expected self-referential REFINES error")


def test_refines_cycles_are_rejected():
    first = OwnershipModule(
        "first",
        (output("field:a.value", OutputPolicy.REFINES, refines="field:b.value"),),
    )
    second = OwnershipModule(
        "second",
        (output("field:b.value", OutputPolicy.REFINES, refines="field:a.value"),),
    )

    try:
        engine(first, second).run(WorldState())
    except ValueError as exc:
        assert "Cyclic REFINES" in str(exc)
        assert "field:a.value" in str(exc)
    else:
        raise AssertionError("Expected REFINES cycle error")


def test_valid_refines_declaration_does_not_order_execution():
    log = []
    parent = OwnershipModule("parent", (output("field:coarse.value"),), log)
    refiner = OwnershipModule(
        "refiner",
        (output("field:fine.value", OutputPolicy.REFINES, refines="field:coarse.value"),),
        log,
    )

    engine(refiner, parent).run(WorldState())
    assert log == ["refiner", "parent"]


def test_overlay_producers_require_distinct_layers_and_integer_priorities():
    first = OwnershipModule(
        "first",
        (output("field:shared.value", OutputPolicy.OVERLAY, layer="first", priority=1),),
    )
    second = OwnershipModule(
        "second",
        (output("field:shared.value", OutputPolicy.OVERLAY, layer="second", priority=2),),
    )

    engine(first, second).run(WorldState())

    duplicate_priority = OwnershipModule(
        "third",
        (output("field:shared.value", OutputPolicy.OVERLAY, layer="third", priority=1),),
    )
    try:
        engine(first, duplicate_priority).run(WorldState())
    except ValueError as exc:
        assert "priority" in str(exc)
    else:
        raise AssertionError("Expected duplicate overlay priority error")

    duplicate_layer = OwnershipModule(
        "third",
        (output("field:shared.value", OutputPolicy.OVERLAY, layer="first", priority=3),),
    )
    try:
        engine(first, duplicate_layer).run(WorldState())
    except ValueError as exc:
        assert "layer" in str(exc)
    else:
        raise AssertionError("Expected duplicate overlay layer error")

    non_integer = OwnershipModule(
        "third",
        (output("field:shared.value", OutputPolicy.OVERLAY, layer="third", priority="3"),),
    )
    try:
        engine(first, non_integer).run(WorldState())
    except ValueError as exc:
        assert "priority" in str(exc)
    else:
        raise AssertionError("Expected non-integer overlay priority error")


def test_mixed_ownership_policies_are_rejected():
    exclusive = OwnershipModule("exclusive", (output("field:shared.value"),))
    overlay = OwnershipModule(
        "overlay",
        (output("field:shared.value", OutputPolicy.OVERLAY, layer="overlay", priority=1),),
    )

    try:
        engine(exclusive, overlay).run(WorldState())
    except ValueError as exc:
        message = str(exc)
        assert "mixed ownership policies" in message
        assert "exclusive" in message
        assert "overlay" in message
    else:
        raise AssertionError("Expected mixed ownership policy error")


def test_event_outputs_are_exempt_from_ownership_collisions():
    events = []

    class EventWritingModule:
        def __init__(self, name):
            self.spec = ModuleSpec(
                name=name,
                version="ownership-events",
                outputs=(OutputSpec("event:shared", DataKind.EVENT),),
            )

        def run(self, world, context):
            world.record_event(Event("shared", context.time, {"producer": self.spec.name}))
            events.append(self.spec.name)

    first = EventWritingModule("first")
    second = EventWritingModule("second")
    world = WorldState()

    engine(first, second).run(world)

    assert events == ["first", "second"]
    assert [event.data["producer"] for event in world.events] == ["first", "second"]


class WritingModule:
    def __init__(self, outputs, action):
        self.spec = ModuleSpec(
            name="test.writer",
            version="ownership-guard",
            outputs=outputs,
        )
        self.action = action

    def run(self, world, context):
        self.action(world)


def run_guarded(module):
    SimulationEngine(
        (module,),
        SimulationConfig(time_unit="days"),
        enforce_declared_outputs=True,
    ).run(WorldState())


def test_guard_rejects_undeclared_field_write():
    module = WritingModule(
        (),
        lambda world: world.set_field("field.not_declared", 1),
    )

    with pytest.raises(ValueError, match="undeclared field output 'field.not_declared'"):
        run_guarded(module)


def test_guard_rejects_undeclared_observation_write():
    module = WritingModule(
        (),
        lambda world: world.set_observation("observation.not_declared", 1),
    )

    with pytest.raises(ValueError, match="undeclared observation output 'observation.not_declared'"):
        run_guarded(module)


def test_guard_rejects_undeclared_event_write():
    module = WritingModule(
        (),
        lambda world: world.record_event(Event("event.not_declared", 0.0, {})),
    )

    with pytest.raises(ValueError, match="undeclared event output 'event.not_declared'"):
        run_guarded(module)


def test_guard_allows_declared_field_observation_and_event_writes():
    module = WritingModule(
        (
            OutputSpec("field:allowed", DataKind.STATE),
            OutputSpec("observation:allowed", DataKind.OBSERVATION),
            OutputSpec("event:allowed", DataKind.EVENT),
        ),
        lambda world: (
            world.set_field("allowed", 1),
            world.set_observation("allowed", 2),
            world.record_event(Event("allowed", 3.0, {})),
        ),
    )

    world = WorldState()
    SimulationEngine(
        (module,),
        SimulationConfig(time_unit="days"),
        enforce_declared_outputs=True,
    ).run(world)

    assert world.fields["allowed"] == 1
    assert world.observations["allowed"] == 2
    assert world.events[0].kind == "allowed"


def test_guard_uses_entity_type_prefix_matching():
    module = WritingModule(
        (OutputSpec("entity:settlement", DataKind.STATE),),
        lambda world: world.add_entity("settlement:001", {"type": "settlement"}),
    )

    world = WorldState()
    SimulationEngine(
        (module,),
        SimulationConfig(time_unit="days"),
        enforce_declared_outputs=True,
    ).run(world)

    assert world.entities["settlement:001"]["type"] == "settlement"


def test_guard_rejects_an_unrelated_entity_id():
    module = WritingModule(
        (OutputSpec("entity:settlement", DataKind.STATE),),
        lambda world: world.add_entity("city:001", {"type": "city"}),
    )

    with pytest.raises(ValueError, match="undeclared entity output 'city:001'"):
        run_guarded(module)


def test_guard_off_preserves_existing_unrestricted_writes():
    module = WritingModule(
        (),
        lambda world: world.set_field("anything", 1),
    )

    world = WorldState()
    SimulationEngine(
        (module,),
        SimulationConfig(time_unit="days"),
    ).run(world)

    assert world.fields["anything"] == 1


def test_real_prototype_pipeline_runs_with_guard_enabled():
    world = WorldState()
    engine = SimulationEngine(
        (
            TerrainModule(),
            HydrologyModule(),
            SettlementSuitabilityModule(),
            SettlementResolutionModule(),
        ),
        SimulationConfig(time_unit="days"),
        enforce_declared_outputs=True,
    )

    engine.run(world)

    assert "terrain.elevation" in world.fields
    assert "hydrology.water" in world.fields
    assert "settlement.suitability" in world.observations
    assert "settlement:001" in world.entities
    assert world.events[0].kind == "settlement.founded"


def write_test_raster(path: Path) -> None:
    elevation = np.full((10, 10), 9.0, dtype="float32")
    elevation[5, 5] = 4.0

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(10.0, 20.0, 0.5, 0.5),
    ) as dataset:
        dataset.write(elevation, 1)


def test_raster_adapter_provider_runs_with_guard_enabled(tmp_path: Path):
    source = tmp_path / "terrain.tif"
    write_test_raster(source)

    class AdapterTerrainModule:
        spec = replace(TerrainModule.spec, name="prototype.terrain")

        def run(self, world: WorldState, context: SimulationContext) -> None:
            RasterTerrainAdapter(source, source_id="test://terrain.tif").load(
                world,
                time=context.time,
            )

    world = WorldState()
    SimulationEngine(
        (
            AdapterTerrainModule(),
            HydrologyModule(),
            SettlementSuitabilityModule(),
            SettlementResolutionModule(),
        ),
        SimulationConfig(time_unit="days"),
        enforce_declared_outputs=True,
    ).run(world, SimulationContext(time=12))

    assert world.fields["terrain.elevation"][5][5] == 4.0


def test_direct_adapter_write_outside_module_execution_remains_unrestricted(tmp_path: Path):
    source = tmp_path / "terrain.tif"
    write_test_raster(source)

    world = WorldState()
    RasterTerrainAdapter(source, source_id="test://terrain.tif").load(world)

    assert world.fields["terrain.elevation"][5][5] == 4.0


class OverlayWritingModule:
    def __init__(self, name, layer, priority, value, with_provenance=True):
        self.spec = ModuleSpec(
            name=name,
            version="ownership-overlay",
            outputs=(
                OutputSpec(
                    "field:shared.value",
                    DataKind.STATE,
                    policy=OutputPolicy.OVERLAY,
                    layer=layer,
                    priority=priority,
                ),
            ),
        )
        self.layer = layer
        self.value = value
        self.with_provenance = with_provenance

    def run(self, world, context):
        world.set_layer_value(
            "field:shared.value",
            self.layer,
            (0, 0),
            self.value,
            Provenance(self.spec.name) if self.with_provenance else None,
        )


def overlay_world(*modules, guarded=False):
    world = WorldState()
    SimulationEngine(
        modules,
        SimulationConfig(time_unit="days"),
        enforce_declared_outputs=guarded,
    ).run(world)
    return world


def test_overlay_effective_value_is_independent_of_producer_order():
    first = OverlayWritingModule("first", "first", 10, "low")
    second = OverlayWritingModule("second", "second", 20, "high")

    world_a = overlay_world(first, second)
    world_b = overlay_world(second, first)

    assert world_a.effective("field:shared.value", (0, 0)) == ("high", "second")
    assert world_b.effective("field:shared.value", (0, 0)) == ("high", "second")


def test_overlay_losing_values_remain_queryable():
    world = overlay_world(
        OverlayWritingModule("first", "first", 10, "low"),
        OverlayWritingModule("second", "second", 20, "high"),
    )

    assert world.layer_values("field:shared.value", (0, 0)) == {
        "first": "low",
        "second": "high",
    }


def test_overlay_provenance_records_winner_and_losers():
    world = overlay_world(
        OverlayWritingModule("first", "first", 10, "low"),
        OverlayWritingModule("second", "second", 20, "high"),
    )

    provenance = world.provenance["overlay:field:shared.value:(0, 0)"]
    assert provenance.producer == "second"
    assert provenance.configuration["_worldloom_overlay"]["layer"] == "second"
    assert provenance.configuration["_worldloom_overlay"]["losing_layers"] == ["first"]
    assert provenance.configuration["_worldloom_overlay"]["losing_producers"] == ["first"]


def test_overlay_provenance_losing_producers_are_only_recorded_when_available():
    world = overlay_world(
        OverlayWritingModule("low", "low", 10, "low"),
        OverlayWritingModule("middle", "middle", 20, "middle", with_provenance=False),
        OverlayWritingModule("high", "high", 30, "high"),
    )

    provenance = world.provenance["overlay:field:shared.value:(0, 0)"]
    overlay_metadata = provenance.configuration["_worldloom_overlay"]

    assert overlay_metadata["losing_layers"] == ["middle", "low"]
    assert overlay_metadata["losing_producers"] == ["low"]


def test_overlay_state_is_snapshot_isolated_and_restorable():
    world = overlay_world(
        OverlayWritingModule("first", "first", 10, {"value": 1}),
        OverlayWritingModule("second", "second", 20, {"value": 2}),
    )
    snapshot = world.snapshot()

    world.overlays["field:shared.value"]["first"][(0, 0)]["value"] = 99
    restored = WorldState()
    restored.restore(snapshot)

    assert restored.layer_values("field:shared.value", (0, 0)) == {
        "first": {"value": 1},
        "second": {"value": 2},
    }
    assert restored.effective("field:shared.value", (0, 0)) == ({"value": 2}, "second")


def test_one_module_can_write_multiple_declared_overlay_layers():
    class MultiLayerModule:
        spec = ModuleSpec(
            name="multi-layer",
            version="ownership-overlay",
            outputs=(
                OutputSpec(
                    "field:shared.value",
                    DataKind.STATE,
                    policy=OutputPolicy.OVERLAY,
                    layer="first",
                    priority=10,
                ),
                OutputSpec(
                    "field:shared.value",
                    DataKind.STATE,
                    policy=OutputPolicy.OVERLAY,
                    layer="second",
                    priority=20,
                ),
            ),
        )

        def run(self, world, context):
            world.set_layer_value("field:shared.value", "first", (0, 0), "low")
            world.set_layer_value("field:shared.value", "second", (0, 0), "high")

    world = overlay_world(MultiLayerModule(), guarded=True)

    assert world.layer_values("field:shared.value", (0, 0)) == {
        "first": "low",
        "second": "high",
    }
    assert world.effective("field:shared.value", (0, 0)) == ("high", "second")


def test_overlay_writes_are_guarded_when_enabled():
    world = overlay_world(
        OverlayWritingModule("first", "first", 10, "low"),
        OverlayWritingModule("second", "second", 20, "high"),
        guarded=True,
    )

    assert world.effective("field:shared.value", (0, 0)) == ("high", "second")


def test_overlay_write_to_another_declared_layer_is_rejected():
    first = OverlayWritingModule("first", "first", 10, "low")

    class WrongLayerModule:
        spec = ModuleSpec(
            name="wrong",
            version="ownership-overlay",
            outputs=(OutputSpec("field:shared.value", DataKind.STATE, policy=OutputPolicy.OVERLAY, layer="second", priority=20),),
        )

        def run(self, world, context):
            world.set_layer_value("field:shared.value", "first", (0, 0), "bad")

    with pytest.raises(ValueError, match="undeclared layer 'first'"):
        overlay_world(first, WrongLayerModule(), guarded=True)


def test_guard_context_is_reset_after_module_exception():
    class FailingModule:
        spec = ModuleSpec(
            name="failing",
            version="ownership-guard",
            outputs=(OutputSpec("field:allowed", DataKind.STATE),),
        )

        def run(self, world, context):
            world.set_field("allowed", 1)
            raise RuntimeError("boom")

    world = WorldState()
    simulation = SimulationEngine((FailingModule(),), SimulationConfig(time_unit="days"), enforce_declared_outputs=True)

    with pytest.raises(RuntimeError, match="boom"):
        simulation.run(world)

    assert world._declared_outputs is None
    assert world._declared_overlay_layers is None
    assert world._active_module_name is None
    world.set_field("outside.module", 2)
    assert world.fields["outside.module"] == 2


def test_reusing_world_state_rejects_conflicting_overlay_registration():
    world = WorldState()
    world.register_overlay("field:shared.value", {"first": 10, "second": 20})

    with pytest.raises(ValueError, match="already registered with different layers"):
        world.register_overlay("field:shared.value", {"first": 10, "third": 30})


def test_reusing_world_state_accepts_identical_overlay_registration():
    world = WorldState()
    layers = {"first": 10, "second": 20}
    world.register_overlay("field:shared.value", layers)
    world.register_overlay("field:shared.value", layers)
    assert world.overlay_priorities["field:shared.value"] == layers


def test_overlay_provenance_is_order_independent_with_three_layers():
    modules = (
        OverlayWritingModule("low", "low", 10, "low"),
        OverlayWritingModule("middle", "middle", 20, "middle"),
        OverlayWritingModule("high", "high", 30, "high"),
    )
    expected = None
    for order in (modules, (modules[2], modules[0], modules[1]), (modules[1], modules[2], modules[0]), (modules[0], modules[2], modules[1])):
        world = overlay_world(*order)
        provenance = world.provenance["overlay:field:shared.value:(0, 0)"]
        current = (provenance.producer, provenance.configuration, provenance.fingerprint)
        if expected is None:
            expected = current
        else:
            assert current == expected

    assert expected[0] == "high"
    assert expected[1]["_worldloom_overlay"] == {
        "layer": "high",
        "losing_layers": ["middle", "low"],
        "losing_producers": ["middle", "low"],
    }


def test_overlay_provenance_is_removed_when_winner_has_no_provenance():
    world = WorldState()
    world.register_overlay("field:shared.value", {"first": 10, "second": 20})
    world.set_layer_value("field:shared.value", "second", (0, 0), "with provenance", Provenance("second"))
    assert "overlay:field:shared.value:(0, 0)" in world.provenance
    world.set_layer_value("field:shared.value", "second", (0, 0), "without provenance")
    assert "overlay:field:shared.value:(0, 0)" not in world.provenance
    assert (0, 0) not in world.overlay_provenance["field:shared.value"]["second"]


def test_overlay_write_to_unregistered_layer_is_rejected():
    module = OverlayWritingModule("first", "first", 10, "low")

    class WrongLayerModule:
        spec = ModuleSpec(
            name="wrong",
            version="ownership-overlay",
            outputs=(
                OutputSpec(
                    "field:shared.value",
                    DataKind.STATE,
                    policy=OutputPolicy.OVERLAY,
                    layer="declared",
                    priority=20,
                ),
            ),
        )

        def run(self, world, context):
            world.set_layer_value("field:shared.value", "wrong", (0, 0), "bad")

    with pytest.raises(ValueError, match="not registered"):
        overlay_world(module, WrongLayerModule())
