import json
import math
from dataclasses import fields as dataclass_fields

import pytest

from tests.test_support import strict_equal
from worldloom.core import (
    Address,
    Event,
    Provenance,
    SpatialGrid,
    WorldSnapshot,
    WorldState,
)
from worldloom.core.hashing import fingerprint
from worldloom.core.persistence import (
    _decode,
    _encode,
    decode_snapshot,
    dumps_snapshot,
    encode_snapshot,
)


def rt(value):
    return _decode(_encode(value))


def _empty_snapshot_data():
    return {
        "fields": {},
        "entities": {},
        "events": [],
        "observations": {},
        "provenance": {},
        "metadata": {},
        "spatial_fields": {},
        "overlays": {},
        "overlay_priorities": {},
        "overlay_provenance": {},
    }


def _decode_with_events(events):
    data = _empty_snapshot_data()
    data["events"] = events
    return decode_snapshot(data)


def _decode_with_provenance(provenance):
    data = _empty_snapshot_data()
    data["provenance"] = provenance
    return decode_snapshot(data)


def _decode_with_spatial_fields(spatial_fields):
    data = _empty_snapshot_data()
    data["spatial_fields"] = spatial_fields
    return decode_snapshot(data)


def test_strict_helper_meta():
    assert strict_equal((1, True), (1, True))
    assert not strict_equal((1, True), [1, True])
    assert not strict_equal(1, 1.0)
    assert not strict_equal(-0.0, 0.0)
    assert not strict_equal({(1, 2): "x"}, {(1.0, 2): "x"})
    assert not strict_equal({1}, {True})
    with pytest.raises(TypeError):
        strict_equal(object(), object())


def test_strict_helper_dataclasses():
    assert strict_equal(
        Event("x", 1.0, {"a": (1,)}),
        Event("x", 1.0, {"a": (1,)}),
    )
    assert not strict_equal(
        Event("x", 1, {}),
        Event("x", 1.0, {}),
    )
    assert strict_equal(
        Provenance("p", inputs=("x",)),
        Provenance("p", inputs=("x",)),
    )
    grid = SpatialGrid(
        (2, 3),
        "EPSG:4326",
        (1, 0, 0, 0, -1, 0),
    )
    assert strict_equal(
        grid,
        SpatialGrid(
            (2, 3),
            "EPSG:4326",
            (1, 0, 0, 0, -1, 0),
        ),
    )
    assert strict_equal(
        Address(("a", "b")),
        Address.parse("/a/b"),
    )


def test_scalars_and_empty():
    values = [
        None,
        True,
        False,
        0,
        -7,
        2**100,
        1.25,
        -0.0,
        "héllo",
        [],
        {},
        set(),
        (),
    ]
    for value in values:
        assert strict_equal(value, rt(value))
        assert value == rt(value)


def test_scalar_types_preserved():
    for value in [1, 1.0, True]:
        assert type(rt(value)) is type(value)


def test_negative_zero():
    assert math.copysign(1.0, rt(-0.0)) == -1.0


@pytest.mark.parametrize(
    "value",
    [
        {1: "int"},
        {True: "bool"},
        {None: "none"},
    ],
)
def test_dictionary_key_types_round_trip(value):
    round_tripped = rt(value)
    assert strict_equal(value, round_tripped)


def test_tuples_keys_and_nested_values():
    value = {
        (1, "x", (2,)): {True, None},
        "x": [{"$set": 1}, {(1, 2): {"$tuple": [3, 4]}}],
    }
    assert strict_equal(value, rt(value))


def test_addresses():
    address = Address(("region", "city with spaces"))
    value = {address: {"location": address}}
    assert strict_equal(value, rt(value))


def enc(value):
    return json.dumps(
        _encode(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def test_determinism():
    first = {
        "b": {3, (2, 1), "a"},
        "a": {"y": 2, "x": 1},
    }
    second = {
        "a": {"x": 1, "y": 2},
        "b": {(2, 1), "a", 3},
    }
    assert enc(first) == enc(second)


@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        frozenset({1}),
        object(),
    ],
)
def test_rejections(value):
    with pytest.raises(TypeError):
        _encode(value)


