from copy import deepcopy
import json
from pathlib import Path

import pytest

from worldloom.core.hashing import fingerprint

from worldloom.adapters.fmg import entities as entities_module
from worldloom.adapters.fmg import import_fmg_snapshot
from worldloom.adapters.fmg.entities import build_entities
from worldloom.adapters.fmg.importer import IMPORTER_VERSION
from worldloom.core import WorldState


REPO_ROOT = Path(__file__).parents[2]
THIMALAND = REPO_ROOT / "examples" / "Thimaland Full 2026-10-02-14-17.json"
PITHIGY = REPO_ROOT / "examples" / "Pithigy Full 2026-10-02-11-35.json"
VIVERIA = REPO_ROOT / "examples" / "Viveria Full 2026-10-02-11-31.json"


EXPECTED_COUNTS = {
    THIMALAND: {"states": 1, "provinces": 0, "burgs": 9, "cultures": 2, "religions": 3},
    PITHIGY: {"states": 4, "provinces": 117, "burgs": 506, "cultures": 4, "religions": 9},
    VIVERIA: {"states": 7, "provinces": 71, "burgs": 713, "cultures": 4, "religions": 8},
}


@pytest.mark.parametrize("path,expected", EXPECTED_COUNTS.items())
def test_entity_counts_match_experiment_digest(path: Path, expected: dict[str, int]):
    world = WorldState()
    import_fmg_snapshot(world, path)
    actual = {
        collection: sum(
            entity["fmg"]["collection"] == collection for entity in world.entities.values()
        )
        for collection in expected
    }
    assert actual == expected


def test_provisional_golden_entity_ids():
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    assert "burg:624f67d66cae" in world.entities
    assert "state:22ebfe471563" in world.entities
    assert "culture:dc5d9cef07f9" in world.entities
    assert "religion:eb478b1e3bf1" in world.entities
    assert "province:5e8c030b494a" not in world.entities


def test_placeholder_records_are_not_entities_and_positions_are_preserved():
    world = WorldState()
    import_fmg_snapshot(world, PITHIGY)
    assert all(entity["fmg"]["id"] != 0 for entity in world.entities.values() if entity["fmg"]["collection"] in {"burgs", "provinces"})
    for entity_id, entity in world.entities.items():
        collection = entity["fmg"]["collection"]
        assert entity["fmg"]["id"] == entity["attributes"]["i"]
        assert entity["fmg"]["position"] >= 0
        if collection in {"states", "cultures", "religions"}:
            assert entity["fmg"]["id"] == entity["fmg"]["position"]


def test_excluded_keys_are_absent_and_fmg_names_are_not_aliases():
    world = WorldState()
    import_fmg_snapshot(world, PITHIGY)
    for entity in world.entities.values():
        collection = entity["fmg"]["collection"]
        attributes = entity["attributes"]
        assert "alias" not in attributes
        if collection in {"states", "provinces", "burgs"}:
            assert "coa" not in attributes
        if collection == "burgs":
            assert "production" not in attributes
            assert "product" in attributes
            assert "market" in attributes
        if collection == "states":
            assert "military" not in attributes
            assert "campaigns" not in attributes


def test_reference_resolution_outcomes():
    data = {
        "info": {"version": "test", "mapId": "test", "seed": 1},
        "pack": {
            "cells": [{}, {}],
            "states": [
                {"i": 0, "neighbors": [1, -1, 99, "x"], "provinces": [1, 0, -1]},
                {"i": 1, "neighbors": [0], "provinces": []},
            ],
            "provinces": [0, {"i": 1, "state": 0, "center": 1}, {"i": 2, "state": 99, "center": -1}],
            "burgs": [0, {"i": 1, "cell": 1, "state": -1}],
            "cultures": [{"i": 0}],
            "religions": [{"i": 0}],
        }
    }
    entities, report = build_entities(data)
    state0 = entities["state:22ebfe471563"]
    state1_id = next(entity_id for entity_id, entity in entities.items() if entity["fmg"] == {"collection": "states", "id": 1, "position": 1})
    assert state0["refs"]["neighbors"] == [state1_id]
    assert state0["refs"]["provinces"] == ["province:5e8c030b494a"]
    province1 = entities["province:5e8c030b494a"]
    assert province1["refs"]["state"] == "state:22ebfe471563"
    assert province1["refs"]["center"] == {"space": "pack.cells", "index": 1}
    burg1 = entities["burg:624f67d66cae"]
    assert burg1["refs"] == {"cell": {"space": "pack.cells", "index": 1}}
    kinds = report["anomalies"]["counts"]
    assert sum(kinds["sentinel"].values()) == 4
    assert sum(kinds["placeholder-reference"].values()) == 1
    assert sum(kinds["unresolved-reference"].values()) == 2
    assert sum(kinds["invalid-type"].values()) == 1
    assert all("position" in example and "record" not in example for example in report["anomalies"]["examples"])


