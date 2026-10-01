"""Experimental tests for canonical-state data routing and propagation.

These tests deliberately use tiny in-memory modules rather than production
models. They probe the current engine semantics without introducing a general
router, validation layer, or identifier scheme.
"""

from worldloom.core import Event, Provenance, WorldState
from worldloom.interfaces import (
    DataKind,
    InputSpec,
    ModuleSpec,
    OutputSpec,
    SimulationConfig,
    SimulationContext,
)
from worldloom.simulation import SimulationEngine


def _spec(
    name: str,
    *,
    inputs=(),
    outputs=(),
    dependencies=(),
    temporal_interval=None,
):
    return ModuleSpec(
        name=name,
        version="experiment",
        inputs=inputs,
        outputs=outputs,
        dependencies=dependencies,
        temporal_interval=temporal_interval,
    )


class StateProducer:
    spec = _spec(
        "experiment.a",
        outputs=(OutputSpec("field:a.value", DataKind.STATE),),
    )

    def run(self, world, context):
        world.set_field(
            "a.value",
            {"producer": self.spec.name, "time": context.time},
            Provenance(self.spec.name, time=context.time),
        )


class StateConsumer:
    spec = _spec(
        "experiment.b",
        inputs=(InputSpec("field:a.value", DataKind.STATE),),
        outputs=(OutputSpec("field:b.value", DataKind.STATE),),
        dependencies=("experiment.a",),
    )

    def run(self, world, context):
        source = world.fields["a.value"]
        world.set_field(
            "b.value",
            {"seen": source, "time": context.time},
            Provenance(self.spec.name, inputs=("field:a.value",), time=context.time),
        )


class FanoutConsumer:
    def __init__(self, name, source_name):
        self.spec = _spec(
            name,
            inputs=(InputSpec("field:a.value", DataKind.STATE),),
            outputs=(OutputSpec(f"field:{source_name}.value", DataKind.STATE),),
            dependencies=("experiment.a",),
        )
        self.output_name = source_name

    def run(self, world, context):
        world.set_field(
            f"{self.output_name}.value",
            world.fields["a.value"],
            Provenance(self.spec.name, inputs=("field:a.value",), time=context.time),
        )


class ChainConsumer:
    spec = _spec(
        "experiment.c",
        inputs=(InputSpec("field:b.value", DataKind.STATE),),
        outputs=(OutputSpec("field:c.value", DataKind.STATE),),
        dependencies=("experiment.b",),
    )

    def run(self, world, context):
        world.set_field(
            "c.value",
            world.fields["b.value"],
            Provenance(self.spec.name, inputs=("field:b.value",), time=context.time),
        )


class ObservationProducer:
    spec = _spec(
        "experiment.observation",
        inputs=(InputSpec("field:a.value", DataKind.STATE),),
        outputs=(OutputSpec("observation:a.measurement", DataKind.OBSERVATION),),
        dependencies=("experiment.a",),
    )

    def run(self, world, context):
        world.set_observation(
            "a.measurement",
            {"source": world.fields["a.value"], "time": context.time},
            Provenance(
                self.spec.name,
                inputs=("field:a.value",),
                time=context.time,
            ),
        )


class ResolutionConsumer:
    spec = _spec(
        "experiment.resolution",
        inputs=(InputSpec("observation:a.measurement", DataKind.OBSERVATION),),
        outputs=(
            OutputSpec("entity:fact", DataKind.STATE),
            OutputSpec("event:fact.created", DataKind.EVENT),
        ),
        dependencies=("experiment.observation",),
    )

    def run(self, world, context):
        if "fact:001" in world.entities:
            return

        measurement = world.observations["a.measurement"]
        world.add_entity(
            "fact:001",
            {"measurement": measurement},
            Provenance(
                self.spec.name,
                inputs=("observation:a.measurement",),
                time=context.time,
            ),
        )
        world.record_event(
            Event(
                kind="fact.created",
                time=context.time,
                data={"entity_id": "fact:001"},
            )
        )


class CadencedProducer:
    spec = _spec(
        "experiment.fast",
        outputs=(OutputSpec("field:fast.value", DataKind.STATE),),
        temporal_interval=1.0,
    )

    def run(self, world, context):
        world.set_field(
            "fast.value",
            {"time": context.time},
            Provenance(self.spec.name, time=context.time),
        )


class CadencedConsumer:
    spec = _spec(
        "experiment.slow",
        inputs=(InputSpec("field:fast.value", DataKind.STATE),),
        outputs=(OutputSpec("field:slow.value", DataKind.STATE),),
        dependencies=("experiment.fast",),
        temporal_interval=2.0,
    )

    def run(self, world, context):
        world.set_field(
            "slow.value",
            {"seen_fast_time": world.fields["fast.value"]["time"], "time": context.time},
            Provenance(self.spec.name, inputs=("field:fast.value",), time=context.time),
        )


class SlowerConsumer:
    spec = _spec(
        "experiment.slowest",
        inputs=(InputSpec("field:slow.value", DataKind.STATE),),
        outputs=(OutputSpec("field:slowest.value", DataKind.STATE),),
        dependencies=("experiment.slow",),
        temporal_interval=5.0,
    )

    def run(self, world, context):
        world.set_field(
            "slowest.value",
            {
                "seen_slow_time": world.fields["slow.value"]["time"],
                "time": context.time,
            },
            Provenance(self.spec.name, inputs=("field:slow.value",), time=context.time),
        )


def _engine(*modules):
    return SimulationEngine(
        modules,
        SimulationConfig(time_unit="days"),
    )


def test_state_routes_a_to_b_through_canonical_world():
    world = WorldState()

    _engine(StateConsumer(), StateProducer()).run(world)

    assert world.fields["b.value"]["seen"] == world.fields["a.value"]


def test_one_state_output_can_fan_out_to_multiple_consumers():
    world = WorldState()

    _engine(
        FanoutConsumer("experiment.b", "b"),
        FanoutConsumer("experiment.c", "c"),
        StateProducer(),
    ).run(world)

    assert world.fields["b.value"] == world.fields["a.value"]
    assert world.fields["c.value"] == world.fields["a.value"]


def test_state_can_propagate_through_a_chain():
    world = WorldState()

    _engine(ChainConsumer(), StateConsumer(), StateProducer()).run(world)

    assert world.fields["c.value"] == world.fields["b.value"]
    assert world.fields["b.value"]["seen"] == world.fields["a.value"]


def test_state_observation_resolution_preserves_semantic_boundary():
    world = WorldState()

    _engine(
        ResolutionConsumer(),
        ObservationProducer(),
        StateProducer(),
    ).run(world, SimulationContext(time=12))

    assert "a.value" in world.fields
    assert "a.measurement" in world.observations
    assert "a.measurement" not in world.fields
    assert world.entities["fact:001"]["measurement"] == world.observations["a.measurement"]
    assert world.events[0].kind == "fact.created"


def test_differing_temporal_cadences_consume_latest_available_state():
    world = WorldState()

    _engine(
        SlowerConsumer(),
        CadencedConsumer(),
        CadencedProducer(),
    ).run(world, SimulationContext(time=0), until=5)

    assert world.fields["fast.value"]["time"] == 5
    assert world.fields["slow.value"]["time"] == 4
    assert world.fields["slowest.value"] == {
        "seen_slow_time": 4,
        "time": 5,
    }
