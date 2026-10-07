from copy import deepcopy
import json
from pathlib import Path

import pytest

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
    assert IMPORTER_VERSION == "0.2.0"


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