def test_report_records_dropped_key_counts():
    world = WorldState()
    import_fmg_snapshot(world, PITHIGY)
    dropped = world.observations["fmg.import.report"]["entities"]["dropped_keys"]
    assert dropped["states"]["coa"] == 3
    assert dropped["states"]["military"] == 3
    assert dropped["states"]["campaigns"] == 3
    assert dropped["provinces"]["coa"] == 117
    assert dropped["burgs"]["coa"] == 506
    assert dropped["burgs"]["production"] == 506


def test_reference_order_independence(monkeypatch):
    data = {
        "pack": {
            "states": [{"i": 0, "provinces": [1]}],
            "provinces": [0, {"i": 1, "state": 0, "center": 0}],
            "burgs": [0, {"i": 1, "state": 0, "cell": 0}],
            "cultures": [{"i": 0}],
            "religions": [{"i": 0}],
            "cells": [{}],
        }
    }
    entities_a, report_a = build_entities(data)
    monkeypatch.setattr(
        entities_module,
        "COLLECTION_SPECS",
        dict(reversed(list(entities_module.COLLECTION_SPECS.items()))),
    )
    entities_b, report_b = build_entities(data)
    assert entities_a == entities_b
    assert report_a == report_b


def test_duplicate_explicit_i_aborts_without_writes(tmp_path: Path):
    raw = json.loads(THIMALAND.read_text(encoding="utf-8"))
    raw["pack"]["states"].append(deepcopy(raw["pack"]["states"][0]))
    path = tmp_path / "duplicate.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    world = WorldState()
    with pytest.raises(ValueError, match="Duplicate explicit FMG i"):
        import_fmg_snapshot(world, path)
    assert not world.fields
    assert not world.entities
    assert not world.observations
    assert not world.provenance


def test_reimport_existing_entities_aborts_without_partial_writes():
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    before = world.snapshot()
    with pytest.raises(ValueError, match="Entity already exists"):
        import_fmg_snapshot(world, THIMALAND)
    assert world.snapshot() == before


def test_entity_import_is_deterministic_and_persistent(tmp_path: Path):
    from worldloom.core.persistence import load_world, save_world

    world_a = WorldState()
    world_b = WorldState()
    import_fmg_snapshot(world_a, THIMALAND)
    import_fmg_snapshot(world_b, THIMALAND)
    assert world_a.entities == world_b.entities
    assert world_a.provenance == world_b.provenance
    assert world_a.observations == world_b.observations

    path = tmp_path / "thimaland.json"
    save_world(world_a, path)
    loaded = load_world(path)
    assert loaded.entities == world_a.entities
    assert loaded.fingerprint(loaded.entities) == world_a.fingerprint(world_a.entities)

def test_importer_version_is_recorded_in_provenance():
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    assert world.provenance
    assert {
        provenance.configuration["importer_version"]
        for provenance in world.provenance.values()
    } == {IMPORTER_VERSION}
    assert IMPORTER_VERSION == "0.3.0"


