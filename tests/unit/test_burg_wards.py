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
        if key.startswith("ward:") and isinstance(entity.get("local_detail"), dict)
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

    provenance_records = [
        world.provenance[f"entity:{ward_id}"] for ward_id in wards(world)
    ]
    provenance_records.extend([
        world.provenance[f"observation:{PRIOR_KEY}"],
        world.provenance[f"observation:{LAYERING_KEY}"],
    ])
    event_kinds = {event.kind for event in world.events}
    for provenance in provenance_records:
        for input_key in provenance.inputs:
            namespace, separator, key = input_key.partition(":")
            assert separator, f"Unnamespaced provenance input: {input_key}"
            if namespace == "entity":
                assert key in world.entities, input_key
            elif namespace == "observation":
                assert key in world.observations, input_key
            elif namespace == "event":
                assert key in event_kinds, input_key
            else:
                pytest.fail(f"Unexpected provenance input namespace: {input_key}")


def test_prior_observation_is_written_once_per_resolve_call(monkeypatch):
    world = imported()
    original_set_observation = world.set_observation
    prior_writes = []

    def recording_set_observation(name, value, provenance=None):
        if name == PRIOR_KEY:
            prior_writes.append(name)
        return original_set_observation(name, value, provenance)

    monkeypatch.setattr(world, "set_observation", recording_set_observation)
    resolve_burg_wards(world, "single-prior-write")
    assert prior_writes == [PRIOR_KEY]


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


def test_markdown_vault_projection_links_hand_built_ward_to_parent_burg(tmp_path):
    world = WorldState(entities={
        "burg:000000000001": {
            "attributes": {"name": "Sample burg", "population": 3.0},
            "refs": {}, "fmg": {"collection": "burgs", "id": 1},
        },
        "ward:000000000002": {
            "attributes": {"population": 3.0},
            "refs": {"burg": "burg:000000000001"},
            "local_detail": {"parent_burg_id": "burg:000000000001", "slot": 1},
        },
    })
    vault = tmp_path / "vault"
    export_markdown_vault(world, vault)
    ward_note = next((vault / "ward").glob("*.md"))
    assert 'worldloom_kind: "ward"' in ward_note.read_text(encoding="utf-8")
    assert "[[burg/Sample burg (000000000001)|Sample burg]]" in ward_note.read_text(
        encoding="utf-8"
    )


def test_markdown_vault_export_of_resolved_thimaland_preserves_baseline_anomalies(tmp_path):
    world = imported(THIMALAND)
    baseline_vault = tmp_path / "baseline-vault"
    export_markdown_vault(world, baseline_vault)
    baseline_anomalies_note = (
        baseline_vault / "_worldloom" / "anomalies.md"
    ).read_text(encoding="utf-8")
    assert "No anomalies recorded" not in baseline_anomalies_note
    baseline_index = (baseline_vault / "index.md").read_text(encoding="utf-8")

    resolved_world = deepcopy(world)
    import_report_before_resolution = deepcopy(
        resolved_world.observations["fmg.import.report"]
    )
    resolve_burg_wards(resolved_world, "thimaland-vault-check")
    assert (
        resolved_world.observations["fmg.import.report"]
        == import_report_before_resolution
    )

    ward_entities = wards(resolved_world)
    resolved_vault = tmp_path / "resolved-vault"
    export_markdown_vault(resolved_world, resolved_vault)

    resolved_anomalies_note = (
        resolved_vault / "_worldloom" / "anomalies.md"
    ).read_text(encoding="utf-8")
    assert resolved_anomalies_note == baseline_anomalies_note

    resolved_index = (resolved_vault / "index.md").read_text(encoding="utf-8")
    banner_suffix = "(see [[_worldloom/anomalies|anomalies]])"
    baseline_banner_lines = [
        line for line in baseline_index.splitlines()
        if line.endswith(banner_suffix)
    ]
    assert baseline_banner_lines
    resolved_banner_lines = [
        line for line in resolved_index.splitlines()
        if line.endswith(banner_suffix)
    ]
    assert resolved_banner_lines == baseline_banner_lines

    assert not any(
        ward_id in resolved_anomalies_note for ward_id in ward_entities
    )

    note_by_id = {}
    for note in resolved_vault.rglob("*.md"):
        content = note.read_text(encoding="utf-8")
        for line in content.splitlines():
            prefix = 'worldloom_id: "'
            if line.startswith(prefix) and line.endswith('"'):
                entity_id = line[len(prefix):-1]
                if entity_id in resolved_world.entities:
                    note_by_id[entity_id] = note
                break
    ward_notes = {
        entity_id: note_by_id[entity_id]
        for entity_id in ward_entities if entity_id in note_by_id
    }
    assert len(ward_notes) == len(ward_entities)
    assert len(list((resolved_vault / "ward").glob("*.md"))) == len(ward_entities)
    for ward_id, ward in ward_entities.items():
        note = ward_notes[ward_id]
        content = note.read_text(encoding="utf-8")
        parent_id = ward["refs"]["burg"]
        parent_note = note_by_id[parent_id]
        link_target = parent_note.relative_to(resolved_vault).with_suffix("").as_posix()
        assert f"[[{link_target}|" in content, f"{ward_id} lacks parent link to {parent_id}"
        assert "## Derived from" in content
        assert "current" in content
        config = resolved_world.provenance[f"entity:{ward_id}"].configuration
        for key, value in config.items():
            assert str(key) in content
            assert str(value) in content
        assert 'worldloom_kind: "ward"' in content

def test_ward_provenance_input_fingerprint_matches_independent_fingerprint():
    world = imported()
    burg_id = burg_ids(world)[0]
    expected = fingerprint(world.entities[burg_id])
    resolve_burg_wards(world, "fingerprint-test", burgs=[burg_id])
    ward = next(entity_id for entity_id, entity in world.entities.items()
                if entity.get("local_detail", {}).get("parent_burg_id") == burg_id)
    config = world.provenance[f"entity:{ward}"].configuration
    assert config["input_fingerprints"] == {f"entity:{burg_id}": expected}
    assert config["burg_fingerprint"] == expected


def test_vault_reports_changed_and_missing_ward_inputs(tmp_path):
    world = imported()
    burg_id = burg_ids(world)[0]
    resolve_burg_wards(world, "staleness-test", burgs=[burg_id])
    ward_ids = [key for key, entity in wards(world, burg_id).items()]
    assert ward_ids
    unchanged = tmp_path / "unchanged"
    export_markdown_vault(world, unchanged)
    assert all("current" in (unchanged / "ward" / path.name).read_text(encoding="utf-8")
               for path in unchanged.joinpath("ward").glob("*.md"))

    world.entities[burg_id]["attributes"]["population"] += 1
    stale = tmp_path / "stale"
    export_markdown_vault(world, stale)
    assert all("stale (input changed since resolution)" in path.read_text(encoding="utf-8")
               for path in stale.joinpath("ward").glob("*.md"))

    world.entities.pop(burg_id)
    missing = tmp_path / "missing"
    export_markdown_vault(world, missing)
    assert all("input missing" in path.read_text(encoding="utf-8")
               for path in missing.joinpath("ward").glob("*.md"))