def test_numpy_scalar_rejected():
    np = pytest.importorskip("numpy")
    with pytest.raises(TypeError):
        _encode(np.float64(1.5))


def test_dataclass_rejected():
    from dataclasses import dataclass

    @dataclass
    class Other:
        value: int

    with pytest.raises(TypeError):
        _encode(Other(1))


def _full_world():
    world = WorldState()
    world.set_field(
        "shared",
        {"values": (1, 2), "set": {3, 4}},
        Provenance("field", time=1),
    )
    world.set_observation(
        "shared",
        {(1, 2): 0.75},
        Provenance("observation"),
    )
    world.add_entity(
        "entity:001",
        {"location": (3, 4)},
        Provenance("entity"),
    )
    world.record_event(
        Event(
            "test.event",
            12,
            {
                "location": (3, 4),
                "address": Address.cell(3, 4),
            },
        )
    )
    world.register_overlay(
        "terrain",
        {"base": 0, "override": 10},
    )
    address = Address.cell(2, 3)
    world.set_layer_value(
        "terrain",
        "base",
        address,
        {"height": 1},
        Provenance("base", inputs=("x",)),
    )
    world.set_layer_value(
        "terrain",
        "override",
        address,
        {"height": 2},
        Provenance(
            "override",
            configuration={"mode": ("replace",)},
            time=2,
        ),
    )
    world.spatial_fields["shared"] = SpatialGrid(
        (10, 10),
        "EPSG:4326",
        (0.5, 0, 10, 0, -0.5, 20),
    )
    return world


def test_snapshot_drift_guard():
    field_names = {field.name for field in dataclass_fields(WorldSnapshot)}
    encoded_keys = set(
        encode_snapshot(
            WorldSnapshot(
                {},
                {},
                [],
                {},
                {},
                {},
                {},
                {},
                {},
                {},
            )
        )
    )
    from worldloom.core.persistence import _TOP_LEVEL

    assert field_names == _TOP_LEVEL
    assert encoded_keys == _TOP_LEVEL
    assert field_names == encoded_keys


def test_full_world_snapshot_round_trip():
    snapshot = _full_world().snapshot(
        {"note": "test", "tuple": (1, 2)}
    )
    loaded = decode_snapshot(json.loads(dumps_snapshot(snapshot)))
    all_members = (
        "fields",
        "entities",
        "events",
        "observations",
        "provenance",
        "metadata",
        "spatial_fields",
        "overlays",
        "overlay_priorities",
        "overlay_provenance",
    )

    for name in all_members:
        assert strict_equal(
            getattr(snapshot, name),
            getattr(loaded, name),
        )
        assert getattr(snapshot, name) == getattr(loaded, name)

    fingerprinted = (
        "fields",
        "entities",
        "observations",
        "metadata",
        "overlay_priorities",
    )
    for name in fingerprinted:
        assert fingerprint(getattr(snapshot, name)) == fingerprint(
            getattr(loaded, name)
        )


def test_mixed_type_set_round_trip():
    value = {1, "1", (2, True), Address.cell(0, 0)}
    assert strict_equal(value, rt(value))



def test_structured_times_round_trip_as_ints():
    world = _full_world()
    snapshot = world.snapshot()
    loaded = decode_snapshot(json.loads(dumps_snapshot(snapshot)))

    assert type(loaded.events[0].time) is int
    assert type(loaded.provenance["field:shared"].time) is int
    assert loaded.events[0].time == 12
    assert loaded.provenance["field:shared"].time == 1


def test_snapshot_collections_remain_separate():
    loaded = decode_snapshot(
        json.loads(dumps_snapshot(_full_world().snapshot()))
    )
    assert "shared" in loaded.fields
    assert "shared" in loaded.observations
    assert loaded.fields["shared"] != loaded.observations["shared"]