@pytest.mark.parametrize(
    "path,expected_burgs,expected_neighbors,expected_provinces",
    [
        (THIMALAND, 9, 0, 0),
        (PITHIGY, 506, 8, 117),
        (VIVERIA, 713, 14, 71),
    ],
)
def test_real_fixture_reference_resolution(
    path: Path,
    expected_burgs: int,
    expected_neighbors: int,
    expected_provinces: int,
):
    world = WorldState()
    import_fmg_snapshot(world, path)
    report = world.observations["fmg.import.report"]["entities"]

    burgs = [
        entity
        for entity in world.entities.values()
        if entity["fmg"]["collection"] == "burgs"
    ]
    assert len(burgs) == expected_burgs
    assert all("cell" in entity["refs"] for entity in burgs)
    assert all("state" in entity["refs"] for entity in burgs)
    assert all(
        entity["refs"]["cell"]["space"] == "pack.cells"
        and isinstance(entity["refs"]["cell"]["index"], int)
        for entity in burgs
    )
    assert all(isinstance(entity["refs"]["state"], str) for entity in burgs)

    states = [
        entity
        for entity in world.entities.values()
        if entity["fmg"]["collection"] == "states"
    ]
    assert sum(len(entity["refs"].get("neighbors", [])) for entity in states) == expected_neighbors
    assert sum(len(entity["refs"].get("provinces", [])) for entity in states) == expected_provinces

    assert isinstance(report["anomalies"]["total"], int)
    anomaly_counts = report["anomalies"]["counts"]
    forbidden = (".cell", ".state", ".neighbors", ".provinces")
    for kind_counts in anomaly_counts.values():
        assert not any(
            path.startswith(("pack.burgs[", "pack.states["))
            and any(suffix in path for suffix in forbidden)
            for path in kind_counts
        )


EXPECTED_NEW_COUNTS = {
    THIMALAND: {"rivers": 49, "routes": 9, "markers": 14},
    PITHIGY: {"rivers": 156, "routes": 427, "markers": 49},
    VIVERIA: {"rivers": 53, "routes": 570, "markers": 59},
}

EXPECTED_NEW_REF_TOTALS = {
    THIMALAND: {"rivers": 191, "routes": 54, "markers": 14},
    PITHIGY: {"rivers": 686, "routes": 2666, "markers": 49},
    VIVERIA: {"rivers": 249, "routes": 3233, "markers": 59},
}


@pytest.mark.parametrize("path,expected", EXPECTED_NEW_COUNTS.items())
def test_new_entity_counts_match_experiment_digest(path: Path, expected: dict[str, int]):
    world = WorldState()
    import_fmg_snapshot(world, path)
    actual = {
        collection: sum(
            entity["fmg"]["collection"] == collection for entity in world.entities.values()
        )
        for collection in expected
    }
    assert actual == expected


def test_new_provisional_golden_entity_ids():
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    assert "river:a64a95346796" in world.entities
    assert "route:da77c3b54be0" in world.entities
    assert "marker:fef0729f0d7f" in world.entities


@pytest.mark.parametrize("path,expected", EXPECTED_NEW_REF_TOTALS.items())
def test_new_reference_resolution_totals(path: Path, expected: dict[str, int]):
    world = WorldState()
    import_fmg_snapshot(world, path)
    entities = world.entities
    assert sum(
        len(entity["refs"].get("cells", []))
        for entity in entities.values()
        if entity["fmg"]["collection"] == "rivers"
    ) == expected["rivers"]
    assert sum(
        len(entity["refs"].get("cells", []))
        for entity in entities.values()
        if entity["fmg"]["collection"] == "routes"
    ) == expected["routes"]
    assert sum(
        "cell" in entity["refs"]
        for entity in entities.values()
        if entity["fmg"]["collection"] == "markers"
    ) == expected["markers"]


@pytest.mark.parametrize("path", [THIMALAND, PITHIGY, VIVERIA])
def test_river_ids_are_explicit_and_sparse(path: Path):
    world = WorldState()
    import_fmg_snapshot(world, path)
    rivers = [
        entity for entity in world.entities.values()
        if entity["fmg"]["collection"] == "rivers"
    ]
    assert all(entity["fmg"]["id"] == entity["attributes"]["i"] for entity in rivers)
    assert all(entity["fmg"]["id"] != entity["fmg"]["position"] for entity in rivers)


def test_pithigy_river_sentinels_are_anomalies_only():
    world = WorldState()
    import_fmg_snapshot(world, PITHIGY)
    report = world.observations["fmg.import.report"]["entities"]["anomalies"]
    rivers = [
        entity for entity in world.entities.values()
        if entity["fmg"]["collection"] == "rivers"
    ]
    assert sum(len(entity["refs"].get("cells", [])) for entity in rivers) == 686
    assert all(
        ref["index"] != -1
        for entity in rivers
        for ref in entity["refs"].get("cells", [])
    )
    assert sum(
        count
        for path, count in report["counts"]["sentinel"].items()
        if path.startswith("pack.rivers[") and ".cells[" in path
    ) == 3


