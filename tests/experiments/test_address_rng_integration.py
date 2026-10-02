from __future__ import annotations

import random
from dataclasses import dataclass

from worldloom.core import Address, Event, Provenance, WorldState, derive_entity_id, rng_for
from worldloom.interfaces import DataKind, InputSpec, ModuleSpec, OutputSpec, SimulationConfig, SimulationContext
from worldloom.simulation import SimulationEngine


SEED = 314159
GENERATOR_ID = "experiment.address_rng.integration"
GENERATOR_VERSION = "1"
ADDRESSES = (
    Address(("region", "a")),
    Address(("region", "b")),
    Address(("region", "c")),
)


@dataclass
class CandidateModule:
    name: str
    purpose: str

    @property
    def spec(self) -> ModuleSpec:
        return ModuleSpec(
            name=self.name,
            version="1",
            outputs=(OutputSpec(f"observation:{self.purpose}", DataKind.OBSERVATION),),
            temporal_interval=None,
            uncertainty="deterministic keyed randomness",
        )

    def run(self, world: WorldState, context: SimulationContext) -> None:
        values = {
            address.canonical: rng_for(
                context.seed,
                GENERATOR_ID,
                GENERATOR_VERSION,
                address,
                self.purpose,
            ).random()
            for address in ADDRESSES
        }
        world.set_observation(
            self.purpose,
            values,
            Provenance(self.spec.name, time=context.time),
        )


@dataclass
class SharedStreamCandidateModule:
    """Negative control: draws from one shared sequential stream."""

    name: str
    purpose: str
    stream: random.Random

    @property
    def spec(self) -> ModuleSpec:
        return ModuleSpec(
            name=self.name,
            version="1",
            outputs=(OutputSpec(f"observation:{self.purpose}", DataKind.OBSERVATION),),
            temporal_interval=None,
            uncertainty="shared sequential stream (control)",
        )

    def run(self, world: WorldState, context: SimulationContext) -> None:
        values = {address.canonical: self.stream.random() for address in ADDRESSES}
        world.set_observation(
            self.purpose,
            values,
            Provenance(self.spec.name, time=context.time),
        )


@dataclass
class ResolutionModule:
    reverse: bool

    spec = ModuleSpec(
        name="experiment.address_rng.resolution",
        version="1",
        inputs=(
            InputSpec("observation:candidate.a", DataKind.OBSERVATION),
            InputSpec("observation:candidate.b", DataKind.OBSERVATION),
        ),
        outputs=(
            OutputSpec("entity:settlement", DataKind.STATE),
            OutputSpec("event:settlement.founded", DataKind.EVENT),
            OutputSpec("field:resolution.jitter", DataKind.STATE),
        ),
        dependencies=("experiment.candidate.a", "experiment.candidate.b"),
        temporal_interval=None,
        uncertainty="resolves keyed candidate values",
    )

    def run(self, world: WorldState, context: SimulationContext) -> None:
        candidates = {
            address: (
                world.observations["candidate.a"][address.canonical]
                + world.observations["candidate.b"][address.canonical]
            )
            for address in ADDRESSES
        }
        ordered = tuple(reversed(ADDRESSES)) if self.reverse else ADDRESSES
        jitter = {
            address.canonical: rng_for(
                context.seed,
                GENERATOR_ID,
                GENERATOR_VERSION,
                address,
                "resolution.jitter",
            ).random()
            for address in ordered
        }
        world.set_field(
            "resolution.jitter",
            jitter,
            Provenance(self.spec.name, time=context.time),
        )
        location = max(
            ordered,
            key=lambda address: candidates[address] + jitter[address.canonical],
        )
        entity_id = derive_entity_id(
            "settlement",
            "question:experiment.settlement",
            "role:founding",
            "slot:001",
        )
        if entity_id not in world.entities:
            world.add_entity(
                entity_id,
                {
                    "type": "settlement",
                    "location": location.canonical,
                    "score": candidates[location] + jitter[location.canonical],
                },
                Provenance(
                    self.spec.name,
                    inputs=("observation:candidate.a", "observation:candidate.b"),
                    configuration={"resolution": "max-keyed-score"},
                    time=context.time,
                ),
            )
            world.record_event(
                Event(
                    kind="settlement.founded",
                    time=context.time,
                    data={"entity_id": entity_id, "location": location.canonical},
                )
            )