def test_snapshot_independence():
    snapshot = _full_world().snapshot(
        {"mutable": {"items": [1, 2]}}
    )
    encoded_data = encode_snapshot(snapshot)
    before = json.dumps(
        encoded_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )

    snapshot.fields["shared"]["set"].add(5)
    snapshot.metadata["mutable"]["items"].append(3)
    snapshot.overlays["terrain"]["base"][Address.cell(2, 3)]["height"] = 99

    after = json.dumps(
        encoded_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    assert before == after


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"fields": 1},
        {
            **_empty_snapshot_data(),
            "extra": {},
        },
    ],
)
def test_snapshot_top_level_keys_are_strict(data):
    with pytest.raises(ValueError):
        decode_snapshot(data)


def test_text_round_trip_is_deterministic():
    snapshot = _full_world().snapshot()
    assert dumps_snapshot(snapshot) == dumps_snapshot(snapshot)


def test_load_snapshot_and_load_world_metadata_semantics(tmp_path):
    world = _full_world()
    expected = world.snapshot({"run": "test"})
    path = tmp_path / "world.json"

    from worldloom.core.persistence import load_snapshot, load_world, save_world

    save_world(world, path, metadata={"run": "test"})
    snapshot = load_snapshot(path)
    loaded = load_world(path)

    all_members = (
        "fields",
        "entities",
        "events",
        "observations",
        "provenance",
        "metadata",
        "spatial_fields",
        "overlays",
        "overlay_priorities",
        "overlay_provenance",
    )
    for name in all_members:
        assert strict_equal(
            getattr(expected, name),
            getattr(snapshot, name),
        )
        assert getattr(expected, name) == getattr(snapshot, name)

    fingerprinted = (
        "fields",
        "entities",
        "observations",
        "metadata",
        "overlay_priorities",
    )
    for name in fingerprinted:
        assert fingerprint(getattr(expected, name)) == fingerprint(
            getattr(snapshot, name)
        )

    assert loaded.fields == world.fields
    assert loaded.entities == world.entities
    assert loaded.observations == world.observations
    assert loaded.events == world.events
    assert loaded.provenance == world.provenance
    assert loaded.spatial_fields == world.spatial_fields
    assert loaded.overlays == world.overlays
    assert loaded.overlay_priorities == world.overlay_priorities
    assert loaded.overlay_provenance == world.overlay_provenance
    assert loaded._declared_outputs is None
    assert loaded._declared_overlay_layers is None
    assert loaded._active_module_name is None


@pytest.mark.parametrize(
    "value",
    [
        {"$unknown": []},
        {"$tuple": [], "extra": []},
        {"$tuple": "not-a-list"},
        {"$set": "not-a-list"},
        {"$address": 1},
        {"$address": "not an address"},
        {"$dict": "not-a-list"},
        {"$dict": [[1]]},
        {"$dict": [[1, "first"], [1.0, "duplicate"]]},
        {"$dict": [[[], "unhashable"]]},
        {"$set": [[]]},
        {"$set": [1, 1]},
    ],
)
def test_decode_rejects_malformed_tagged_values(value):
    with pytest.raises(ValueError):
        _decode(value)


def test_loads_rejects_duplicate_json_object_keys():
    from worldloom.core.persistence import loads_snapshot

    with pytest.raises(ValueError):
        loads_snapshot('{"fields": {}, "fields": {}}')


def test_loads_rejects_duplicate_tag_keys():
    from worldloom.core.persistence import loads_snapshot

    with pytest.raises(ValueError):
        loads_snapshot('{"$tuple": [], "$tuple": []}')


@pytest.mark.parametrize(
    "text",
    [
        '{"fields": {"value": NaN}, "entities": {}, "events": [], "observations": {}, "provenance": {}, "metadata": {}, "spatial_fields": {}, "overlays": {}, "overlay_priorities": {}, "overlay_provenance": {}}',
        '{"fields": {"value": Infinity}, "entities": {}, "events": [], "observations": {}, "provenance": {}, "metadata": {}, "spatial_fields": {}, "overlays": {}, "overlay_priorities": {}, "overlay_provenance": {}}',
        '{"fields": {"value": -Infinity}, "entities": {}, "events": [], "observations": {}, "provenance": {}, "metadata": {}, "spatial_fields": {}, "overlays": {}, "overlay_priorities": {}, "overlay_provenance": {}}',
        '{"fields": {"value": 1e999}, "entities": {}, "events": [], "observations": {}, "provenance": {}, "metadata": {}, "spatial_fields": {}, "overlays": {}, "overlay_priorities": {}, "overlay_provenance": {}}',
    ],
)
def test_loads_rejects_nonfinite_json_numbers(text):
    from worldloom.core.persistence import loads_snapshot

    with pytest.raises(ValueError):
        loads_snapshot(text)


