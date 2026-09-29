from worldloom.core import Event, Provenance, WorldSnapshot, WorldState


def make_world() -> WorldState:
    world = WorldState()
    world.set_field(
        "terrain",
        {"elevation": [[1, 2], [3, 4]]},
        Provenance("terrain", configuration={"source": {"name": "prototype"}}),
    )
    world.add_entity(
        "settlement:001",
        {"location": [1, 2], "population": {"value": 100}},
        Provenance("settlement"),
    )
    world.record_event(
        Event("settlement.founded", 1847, {"entity_id": "settlement:001"})
    )
    world.set_observation(
        "suitability",
        {"score": [0.5, 0.75]},
        Provenance("suitability", configuration={"method": {"name": "test"}}),
    )
    return world


def test_snapshot_captures_all_world_state():
    world = make_world()

    snapshot = world.snapshot(metadata={"step": 4, "time": 1847})

    assert isinstance(snapshot, WorldSnapshot)
    assert snapshot.fields == world.fields
    assert snapshot.entities == world.entities
    assert snapshot.events == world.events
    assert snapshot.observations == world.observations
    assert snapshot.provenance == world.provenance
    assert snapshot.metadata == {"step": 4, "time": 1847}


def test_snapshot_isolated_from_later_world_mutation():
    world = make_world()
    metadata = {"execution": {"seed": 42}}
    snapshot = world.snapshot(metadata=metadata)

    world.fields["terrain"]["elevation"][0][0] = 99
    world.entities["settlement:001"]["population"]["value"] = 999
    world.events[0].data["entity_id"] = "settlement:002"
    world.observations["suitability"]["score"].append(1.0)
    world.provenance["field:terrain"].configuration["source"]["name"] = "changed"
    metadata["execution"]["seed"] = 7

    assert snapshot.fields["terrain"]["elevation"][0][0] == 1
    assert snapshot.entities["settlement:001"]["population"]["value"] == 100
    assert snapshot.events[0].data["entity_id"] == "settlement:001"
    assert snapshot.observations["suitability"]["score"] == [0.5, 0.75]
    assert snapshot.provenance["field:terrain"].configuration["source"]["name"] == "prototype"
    assert snapshot.metadata == {"execution": {"seed": 42}}


def test_restore_isolated_from_snapshot():
    world = make_world()
    snapshot = world.snapshot()

    world.fields.clear()
    world.entities.clear()
    world.events.clear()
    world.observations.clear()
    world.provenance.clear()

    world.restore(snapshot)

    assert world.fields == snapshot.fields
    assert world.entities == snapshot.entities
    assert world.events == snapshot.events
    assert world.observations == snapshot.observations
    assert world.provenance == snapshot.provenance

    world.fields["terrain"]["elevation"][0][0] = 77
    world.entities["settlement:001"]["population"]["value"] = 777
    world.events[0].data["entity_id"] = "settlement:003"
    world.observations["suitability"]["score"].append(2.0)
    world.provenance["field:terrain"].configuration["source"]["name"] = "restored-change"

    assert snapshot.fields["terrain"]["elevation"][0][0] == 1
    assert snapshot.entities["settlement:001"]["population"]["value"] == 100
    assert snapshot.events[0].data["entity_id"] == "settlement:001"
    assert snapshot.observations["suitability"]["score"] == [0.5, 0.75]
    assert snapshot.provenance["field:terrain"].configuration["source"]["name"] == "prototype"