def _jitter_keyed(seed: int, traversal: tuple[Address, ...]) -> dict[str, float]:
    return {
        address.canonical: rng_for(
            seed, GENERATOR_ID, GENERATOR_VERSION, address, "resolution.jitter"
        ).random()
        for address in traversal
    }


def _jitter_shared(seed: int, traversal: tuple[Address, ...]) -> dict[str, float]:
    shared = random.Random(seed)
    return {address.canonical: shared.random() for address in traversal}


def test_keyed_draws_inside_traversal_are_order_independent():
    forward = _jitter_keyed(SEED, ADDRESSES)
    reverse = _jitter_keyed(SEED, tuple(reversed(ADDRESSES)))
    assert forward == reverse


def test_negative_control_shared_stream_is_traversal_order_dependent():
    forward = _jitter_shared(SEED, ADDRESSES)
    reverse = _jitter_shared(SEED, tuple(reversed(ADDRESSES)))
    assert forward != reverse


def _engine(reverse_producers: bool, reverse_resolution: bool) -> SimulationEngine:
    producers = (
        CandidateModule("experiment.candidate.a", "candidate.a"),
        CandidateModule("experiment.candidate.b", "candidate.b"),
    )
    if reverse_producers:
        producers = tuple(reversed(producers))
    return SimulationEngine(
        producers + (ResolutionModule(reverse_resolution),),
        SimulationConfig(time_unit="days"),
    )


def _run(reverse_producers: bool, reverse_resolution: bool) -> WorldState:
    world = WorldState()
    _engine(reverse_producers, reverse_resolution).run(
        world,
        SimulationContext(time=12, seed=SEED),
    )
    return world


def _run_shared_stream(reverse_producers: bool) -> WorldState:
    stream = random.Random(SEED)
    producers = (
        SharedStreamCandidateModule("experiment.candidate.a", "candidate.a", stream),
        SharedStreamCandidateModule("experiment.candidate.b", "candidate.b", stream),
    )
    if reverse_producers:
        producers = tuple(reversed(producers))
    world = WorldState()
    SimulationEngine(producers, SimulationConfig(time_unit="days")).run(
        world, SimulationContext(time=12, seed=SEED)
    )
    return world


def test_negative_control_shared_stream_producers_are_order_dependent():
    forward = _run_shared_stream(False)
    reverse = _run_shared_stream(True)
    assert forward.observations != reverse.observations


def test_engine_result_is_independent_of_producer_and_candidate_order():
    reference = _run(False, False)
    reordered = _run(True, True)

    assert reference.fields
    assert reordered.fields == reference.fields
    assert "resolution.jitter" in reference.fields
    assert reordered.observations == reference.observations
    assert reordered.entities == reference.entities
    assert reordered.events == reference.events
    assert reordered.provenance == reference.provenance
    assert WorldState.fingerprint(reordered.fields) == WorldState.fingerprint(reference.fields)
    assert WorldState.fingerprint(reordered.observations) == WorldState.fingerprint(reference.observations)
    assert WorldState.fingerprint(reordered.entities) == WorldState.fingerprint(reference.entities)


def test_upstream_value_changes_do_not_create_a_second_resolved_entity():
    world = _run(False, False)
    entity_id = derive_entity_id(
        "settlement",
        "question:experiment.settlement",
        "role:founding",
        "slot:001",
    )
    first = world.entities[entity_id].copy()

    changed = WorldState()
    _engine(False, False).run(
        changed,
        SimulationContext(time=12, seed=SEED + 1),
    )

    assert entity_id in changed.entities
    assert len(changed.entities) == 1
    assert changed.entities[entity_id] != first
    assert changed.events[0].data["entity_id"] == entity_id


def test_same_seed_reproduces_engine_state_and_provenance():
    first = _run(False, False)
    second = _run(False, False)

    assert WorldState.fingerprint(first.fields) == WorldState.fingerprint(second.fields)
    assert WorldState.fingerprint(first.observations) == WorldState.fingerprint(second.observations)
    assert WorldState.fingerprint(first.entities) == WorldState.fingerprint(second.entities)
    assert first.provenance == second.provenance
