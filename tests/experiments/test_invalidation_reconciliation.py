from worldloom.core import Provenance, WorldState


def _resolve_settlement(world: WorldState, context_time: float) -> None:
    candidates = world.observations["settlement.candidates"]
    region = max(candidates, key=lambda key: candidates[key]["score"])
    world.add_entity(
        "settlement:001",
        {"region": region, "location": candidates[region]["location"]},
        Provenance(
            "test.resolution",
            inputs=("observation:settlement.candidates",),
            time=context_time,
        ),
    )


def test_upstream_change_is_detectable_but_resolved_fact_is_not_automatically_invalidated():
    world = WorldState()

    first_observation = {
        "region:a": {"location": (2, 3), "score": 0.7},
        "region:b": {"location": (7, 4), "score": 0.9},
    }
    world.set_observation(
        "settlement.candidates",
        first_observation,
        Provenance("test.projection", time=10),
    )
    first_observation_provenance = world.provenance["observation:settlement.candidates"]
    first_observation_fingerprint = first_observation_provenance.fingerprint

    _resolve_settlement(world, 10)
    first_entity = world.entities["settlement:001"].copy()
    entity_provenance = world.provenance["entity:settlement:001"]

    changed_observation = {
        "region:a": {"location": (2, 3), "score": 0.95},
        "region:b": {"location": (7, 4), "score": 0.4},
    }
    world.set_observation(
        "settlement.candidates",
        changed_observation,
        Provenance("test.projection", time=20),
    )
    current_observation_provenance = world.provenance["observation:settlement.candidates"]

    assert current_observation_provenance.fingerprint != first_observation_fingerprint
    assert world.entities["settlement:001"] == first_entity
    assert entity_provenance.inputs == ("observation:settlement.candidates",)
    assert entity_provenance.fingerprint == WorldState.fingerprint(first_entity)


def test_snapshot_can_preserve_the_previous_provenance_needed_for_change_detection():
    world = WorldState()
    world.set_observation(
        "settlement.candidates",
        {"region:b": {"location": (7, 4), "score": 0.9}},
        Provenance("test.projection", time=10),
    )
    before_change = world.snapshot()

    world.set_observation(
        "settlement.candidates",
        {"region:b": {"location": (7, 4), "score": 0.4}},
        Provenance("test.projection", time=20),
    )

    before = before_change.provenance["observation:settlement.candidates"]
    after = world.provenance["observation:settlement.candidates"]

    assert before.fingerprint != after.fingerprint
    assert before.time == 10
    assert after.time == 20
