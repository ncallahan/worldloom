"""Direct regression tests for tolerated FMG entity-builder edge cases."""

from copy import deepcopy

import pytest

from worldloom.adapters.fmg import entities as entities_module
from worldloom.adapters.fmg.entities import (
    COLLECTION_SPECS,
    REFERENCE_SPECS,
    build_entities,
)


COLLECTIONS = tuple(COLLECTION_SPECS)
REFERENCE_CASES = [
    (collection, field, target, mesh)
    for collection, fields in REFERENCE_SPECS.items()
    for field, (target, mesh) in fields.items()
]


def _base_data():
    return {
        "pack": {
            "cells": [{}, {}],
            "states": [{"i": 0, "neighbors": [0], "provinces": [1]}],
            "provinces": [0, {"i": 1, "state": 0, "center": 0}],
            "burgs": [0, {"i": 1, "cell": 0, "state": 0}],
            "cultures": [{"i": 0}],
            "religions": [{"i": 0}],
            "rivers": [{"i": 1, "cells": [0]}],
            "routes": [{"i": 0, "points": [[1, 2, 0]]}],
            "markers": [{"i": 0, "cell": 0}],
        }
    }


def _anomaly_count(report, kind, path):
    return report["anomalies"]["counts"].get(kind, {}).get(path, 0)


@pytest.mark.parametrize("collection", COLLECTIONS)
def test_non_dict_record_is_reported_and_skipped(collection):
    data = _base_data()
    data["pack"][collection] = ["not-a-record"]

    entities, report = build_entities(data)

    assert report["entity_counts"][collection] == 0
    assert _anomaly_count(report, "invalid-type", f"pack.{collection}[0]") == 1
    assert not any(
        entity["fmg"]["collection"] == collection for entity in entities.values()
    )


@pytest.mark.parametrize("bad_id", ["missing", "string", "bool", "none"])
def test_malformed_explicit_ids_are_reported_and_skipped(bad_id):
    data = _base_data()
    record = {"name": "invalid"}
    if bad_id != "missing":
        record["i"] = {"string": "bad", "bool": True, "none": None}[bad_id]
    data["pack"]["states"] = [record]

    entities, report = build_entities(data)

    assert not entities
    assert report["entity_counts"]["states"] == 0
    assert _anomaly_count(report, "invalid-type", "pack.states[0].i") == 1


@pytest.mark.parametrize("collection", COLLECTIONS)
def test_duplicate_explicit_ids_abort_with_exact_message(collection):
    data = _base_data()
    data["pack"][collection] = [{"i": 17}, {"i": 17}]

    with pytest.raises(
        ValueError,
        match=rf"^Duplicate explicit FMG i in pack\.{collection}: 17$",
    ):
        build_entities(data)


@pytest.mark.parametrize("bad_value", ["not-a-list", None])
def test_non_list_collection_value_handling(bad_value):
    data = _base_data()
    data["pack"]["states"] = bad_value

    if bad_value is None:
        entities, report = build_entities(data)
        assert report["entity_counts"]["states"] == 0
        assert not any(
            entity["fmg"]["collection"] == "states" for entity in entities.values()
        )
    else:
        with pytest.raises(ValueError, match=r"^FMG pack\.states must be a list$"):
            build_entities(data)


@pytest.mark.parametrize("collection", COLLECTIONS)
def test_absent_collection_is_treated_as_empty(collection):
    data = _base_data()
    data["pack"].pop(collection)

    _entities, report = build_entities(data)

    assert report["entity_counts"][collection] == 0
    assert report["anomalies"]["total"] == 0


@pytest.mark.parametrize(
    "collection,field,target,mesh", REFERENCE_CASES
)
@pytest.mark.parametrize("value", [-1, 99, 0, "x", True])
@pytest.mark.parametrize("as_list", [False, True])
def test_reference_values_have_direct_expected_outcomes(
    collection, field, target, mesh, value, as_list
):
    data = _base_data()
    position = {
        "states": 0,
        "provinces": 1,
        "burgs": 1,
        "rivers": 0,
        "markers": 0,
    }[collection]
    record = data["pack"][collection][position]
    record[field] = [value] if as_list else value
    path = f"pack.{collection}[{position}].{field}"
    if as_list:
        path += "[0]"

    _entities, report = build_entities(data)

    if not isinstance(value, int) or isinstance(value, bool):
        expected_kind = "invalid-type"
    elif value == -1:
        expected_kind = "sentinel"
    elif value == 99:
        expected_kind = "out-of-range" if mesh else "unresolved-reference"
    elif collection == "states" and field == "provinces":
        expected_kind = "placeholder-reference"
    else:
        expected_kind = None

    if expected_kind is None:
        assert report["anomalies"]["total"] == 0
    else:
        assert _anomaly_count(report, expected_kind, path) == 1
        assert report["anomalies"]["total"] == 1


def test_missing_pack_cells_makes_mesh_references_out_of_range():
    data = _base_data()
    data["pack"].pop("cells")
    data["pack"]["provinces"][1]["center"] = 0
    data["pack"]["burgs"][1]["cell"] = 0

    _entities, report = build_entities(data)

    counts = report["anomalies"]["counts"]["out-of-range"]
    assert counts["pack.provinces[1].center"] == 1
    assert counts["pack.burgs[1].cell"] == 1


def test_empty_pack_has_zero_counts_and_no_anomalies():
    _entities, report = build_entities({"pack": {}})

    assert report["entity_counts"] == {collection: 0 for collection in COLLECTIONS}
    assert report["anomalies"] == {"counts": {}, "examples": [], "total": 0}


def test_forced_derived_id_collision_raises_exact_error(monkeypatch):
    data = _base_data()
    data["pack"]["states"] = [{"i": 1}, {"i": 2}]
    monkeypatch.setattr(
        entities_module, "derive_entity_id", lambda *_args: "state:constant"
    )

    with pytest.raises(
        ValueError, match=r"^Derived entity ID collision: state:constant$"
    ):
        build_entities(data)
