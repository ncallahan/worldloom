from __future__ import annotations

from copy import deepcopy
import math
from pathlib import Path

import pytest

from worldloom.adapters.fmg import import_fmg_snapshot
from worldloom.core import WorldState, derive_entity_id
from worldloom.core.hashing import fingerprint
from worldloom.core.persistence import load_world, save_world
from worldloom.adapters.markdown_vault import export_markdown_vault
from worldloom.detail.burg_wards import (
    LAYERING_KEY, PRIOR_KEY, QUESTION_ID, resolve_burg_wards,
)

ROOT = Path(__file__).parents[2]
THIMALAND = ROOT / "examples" / "Thimaland Full 2026-10-02-14-17.json"
PITHIGY = ROOT / "examples" / "Pithigy Full 2026-10-02-11-35.json"


def imported(path=THIMALAND):
    world = WorldState()
    import_fmg_snapshot(world, path)
    return world


def burg_ids(world):
    return sorted(
        key for key, entity in world.entities.items()
        if entity.get("fmg", {}).get("collection") == "burgs"
    )


def wards(world, burg_id=None):
    return {
        key: entity for key, entity in world.entities.items()
        if entity.get("kind") == "ward"
        and (burg_id is None or entity["refs"]["burg"] == burg_id)
    }


def resolution(world, burg_id):
    return next(
        event for event in world.events
        if event.kind == "local_detail.resolved"
        and event.data.get("entity_id") == burg_id
        and event.data.get("question_id") == QUESTION_ID
    )


def test_same_seed_split_call_order_independence_and_stable_slot_ids():
    base = imported()
    ids = burg_ids(base)
    subset_a, subset_b = ids[::2], ids[1::2]
    a_then_b, b_then_a = deepcopy(base), deepcopy(base)
    resolve_burg_wards(a_then_b, 123, burgs=subset_a)
    resolve_burg_wards(a_then_b, 123, burgs=subset_b)
    resolve_burg_wards(b_then_a, 123, burgs=subset_b)
    resolve_burg_wards(b_then_a, 123, burgs=subset_a)

    assert wards(a_then_b) == wards(b_then_a)
    ward_provenance = lambda world: {
        key: value for key, value in world.provenance.items()
        if key.startswith("entity:ward:")
    }
    assert ward_provenance(a_then_b) == ward_provenance(b_then_a)
    totals = lambda world: {
        event.data["entity_id"]: event.data["resolved_total"]
        for event in world.events
        if event.kind == "local_detail.resolved"
        and event.data.get("question_id") == QUESTION_ID
    }
    assert totals(a_then_b) == totals(b_then_a)
    assert a_then_b.observations[PRIOR_KEY] == b_then_a.observations[PRIOR_KEY]

    other = deepcopy(base)
    resolve_burg_wards(other, 124, burgs=ids)
    assert {k: v["attributes"]["population"] for k, v in wards(a_then_b).items()} != {
        k: v["attributes"]["population"] for k, v in wards(other).items()
    }
    burg_id = ids[0]
    slot_id = derive_entity_id(
        "ward", "question:burg.wards", f"burg:{burg_id}", "slot:001"
    )
    assert slot_id in wards(a_then_b, burg_id)
    assert slot_id in wards(other, burg_id)


def test_imported_canon_and_burg_fingerprints_never_change():
    world = imported()
    canon_entities = deepcopy(world.entities)
    canon_fields = deepcopy(world.fields)
    import_report = deepcopy(world.observations["fmg.import.report"])
    canon_provenance = deepcopy(world.provenance)
    before = {key: fingerprint(world.entities[key]) for key in burg_ids(world)}
    resolve_burg_wards(world, "stable")
    assert all(world.entities.get(key) == value for key, value in canon_entities.items())
    assert world.fields == canon_fields
    assert world.observations["fmg.import.report"] == import_report
    assert all(world.provenance[key] == value for key, value in canon_provenance.items())
    assert {key: fingerprint(world.entities[key]) for key in before} == before


def test_reresolving_is_noop_for_entities_and_events():
    world = imported()
    resolve_burg_wards(world, 10)
    entities, events = deepcopy(world.entities), list(world.events)
    result = resolve_burg_wards(world, 999)
    assert result["resolved"] == 0
    assert result["already_resolved"] == len(burg_ids(world))
    assert world.entities == entities
    assert world.events == events


