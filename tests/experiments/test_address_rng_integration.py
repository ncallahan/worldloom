from __future__ import annotations

from dataclasses import dataclass

from worldloom.core import Address, Event, Provenance, WorldState, derive_entity_id, rng_for
from worldloom.interfaces import DataKind, InputSpec, ModuleSpec, OutputSpec, SimulationContext
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
        location = max(ordered, key=lambda address: candidates[address])
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
                    "score": candidates[location],
                },
                Provenance(
                    self.spec.name,
                    inputs=("observation:candidate.a", "observation:candidate.b"),
                    configuration={"reverse": self.reverse},
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


def _engine(reverse_producers: bool, reverse_resolution: bool) -> SimulationEngine:
    producers = (
        CandidateModule("experiment.candidate.a", "candidate.a"),
        CandidateModule("experiment.candidate.b", "candidate.b"),
    )
    if reverse_producers:
        producers = tuple(reversed(producers))
    return SimulationEngine(
        producers + (ResolutionModule(reverse_resolution),),
    )


def _run(reverse_producers: bool, reverse_resolution: bool) -> WorldState:
    world = WorldState()
    _engine(reverse_producers, reverse_resolution).run(
        world,
        SimulationContext(time=12, seed=SEED),
    )
    return world


def test_engine_result_is_independent_of_producer_and_candidate_order():
    reference = _run(False, False)
    reordered = _run(True, True)

    assert reordered.fields == reference.fields
    assert reordered.observations == reference.observations
    assert reordered.entities == reference.entities
    assert reordered.events == reference.events
    assert reordered.provenance == reference.provenance
    assert reordered.fingerprint() == reference.fingerprint()


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

    assert first.fingerprint() == second.fingerprint()
    assert first.provenance == second.provenance
