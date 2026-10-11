from __future__ import annotations

from copy import deepcopy
import math
from pathlib import Path

import pytest

from worldloom.adapters.fmg import import_fmg_snapshot
from worldloom.core import WorldState, derive_entity_id
from worldloom.core.hashing import fingerprint
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


def test_same_seed_different_seed_order_independence_and_stable_slot_ids():
    base = imported()
    ids = burg_ids(base)
    forward, reverse = deepcopy(base), deepcopy(base)
    resolve_burg_wards(forward, 123, burgs=ids)
    resolve_burg_wards(reverse, 123, burgs=reversed(ids))
    assert forward.entities == reverse.entities
    assert forward.observations == reverse.observations
    assert forward.events == reverse.events

    other = deepcopy(base)
    resolve_burg_wards(other, 124, burgs=ids)
    assert {k: v["attributes"]["population"] for k, v in wards(forward).items()} != {
        k: v["attributes"]["population"] for k, v in wards(other).items()
    }
    burg_id = ids[0]
    slot_id = derive_entity_id(
        "ward", "question:burg.wards", f"burg:{burg_id}", "slot:001"
    )
    assert slot_id in wards(forward, burg_id)
    assert slot_id in wards(other, burg_id)


def test_imported_canon_and_burg_fingerprints_never_change():
    world = imported()
    canon = deepcopy(world.entities)
    before = {key: fingerprint(world.entities[key]) for key in burg_ids(world)}
    resolve_burg_wards(world, "stable")
    assert all(world.entities[key] == value for key, value in canon.items())
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
            config = world.provenance[ward_id].configuration
            assert config["seed"] == 44
            assert config["producer"] == "worldloom.detail.burg_wards"
            assert config["version"] == "0.1.0"
            assert config["resolved_total"] == total
            assert config["burg_fingerprint"] == fingerprint(world.entities[burg_id])
            assert entity["local_detail"]["parent_burg_id"] == burg_id
            assert entity["local_detail"]["slot"] >= 1


def test_prior_is_not_rewritten_and_controls_later_draw_parameters():
    burg_id = burg_ids(imported())[0]
    world = imported()
    resolve_burg_wards(world, 1, burgs=[burg_id], burg_sigma=0.1)
    original = deepcopy(world.observations[PRIOR_KEY][burg_id])
    fresh = imported()
    fresh.observations[PRIOR_KEY] = {burg_id: original}
    resolve_burg_wards(fresh, 2, burgs=[burg_id], burg_sigma=0.4)
    assert fresh.observations[PRIOR_KEY][burg_id] == original
    assert world.observations[PRIOR_KEY][burg_id]["mu"] == pytest.approx(
        math.log(original["claim"]) - 0.1**2 / 2
    )


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
    claims = {}
    for key in burg_ids(world):
        claim = world.entities[key]["attributes"].get("population")
        if (
            isinstance(claim, (int, float)) and not isinstance(claim, bool)
            and math.isfinite(claim) and claim > 0
        ):
            claims[key] = claim
    resolve_burg_wards(world, "pithigy-statistical-check")
    ratios = [
        resolution(world, key).data["resolved_total"] / claim
        for key, claim in claims.items()
    ]
    tolerance = 4 * math.sqrt((math.exp(0.15**2) - 1) / len(ratios))
    assert abs(sum(ratios) / len(ratios) - 1) <= tolerance
