from worldloom.core import Provenance, WorldState


def test_progressive_resolution_keeps_resolved_fact_stable_after_observation_change():
    world = WorldState()
    world.set_observation(
        "settlement.candidates",
        {"region:a": {"location": (2, 3), "score": 0.7}, "region:b": {"location": (7, 4), "score": 0.9}},
        Provenance("test.coarse_projection", time=10),
    )
    world.add_entity(
        "settlement:001",
        {"region": "region:b", "location": (7, 4)},
        Provenance("test.progressive_resolution", inputs=("observation:settlement.candidates",), time=10),
    )
    first = world.entities["settlement:001"].copy()

    world.set_observation(
        "settlement.candidates",
        {"region:a": {"location": (2, 3), "score": 0.95}, "region:b": {"location": (7, 4), "score": 0.4}},
        Provenance("test.coarse_projection", time=20),
    )

    assert world.entities["settlement:001"] == first
    assert world.provenance["entity:settlement:001"].inputs == ("observation:settlement.candidates",)


def test_fingerprints_are_stable_and_recorded_for_observations_and_entities():
    world = WorldState()
    observation = {"region:b": {"location": (7, 4), "score": 0.9}}
    entity = {"region": "region:b", "location": (7, 4)}
    world.set_observation("settlement.candidates", observation, Provenance("test.coarse_projection"))
    world.add_entity("settlement:001", entity, Provenance("test.resolution", inputs=("observation:settlement.candidates",)))

    assert world.provenance["observation:settlement.candidates"].fingerprint == WorldState.fingerprint(observation)
    assert world.provenance["entity:settlement:001"].fingerprint == WorldState.fingerprint(entity)
    assert WorldState.fingerprint({"b": 2, "a": 1}) == WorldState.fingerprint({"a": 1, "b": 2})