def test_ward_values_sum_to_event_total_and_provenance_records_inputs():
    world = imported()
    original_burgs = burg_ids(world)
    resolve_burg_wards(world, 44)
    for burg_id in original_burgs:
        total = resolution(world, burg_id).data["resolved_total"]
        entries = wards(world, burg_id)
        assert math.isclose(
            sum(e["attributes"]["population"] for e in entries.values()),
            total, rel_tol=1e-9,
        )
        for ward_id, entity in entries.items():
            ward_provenance = world.provenance[f"entity:{ward_id}"]
            config = ward_provenance.configuration
            assert ward_provenance.fingerprint == fingerprint(entity)
            assert config["seed"] == 44
            assert config["producer"] == "worldloom.detail.burg_wards"
            assert config["version"] == "0.1.0"
            assert config["resolved_total"] == total
            assert config["burg_fingerprint"] == fingerprint(world.entities[burg_id])
            assert entity["local_detail"]["parent_burg_id"] == burg_id
            assert entity["local_detail"]["slot"] >= 1


def test_prior_is_not_rewritten_and_controls_later_draw_parameters():
    burg_id = burg_ids(imported())[0]
    original_world = imported()
    resolve_burg_wards(original_world, 1, burgs=[burg_id], burg_sigma=0.1)
    original = deepcopy(original_world.observations[PRIOR_KEY][burg_id])

    carrying_prior = imported()
    carrying_prior.set_observation(
        PRIOR_KEY, {burg_id: original},
        original_world.provenance[f"observation:{PRIOR_KEY}"],
    )
    resolve_burg_wards(carrying_prior, 2, burgs=[burg_id], burg_sigma=0.4)

    fresh_sigma = imported()
    resolve_burg_wards(fresh_sigma, 2, burgs=[burg_id], burg_sigma=0.1)
    assert carrying_prior.observations[PRIOR_KEY][burg_id] == original
    assert carrying_prior.observations[PRIOR_KEY][burg_id]["mu"] == pytest.approx(
        math.log(original["claim"]) - 0.1**2 / 2
    )
    assert resolution(carrying_prior, burg_id).data["resolved_total"] == (
        resolution(fresh_sigma, burg_id).data["resolved_total"]
    )
    ward_prov = carrying_prior.provenance[
        f"entity:{next(iter(wards(carrying_prior, burg_id)))}"
    ]
    assert ward_prov.configuration["burg_sigma"] == 0.1


def test_prior_claim_is_not_refreshed_if_burg_claim_changes():
    world = imported()
    burg_id = burg_ids(world)[0]
    resolve_burg_wards(world, 17, burgs=[burg_id], burg_sigma=0.1)
    prior = deepcopy(world.observations[PRIOR_KEY][burg_id])
    unresolved = imported()
    unresolved.set_observation(PRIOR_KEY, {burg_id: prior})
    unresolved.entities[burg_id]["attributes"]["population"] += 123
    resolve_burg_wards(unresolved, 18, burgs=[burg_id], burg_sigma=0.4)
    assert unresolved.observations[PRIOR_KEY][burg_id]["claim"] == prior["claim"]


@pytest.mark.parametrize(
    "population,reason",
    [
        (0, "non-positive-population"),
        (-1, "non-positive-population"),
        (float("nan"), "non-finite-population"),
        ("bad", "non-numeric-population"),
        (None, "non-numeric-population"),
    ],
)
def test_invalid_claims_skip_with_reason(population, reason):
    entity = {
        "fmg": {"collection": "burgs", "id": 1},
        "attributes": {"i": 1, "population": population, "state": 1},
        "refs": {},
    }
    world = WorldState(entities={"burg:test": entity})
    result = resolve_burg_wards(world, 1)
    assert result["resolved"] == 0
    assert result["skipped"] == [{"burg_id": "burg:test", "reason": reason}]


def test_missing_claim_and_layering_check_are_reported():
    world = WorldState(entities={
        "state:test": {
            "fmg": {"collection": "states", "id": 1},
            "attributes": {"i": 1, "urban": 4.0}, "refs": {},
        },
        "burg:one": {
            "fmg": {"collection": "burgs", "id": 1},
            "attributes": {"i": 1, "state": 1, "population": 4.0}, "refs": {},
        },
        "burg:missing": {
            "fmg": {"collection": "burgs", "id": 2},
            "attributes": {"i": 2, "state": 1}, "refs": {},
        },
    })
    result = resolve_burg_wards(world, 3)
    assert result["resolved"] == 1
    assert result["skipped"] == [
        {"burg_id": "burg:missing", "reason": "missing-population"}
    ]
    check = world.observations[LAYERING_KEY]["state:test"]
    resolved_sum = sum(
        event.data["resolved_total"]
        for event in world.events
        if event.kind == "local_detail.resolved"
        and event.data.get("question_id") == QUESTION_ID
        and world.entities[event.data["entity_id"]]["attributes"].get("state") == 1
    )
    assert check["urban_claim"] == 4.0
    assert check["resolved_burg_sum"] == resolved_sum
    assert check["burgs_covered"] == 1
    assert check["burgs_total"] == 2
    assert check["relative_difference"] == pytest.approx((resolved_sum - 4.0) / 4.0)


