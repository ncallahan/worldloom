from dataclasses import fields

from worldloom.core import Address, Event, Provenance, SpatialGrid, WorldSnapshot, WorldState


OVERLAY_NAME = "terrain-overlay"
OVERLAY_ADDRESS = Address.cell(0, 0)
SPATIAL_GRID = SpatialGrid(
    shape=(2, 2),
    crs=None,
    transform=(1.0, 0.0, 0.0, 0.0, -1.0, 2.0),
)


def make_world() -> WorldState:
    world = WorldState()
    world.set_field(
        "terrain",
        {"elevation": [[1, 2], [3, 4]]},
        Provenance("terrain", configuration={"source": {"name": "prototype"}}),
        spatial=SPATIAL_GRID,
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
    world.register_overlay(OVERLAY_NAME, {"low": 10, "high": 20})
    world.set_layer_value(
        OVERLAY_NAME,
        "low",
        OVERLAY_ADDRESS,
        {"value": 1},
        Provenance("low", configuration={"source": {"name": "low"}}),
    )
    world.set_layer_value(
        OVERLAY_NAME,
        "high",
        OVERLAY_ADDRESS,
        {"value": 2},
        Provenance("high", configuration={"source": {"name": "high"}}),
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
    assert snapshot.spatial_fields == world.spatial_fields
    assert snapshot.overlays == world.overlays
    assert snapshot.overlay_priorities == world.overlay_priorities
    assert snapshot.overlay_provenance == world.overlay_provenance
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
    world.overlays[OVERLAY_NAME]["high"][OVERLAY_ADDRESS]["value"] = 99
    world.set_layer_value(
        OVERLAY_NAME,
        "low",
        Address.cell(1, 1),
        {"value": 3},
        Provenance("low-extra"),
    )
    world.overlay_priorities[OVERLAY_NAME]["high"] = 99
    world.set_field(
        "terrain",
        world.fields["terrain"],
        spatial=SpatialGrid(
            shape=(3, 3),
            crs=None,
            transform=(2.0, 0.0, 0.0, 0.0, -2.0, 3.0),
        ),
    )
    world.overlay_provenance[OVERLAY_NAME]["high"][OVERLAY_ADDRESS].configuration["source"]["name"] = "changed"
    metadata["execution"]["seed"] = 7

    assert snapshot.fields["terrain"]["elevation"][0][0] == 1
    assert snapshot.entities["settlement:001"]["population"]["value"] == 100
    assert snapshot.events[0].data["entity_id"] == "settlement:001"
    assert snapshot.observations["suitability"]["score"] == [0.5, 0.75]
    assert snapshot.provenance["field:terrain"].configuration["source"]["name"] == "prototype"
    assert snapshot.spatial_fields == {"terrain": SPATIAL_GRID}
    assert snapshot.overlays[OVERLAY_NAME]["high"][OVERLAY_ADDRESS] == {"value": 2}
    assert Address.cell(1, 1) not in snapshot.overlays[OVERLAY_NAME]["low"]
    assert snapshot.overlay_priorities[OVERLAY_NAME] == {"low": 10, "high": 20}
    assert snapshot.overlay_provenance[OVERLAY_NAME]["high"][OVERLAY_ADDRESS].configuration["source"]["name"] == "high"
    assert snapshot.metadata == {"execution": {"seed": 42}}


def test_restore_isolated_from_snapshot():
    world = make_world()
    snapshot = world.snapshot(metadata={"execution": {"seed": 42}})

    world.fields.clear()
    world.entities.clear()
    world.events.clear()
    world.observations.clear()
    world.provenance.clear()
    world.spatial_fields.clear()
    world.overlays.clear()
    world.overlay_priorities.clear()
    world.overlay_provenance.clear()

    world.restore(snapshot)

    assert world.fields == snapshot.fields
    assert world.entities == snapshot.entities
    assert world.events == snapshot.events
    assert world.observations == snapshot.observations
    assert world.provenance == snapshot.provenance
    assert world.spatial_fields == snapshot.spatial_fields
    assert world.overlays == snapshot.overlays
    assert world.overlay_priorities == snapshot.overlay_priorities
    assert world.overlay_provenance == snapshot.overlay_provenance

    world.fields["terrain"]["elevation"][0][0] = 77
    world.entities["settlement:001"]["population"]["value"] = 777
    world.events[0].data["entity_id"] = "settlement:003"
    world.observations["suitability"]["score"].append(2.0)
    world.provenance["field:terrain"].configuration["source"]["name"] = "restored-change"
    world.overlays[OVERLAY_NAME]["low"][OVERLAY_ADDRESS]["value"] = 77
    world.set_layer_value(
        OVERLAY_NAME,
        "high",
        Address.cell(1, 1),
        {"value": 4},
        Provenance("high-extra"),
    )
    world.overlay_priorities[OVERLAY_NAME]["high"] = 99
    world.set_field(
        "terrain",
        world.fields["terrain"],
        spatial=SpatialGrid(
            shape=(3, 3),
            crs=None,
            transform=(2.0, 0.0, 0.0, 0.0, -2.0, 3.0),
        ),
    )
    world.overlay_provenance[OVERLAY_NAME]["high"][OVERLAY_ADDRESS].configuration["source"]["name"] = "restored-change"

    assert snapshot.fields["terrain"]["elevation"][0][0] == 1
    assert snapshot.entities["settlement:001"]["population"]["value"] == 100
    assert snapshot.events[0].data["entity_id"] == "settlement:001"
    assert snapshot.observations["suitability"]["score"] == [0.5, 0.75]
    assert snapshot.provenance["field:terrain"].configuration["source"]["name"] == "prototype"
    assert snapshot.spatial_fields == {"terrain": SPATIAL_GRID}
    assert snapshot.overlays[OVERLAY_NAME]["low"][OVERLAY_ADDRESS] == {"value": 1}
    assert Address.cell(1, 1) not in snapshot.overlays[OVERLAY_NAME]["high"]
    assert snapshot.overlay_priorities[OVERLAY_NAME] == {"low": 10, "high": 20}
    assert snapshot.overlay_provenance[OVERLAY_NAME]["high"][OVERLAY_ADDRESS].configuration["source"]["name"] == "high"
    assert snapshot.metadata == {"execution": {"seed": 42}}


def test_restore_replaces_captured_state():
    world = make_world()
    snapshot = world.snapshot(metadata={"execution": {"seed": 42}})

    world.set_field("extra", {"value": 9}, spatial=SpatialGrid(
        shape=(2, 2),
        crs=None,
        transform=(1.0, 0.0, 10.0, 0.0, -1.0, 12.0),
    ))
    world.register_overlay("extra-overlay", {"only": 30})
    world.set_layer_value("extra-overlay", "only", Address.cell(0, 0), {"value": 9}, Provenance("extra"))
    world.spatial_fields["extra-spatial"] = SpatialGrid(
        shape=(2, 2),
        crs=None,
        transform=(1.0, 0.0, 20.0, 0.0, -1.0, 22.0),
    )

    world.restore(snapshot)

    assert world.fields == snapshot.fields
    assert world.entities == snapshot.entities
    assert world.events == snapshot.events
    assert world.observations == snapshot.observations
    assert world.provenance == snapshot.provenance
    assert world.spatial_fields == snapshot.spatial_fields
    assert world.overlays == snapshot.overlays
    assert world.overlay_priorities == snapshot.overlay_priorities
    assert world.overlay_provenance == snapshot.overlay_provenance
    assert "extra" not in world.fields
    assert "extra-overlay" not in world.overlays
    assert "extra-overlay" not in world.overlay_priorities
    assert "extra-overlay" not in world.overlay_provenance
    assert "extra-spatial" not in world.spatial_fields
    assert snapshot.metadata == {"execution": {"seed": 42}}


def test_restore_ignores_metadata():
    world = make_world()
    snapshot_a = world.snapshot(metadata={"execution": {"seed": 42}})
    snapshot_b = world.snapshot(metadata={"execution": {"seed": 99, "note": "different"}})

    restored_a = make_world()
    restored_b = make_world()
    restored_a.restore(snapshot_a)
    restored_b.restore(snapshot_b)

    assert restored_a.fields == restored_b.fields
    assert restored_a.entities == restored_b.entities
    assert restored_a.events == restored_b.events
    assert restored_a.observations == restored_b.observations
    assert restored_a.provenance == restored_b.provenance
    assert restored_a.spatial_fields == restored_b.spatial_fields
    assert restored_a.overlays == restored_b.overlays
    assert restored_a.overlay_priorities == restored_b.overlay_priorities
    assert restored_a.overlay_provenance == restored_b.overlay_provenance


def test_world_state_and_snapshot_state_fields_match():
    world_state_fields = {field.name for field in fields(WorldState) if not field.name.startswith("_")}
    snapshot_state_fields = {field.name for field in fields(WorldSnapshot) if field.name != "metadata"}

    assert world_state_fields == snapshot_state_fields