def test_new_collections_have_no_dropped_keys():
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    dropped = world.observations["fmg.import.report"]["entities"]["dropped_keys"]
    assert dropped["rivers"] == {}
    assert dropped["routes"] == {}
    assert dropped["markers"] == {}


def test_route_points_keep_raw_attributes_and_resolve_third_item():
    data = {
        "pack": {
            "cells": [{}],
            "states": [], "provinces": [], "burgs": [], "cultures": [], "religions": [],
            "rivers": [], "markers": [],
            "routes": [{"i": 0, "points": [[1, 2, 0]]}],
        }
    }
    entities, report = build_entities(data)
    route = entities["route:da77c3b54be0"]
    assert route["attributes"]["points"] == [[1, 2, 0]]
    assert route["refs"]["cells"] == [{"space": "pack.cells", "index": 0}]
    assert report["anomalies"]["total"] == 0


def test_malformed_route_points_and_mesh_sentinels_are_tolerated():
    data = {
        "pack": {
            "cells": [{}],
            "states": [], "provinces": [], "burgs": [], "cultures": [], "religions": [],
            "rivers": [{"i": 1, "cells": [0, -1, 0]}],
            "routes": [
                {"i": 0, "points": "not-a-list"},
                {"i": 1, "points": [[1, 2]]},
                {"i": 2, "points": [[1, 2, "x"]]},
            ],
            "markers": [{"i": 0, "cell": "x"}],
        }
    }
    entities, report = build_entities(data)
    assert all("cells" not in entity["refs"] for entity in entities.values() if entity["fmg"]["collection"] == "routes")
    river = next(
        entity for entity in entities.values()
        if entity["fmg"]["collection"] == "rivers" and entity["fmg"]["id"] == 1
    )
    assert river["refs"]["cells"] == [
        {"space": "pack.cells", "index": 0},
        {"space": "pack.cells", "index": 0},
    ]
    assert "cell" not in next(
        entity["refs"] for entity in entities.values() if entity["fmg"]["collection"] == "markers"
    )
    counts = report["anomalies"]["counts"]
    assert sum(counts["invalid-type"].values()) == 4
    assert sum(counts["sentinel"].values()) == 1
    invalid_paths = [
        path for path, count in counts["invalid-type"].items() for _ in range(count)
    ]
    assert "pack.routes[0].points" in invalid_paths
    assert "pack.routes[1].points[0]" in invalid_paths
    assert "pack.routes[2].points[0][2]" in invalid_paths
    assert "pack.markers[0].cell" in invalid_paths


def test_new_collection_order_independence(monkeypatch):
    data = {
        "pack": {
            "states": [], "provinces": [], "burgs": [], "cultures": [], "religions": [],
            "rivers": [{"i": 1, "cells": [0]}],
            "routes": [{"i": 0, "points": [[1, 2, 0]]}],
            "markers": [{"i": 0, "cell": 0}],
            "cells": [{}],
        }
    }
    entities_a, report_a = build_entities(data)
    monkeypatch.setattr(
        entities_module,
        "COLLECTION_SPECS",
        dict(reversed(list(entities_module.COLLECTION_SPECS.items()))),
    )
    entities_b, report_b = build_entities(data)
    assert entities_a == entities_b
    assert report_a == report_b


def test_new_collection_duplicate_i_aborts_without_writes(tmp_path: Path):
    raw = json.loads(THIMALAND.read_text(encoding="utf-8"))
    raw["pack"]["rivers"].append(deepcopy(raw["pack"]["rivers"][0]))
    path = tmp_path / "duplicate-river.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    world = WorldState()
    with pytest.raises(ValueError, match="Duplicate explicit FMG i in pack.rivers"):
        import_fmg_snapshot(world, path)
    assert not world.fields
    assert not world.entities
    assert not world.observations
    assert not world.provenance