def test_pithigy_mean_resolved_over_claim_within_sampling_tolerance():
    world = imported(PITHIGY)
    claims = {
        key: world.entities[key]["attributes"]["population"]
        for key in burg_ids(world)
    }
    result = resolve_burg_wards(world, "pithigy-statistical-check")
    assert result["skipped"] == []
    ratios = [
        resolution(world, key).data["resolved_total"] / claim
        for key, claim in claims.items()
    ]
    tolerance = 4 * math.sqrt((math.exp(0.15**2) - 1) / len(ratios))
    assert abs(sum(ratios) / len(ratios) - 1) <= tolerance


@pytest.mark.parametrize("source", [THIMALAND, PITHIGY])
def test_real_import_layering_check_matches_independent_state_burg_sums(source):
    world = imported(source)
    original_entities = deepcopy(world.entities)
    result = resolve_burg_wards(world, f"layering-{source.stem}")
    assert result["skipped"] == []

    states = {
        entity["attributes"]["i"]: (entity_id, entity)
        for entity_id, entity in original_entities.items()
        if entity.get("fmg", {}).get("collection") == "states"
        and isinstance(entity.get("attributes"), dict)
        and "i" in entity["attributes"]
    }
    burgs = {
        entity_id: entity for entity_id, entity in original_entities.items()
        if entity.get("fmg", {}).get("collection") == "burgs"
    }
    event_totals = {
        event.data["entity_id"]: event.data["resolved_total"]
        for event in world.events
        if event.kind == "local_detail.resolved"
        and event.data.get("question_id") == QUESTION_ID
    }
    check = world.observations[LAYERING_KEY]
    expected_count_sum = 0
    for state_index, (state_id, state) in states.items():
        state_burgs = [
            burg_id for burg_id, burg in burgs.items()
            if burg.get("attributes", {}).get("state") == state_index
        ]
        expected_count_sum += len(state_burgs)
        resolved_sum = sum(event_totals[burg_id] for burg_id in state_burgs)
        state_check = check[state_id]
        assert state_check["burgs_total"] == len(state_burgs)
        assert state_check["burgs_covered"] == state_check["burgs_total"]
        assert state_check["urban_claim"] == state["attributes"].get("urban")
        assert state_check["resolved_burg_sum"] == pytest.approx(resolved_sum)
    assert expected_count_sum == len(burgs)


def test_event_records_seed_and_resolution_parameters():
    world = imported()
    burg_id = burg_ids(world)[0]
    resolve_burg_wards(
        world, "event-seed", burgs=[burg_id], burg_sigma=0.2,
        ward_sigma=0.7, target_ward_size=3.5, max_wards=9,
    )
    event = resolution(world, burg_id)
    assert event.data["seed"] == "event-seed"
    assert event.data["burg_sigma"] == world.observations[PRIOR_KEY][burg_id]["sigma"]
    assert event.data["ward_sigma"] == 0.7
    assert event.data["target_ward_size"] == 3.5
    assert event.data["max_wards"] == 9


def test_persistence_round_trip_and_loaded_resolution_is_noop(tmp_path):
    world = imported()
    resolve_burg_wards(world, "persist-seed")
    path = tmp_path / "worldloom.json"
    save_world(world, path)
    loaded = load_world(path)
    for name in ("entities", "provenance", "events", "observations"):
        assert getattr(loaded, name) == getattr(world, name)
    before = (
        deepcopy(loaded.entities), deepcopy(loaded.provenance),
        deepcopy(loaded.events), deepcopy(loaded.observations),
    )
    result = resolve_burg_wards(loaded, "different-seed")
    assert result["resolved"] == 0
    assert result["already_resolved"] == len(burg_ids(loaded))
    assert (
        loaded.entities, loaded.provenance, loaded.events, loaded.observations
    ) == before


def test_markdown_vault_exporter_handles_ward_reference_without_anomaly(tmp_path):
    world = WorldState(entities={
        "burg:000000000001": {
            "attributes": {"name": "Sample burg", "population": 3.0},
            "refs": {}, "fmg": {"collection": "burgs", "id": 1},
        },
        "ward:000000000002": {
            "kind": "ward", "attributes": {"population": 3.0},
            "refs": {"burg": "burg:000000000001"},
            "local_detail": {"parent_burg_id": "burg:000000000001", "slot": 1},
        },
    })
    summary = export_markdown_vault(world, tmp_path / "vault")
    assert summary is None
    ward_note = tmp_path / "vault" / "ward" / "Unnamed ward (000000000002).md"
    assert ward_note.exists()
    assert "[[burg/Sample burg (000000000001)|Sample burg]]" in ward_note.read_text(
        encoding="utf-8"
    )