@pytest.mark.parametrize(
    "events",
    [
        [{}],
        [{"kind": 1, "time": 1.0, "data": {}}],
        [{"kind": "event", "time": true, "data": {}}],
        [{"kind": "event", "time": 1.0, "data": []}],
    ],
)
def test_decode_valid_event_json_shape():
    snapshot = _decode_with_events([{"kind": "event", "time": 1, "data": {"value": {"$tuple": [1, 2]}}}])
    assert snapshot.events == [Event("event", 1, {"value": (1, 2)})]


def test_decode_rejects_invalid_events(events):
    with pytest.raises(ValueError):
        _decode_with_events(events)


@pytest.mark.parametrize(
    "provenance",
    [
        {"name": {}},
        {
            "name": {
                "producer": 1,
                "inputs": {"not": "a tuple"},
                "configuration": {},
                "time": 0.0,
                "fingerprint": None,
            }
        },
        {
            "name": {
                "producer": "producer",
                "inputs": {"$tuple": []},
                "configuration": [],
                "time": 0.0,
                "fingerprint": None,
            }
        },
        {
            "name": {
                "producer": "producer",
                "inputs": (),
                "configuration": {},
                "time": True,
                "fingerprint": None,
            }
        },
        {
            "name": {
                "producer": "producer",
                "inputs": (),
                "configuration": {},
                "time": 0.0,
                "fingerprint": 1,
            }
        },
    ],
)
def test_decode_valid_provenance_json_shape():
    snapshot = _decode_with_provenance({"name": {"producer": "producer", "inputs": {"$tuple": ["input"]}, "configuration": {}, "time": 1, "fingerprint": None}})
    assert snapshot.provenance["name"] == Provenance("producer", ("input",), {}, 1, None)


def test_decode_rejects_invalid_provenance(provenance):
    with pytest.raises(ValueError):
        _decode_with_provenance(provenance)


@pytest.mark.parametrize(
    "spatial_fields",
    [
        {"grid": {}},
        {
            "grid": {
                "shape": [2, 2],
                "crs": "EPSG:4326",
                "transform": {"$tuple": [1, 0, 0, 0, -1, 0]},
            }
        },
        {
            "grid": {
                "shape": (2, 2),
                "crs": 1,
                "transform": (1, 0, 0, 0, -1, 0),
            }
        },
        {
            "grid": {
                "shape": (2, 2),
                "crs": "EPSG:4326",
                "transform": [1, 0, 0, 0, -1, 0],
            }
        },
    ],
)
def test_decode_valid_spatial_field_json_shape():
    snapshot = _decode_with_spatial_fields({"grid": {"shape": {"$tuple": [2, 2]}, "crs": "EPSG:4326", "transform": {"$tuple": [1, 0, 0, 0, -1, 0]}}})
    assert snapshot.spatial_fields["grid"] == SpatialGrid((2, 2), "EPSG:4326", (1, 0, 0, 0, -1, 0))


def test_decode_rejects_invalid_spatial_fields(spatial_fields):
    with pytest.raises(ValueError):
        _decode_with_spatial_fields(spatial_fields)


@pytest.mark.parametrize(
    "member",
    [
        "fields",
        "entities",
        "events",
        "observations",
        "provenance",
        "metadata",
        "spatial_fields",
        "overlays",
        "overlay_priorities",
        "overlay_provenance",
    ],
)
def test_decode_rejects_wrong_snapshot_member_types(member):
    data = _empty_snapshot_data()
    data[member] = "wrong"
    with pytest.raises(ValueError):
        decode_snapshot(data)