def test_mesh_reference_out_of_range_is_anomaly_for_each_mesh_collection():
    data = {
        "pack": {
            "cells": [{}],
            "states": [{"i": 0}],
            "provinces": [0, {"i": 1, "state": 0, "center": 9}],
            "burgs": [0, {"i": 1, "cell": -2, "state": 0}],
            "cultures": [], "religions": [],
            "rivers": [{"i": 1, "cells": [0, 1, -2]}],
            "routes": [{"i": 0, "points": [[1, 2, 1], [3, 4, -2]]}],
            "markers": [{"i": 0, "cell": 2}],
        }
    }
    entities, report = build_entities(data)
    assert "center" not in entities["province:5e8c030b494a"]["refs"]
    assert "cell" not in entities["burg:624f67d66cae"]["refs"]
    assert entities["river:a64a95346796"]["refs"]["cells"] == [
        {"space": "pack.cells", "index": 0}
    ]
    assert "cells" not in entities["route:da77c3b54be0"]["refs"]
    assert "cell" not in entities["marker:fef0729f0d7f"]["refs"]
    paths = report["anomalies"]["counts"]["out-of-range"]
    assert paths["pack.provinces[1].center"] == 1
    assert paths["pack.burgs[1].cell"] == 1
    assert paths["pack.rivers[0].cells[1]"] == 1
    assert paths["pack.rivers[0].cells[2]"] == 1
    assert paths["pack.routes[0].points[0][2]"] == 1
    assert paths["pack.routes[0].points[1][2]"] == 1
    assert paths["pack.markers[0].cell"] == 1


def test_lone_surrogate_is_sanitized_recursively_and_persists(tmp_path: Path):
    from worldloom.core.persistence import load_world, save_world

    high = chr(0xD802)
    low_key = chr(0xD803)
    low_value = chr(0xD804)
    route_value = chr(0xD805)
    nested_value = chr(0xD807)
    data = {
        "pack": {
            "cells": [{}],
            "states": [], "provinces": [], "burgs": [], "cultures": [], "religions": [],
            "rivers": [],
            "routes": [{"i": 0, "name": "route " + high, "meta": {low_key: "value " + low_value}}],
            "markers": [{"i": 0, "icon": "marker " + route_value, "nested": ["ok " + nested_value]}],
        }
    }
    source = _write_hand_built_source(tmp_path, data)
    world = WorldState()
    import_fmg_snapshot(world, source)
    route = world.entities["route:da77c3b54be0"]
    marker = world.entities["marker:fef0729f0d7f"]
    assert route["attributes"]["name"] == "route " + chr(0xFFFD)
    assert route["attributes"]["meta"] == {chr(0xFFFD): "value " + chr(0xFFFD)}
    assert marker["attributes"]["icon"] == "marker " + chr(0xFFFD)
    assert marker["attributes"]["nested"] == ["ok " + chr(0xFFFD)]
    counts = world.observations["fmg.import.report"]["entities"]["anomalies"]["counts"]["lone-surrogate"]
    assert counts["pack.routes[0].name"] == 1
    assert counts["pack.routes[0].meta.{key}"] == 1
    assert counts["pack.routes[0].meta." + chr(0xFFFD)] == 1
    assert counts["pack.markers[0].icon"] == 1
    assert counts["pack.markers[0].nested[0]"] == 1
    assert fingerprint(world.entities)

    emoji_data = {
        "pack": {
            "cells": [{}],
            "states": [], "provinces": [], "burgs": [], "cultures": [], "religions": [],
            "rivers": [], "routes": [{"i": 0, "name": "😀"}],
            "markers": [],
        }
    }
    emoji_entities, emoji_report = build_entities(emoji_data)
    assert emoji_entities["route:da77c3b54be0"]["attributes"]["name"] == "😀"
    assert "lone-surrogate" not in emoji_report["anomalies"]["counts"]

    path = tmp_path / "sanitized.json"
    save_world(world, path)
    loaded = load_world(path)
    assert loaded.entities == world.entities
    assert loaded.fingerprint(loaded.entities) == fingerprint(world.entities)


def _write_hand_built_source(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "hand-built.json"
    path.write_text(json.dumps(data, ensure_ascii=True), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "path,expected",
    [(THIMALAND, 1), (PITHIGY, 2), (VIVERIA, 1)],
)
def test_observed_lone_surrogate_anomaly_counts(path: Path, expected: int):
    world = WorldState()
    import_fmg_snapshot(world, path)
    counts = world.observations["fmg.import.report"]["entities"]["anomalies"]["counts"]
    assert sum(counts.get("lone-surrogate", {}).values()) == expected