def test_decode_rejects_nonstring_overlay_provenance_name():
    data = _empty_snapshot_data()
    data["overlay_provenance"] = {
        ("not", "a", "string"): {},
    }
    with pytest.raises(ValueError):
        decode_snapshot(data)


def test_prototype_round_trips(tmp_path):
    from worldloom.core.persistence import load_world, save_world
    from worldloom.interfaces import SimulationConfig
    from worldloom.modules import (
        HydrologyModule,
        SettlementResolutionModule,
        SettlementSuitabilityModule,
        TerrainModule,
    )
    from worldloom.simulation import SimulationEngine

    def run(grid):
        world = WorldState()
        SimulationEngine(
            (
                TerrainModule(spatial_grid=grid),
                HydrologyModule(),
                SettlementSuitabilityModule(),
                SettlementResolutionModule(),
            ),
            SimulationConfig(time_unit="days"),
        ).run(world)
        return world

    for index, grid in enumerate(
        [
            SpatialGrid(
                (10, 10),
                "EPSG:4326",
                (0.5, 0, 10, 0, -0.5, 20),
            ),
            None,
        ]
    ):
        world = run(grid)
        path = tmp_path / f"prototype-{index}.json"
        save_world(world, path)
        loaded = load_world(path)

        for name in (
            "fields",
            "entities",
            "events",
            "observations",
            "provenance",
            "spatial_fields",
            "overlays",
            "overlay_priorities",
            "overlay_provenance",
        ):
            assert strict_equal(
                getattr(world, name),
                getattr(loaded, name),
            )
            assert getattr(world, name) == getattr(loaded, name)

        for name in ("fields", "entities", "observations"):
            assert fingerprint(getattr(world, name)) == fingerprint(
                getattr(loaded, name)
            )

        for key, value in loaded.provenance.items():
            if key.startswith("field:"):
                stored = loaded.fields[key.removeprefix("field:")]
            elif key.startswith("observation:"):
                stored = loaded.observations[key.removeprefix("observation:")]
            elif key.startswith("entity:"):
                stored = loaded.entities[key.removeprefix("entity:")]
            else:
                continue
            assert value.fingerprint == fingerprint(stored)


def test_loaded_world_is_independent_from_original(tmp_path):
    from worldloom.core.persistence import load_world, save_world
    world = _full_world()
    path = tmp_path / "independence.json"
    save_world(world, path)
    loaded = load_world(path)
    loaded.fields["shared"]["set"].add(99)
    loaded.metadata["changed"] = True
    loaded.events[0].data["location"] = (99, 99)
    loaded.overlays["terrain"]["base"][Address.cell(2, 3)]["height"] = 99
    assert 99 not in world.fields["shared"]["set"]
    assert "changed" not in world.metadata
    assert world.events[0].data["location"] == (3, 4)
    assert world.overlays["terrain"]["base"][Address.cell(2, 3)]["height"] == 1


def test_save_world_preserves_existing_file_on_encode_failure(tmp_path):
    from worldloom.core.persistence import save_world
    path = tmp_path / "world.json"
    save_world(_full_world(), path)
    original = path.read_text(encoding="utf-8")
    bad_world = WorldState()
    bad_world.set_field("bad", object())
    with pytest.raises(TypeError):
        save_world(bad_world, path)
    assert path.read_text(encoding="utf-8") == original


@pytest.mark.parametrize(
    "grid",
    [
        SpatialGrid((10, 10), "EPSG:4326", (0.5, 0, 10, 0, -0.5, 20)),
        None,
    ],
)
def test_prototype_round_trips(tmp_path, grid):
    from worldloom.core.persistence import load_world, save_world

    world = _full_world()
    path = tmp_path / "overlay.json"
    save_world(world, path)
    loaded = load_world(path)
    address = Address.cell(2, 3)

    assert loaded.layer_values(
        "terrain",
        address,
    ) == {
        "base": {"height": 1},
        "override": {"height": 2},
    }
    assert loaded.effective(
        "terrain",
        address,
    ) == ({"height": 2}, "override")
