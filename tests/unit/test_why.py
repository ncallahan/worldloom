from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import random

import worldloom.core as core_module
import worldloom.core.rng as core_rng
import worldloom.detail.burg_wards as resolver

from worldloom.adapters.fmg import import_fmg_snapshot
from worldloom.adapters.markdown_vault import export_markdown_vault
from worldloom.cli import main
from worldloom.core import WorldState
from worldloom.core.persistence import load_world, save_world
from worldloom.core.provenance import Provenance
from worldloom.detail.burg_wards import LAYERING_KEY, PRIOR_KEY, resolve_burg_wards
from worldloom.why import build_trace, format_trace

ROOT = Path(__file__).parents[2]
THIMALAND = ROOT / "examples" / "Thimaland Full 2026-10-02-14-17.json"


def _world(tmp_path: Path):
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    state_indices = {
        entity["attributes"]["i"] for entity in world.entities.values()
        if isinstance(entity, dict) and isinstance(entity.get("fmg"), dict)
        and entity["fmg"].get("collection") == "states"
        and isinstance(entity.get("attributes"), dict) and "i" in entity["attributes"]
    }
    burg_id = next(key for key, entity in world.entities.items()
                   if isinstance(entity, dict)
                   and isinstance(entity.get("fmg"), dict)
                   and entity["fmg"].get("collection") == "burgs"
                   and isinstance(entity.get("attributes"), dict)
                   and isinstance(entity["attributes"].get("population"), (int, float))
                   and entity["attributes"]["population"] > 0
                   and entity["attributes"].get("state") in state_indices)
    resolve_burg_wards(world, "why-test", burgs=[burg_id])
    path = tmp_path / "world.json"
    save_world(world, path)
    return load_world(path), path, burg_id


def _wards(world, burg_id):
    return {key: value for key, value in world.entities.items()
            if isinstance(value.get("refs"), dict) and value["refs"].get("burg") == burg_id
            and isinstance(value.get("local_detail"), dict) and "slot" in value["local_detail"]}


def test_trace_records_exact_ward_values_and_is_read_only(tmp_path, monkeypatch):
    world, path, burg_id = _world(tmp_path)
    ward_id, ward = next(iter(_wards(world, burg_id).items()))
    before = deepcopy(world.snapshot())
    config = world.provenance[f"entity:{ward_id}"].configuration
    trace = build_trace(world, ward_id)
    assert trace["ward"]["resolved_draw"]["resolved_total"] == config["resolved_total"]
    assert trace["ward"]["resolution_record"]["seed"] == config["seed"] == "why-test"
    assert trace["ward"]["resolution_record"]["burg_sigma"] == config["burg_sigma"]
    assert trace["ward"]["resolution_record"]["ward_sigma"] == config["ward_sigma"]
    assert trace["ward"]["resolution_record"]["target_ward_size"] == config["target_ward_size"]
    assert trace["ward"]["resolution_record"]["max_wards"] == config["max_wards"]
    assert trace["ward"]["resolved_draw"]["slot"] == ward["local_detail"]["slot"]
    assert trace["ward"]["resolved_draw"]["wards_currently_present"] == len(_wards(world, burg_id))
    assert trace["ward"]["prior"]["claim"] == world.observations[PRIOR_KEY][burg_id]["claim"]
    assert trace["ward"]["prior"]["mu"] == world.observations[PRIOR_KEY][burg_id]["mu"]
    assert trace["ward"]["prior"]["sigma"] == world.observations[PRIOR_KEY][burg_id]["sigma"]
    assert trace["ward"]["layering"] == world.observations[LAYERING_KEY][
        next(key for key, entity in world.entities.items()
             if entity.get("fmg", {}).get("collection") == "states"
             and entity.get("attributes", {}).get("i") == world.entities[burg_id]["attributes"].get("state"))
    ]
    def forbidden(*args, **kwargs):
        raise AssertionError("why must not resolve or draw randomness")
    monkeypatch.setattr(resolver, "resolve_burg_wards", forbidden)
    monkeypatch.setattr(core_rng, "rng_for", forbidden)
    monkeypatch.setattr(core_module, "rng_for", forbidden)
    monkeypatch.setattr(random.Random, "lognormvariate", forbidden)
    assert build_trace(world, ward_id)["kind"] == "ward"
    assert world.snapshot() == before
    file_before = path.read_bytes()
    assert main(["why", str(path), ward_id]) == 0
    assert path.read_bytes() == file_before


def test_staleness_status_values(tmp_path):
    world, _, burg_id = _world(tmp_path)
    ward_id = next(iter(_wards(world, burg_id)))
    prov = world.provenance[f"entity:{ward_id}"]
    assert build_trace(world, ward_id)["ward"]["burg_input_staleness"] == "current"
    world.entities[burg_id]["attributes"]["population"] += 1
    assert build_trace(world, ward_id)["ward"]["burg_input_staleness"] == "stale (input changed since resolution)"
    del world.entities[burg_id]
    assert build_trace(world, ward_id)["ward"]["burg_input_staleness"] == "input missing"
    world, _, burg_id = _world(tmp_path)
    ward_id = next(iter(_wards(world, burg_id)))
    prov = world.provenance[f"entity:{ward_id}"]
    config = deepcopy(prov.configuration)
    config.pop("input_fingerprints")
    world.provenance[f"entity:{ward_id}"] = Provenance(prov.producer, prov.inputs, config, prov.time, prov.fingerprint)
    assert build_trace(world, ward_id)["ward"]["burg_input_staleness"] == "no recorded fingerprint"


def test_unknown_entity_and_unreadable_file_errors(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text("{bad", encoding="utf-8")
    assert main(["why", str(path), "entity:nope"]) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.startswith("error:")
    world, saved, _ = _world(tmp_path)
    assert main(["why", str(saved), "entity:unknown"]) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.startswith("error:")


def test_cycle_guard_and_prior_drift(tmp_path):
    world, _, burg_id = _world(tmp_path)
    ward_id = next(iter(_wards(world, burg_id)))
    current = world.entities[burg_id]["attributes"]["population"]
    world.entities[burg_id]["attributes"]["population"] = current + 1
    trace = build_trace(world, ward_id)
    assert trace["ward"]["prior_claim_comparison"] == "differs"
    world.provenance[f"entity:{burg_id}"] = Provenance(
        "synthetic", (f"entity:{ward_id}",), {}
    )
    trace = build_trace(world, burg_id)
    assert trace["trace"]["inputs"][0]["trace"]["inputs"][0]["trace"]["status"] == "cycle detected"


def test_unresolved_burg_does_not_guess_reason(tmp_path):
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    burg_id = next(key for key, entity in world.entities.items()
                   if entity.get("fmg", {}).get("collection") == "burgs")
    trace = build_trace(world, burg_id)
    assert trace["burg"]["resolution_status"] == "no recorded resolution; reason not recorded"
    assert trace["burg"]["resolution_status"] == "no recorded resolution; reason not recorded"
    assert trace["burg"]["resolution_record"] == "not recorded"



def test_unavailable_fingerprint_and_malformed_records_are_tolerated(tmp_path):
    world, _, burg_id = _world(tmp_path)
    ward_id = next(iter(_wards(world, burg_id)))
    provenance = world.provenance[f"entity:{ward_id}"]
    config = deepcopy(provenance.configuration)
    config["input_fingerprints"][f"entity:{burg_id}"] = "wrong"
    world.provenance[f"entity:{ward_id}"] = Provenance(
        provenance.producer, provenance.inputs, config, provenance.time, provenance.fingerprint
    )
    world.entities[burg_id]["attributes"]["unhashable"] = object()
    assert build_trace(world, ward_id)["ward"]["burg_input_staleness"] == "fingerprint unavailable"
    world.observations[PRIOR_KEY] = "malformed"
    world.observations[LAYERING_KEY] = {"malformed": "row"}
    trace = build_trace(world, ward_id)
    assert trace["ward"]["prior"] == "unreadable"
    state_index = world.entities[burg_id]["attributes"].get("state")
    state_id = next(key for key, entity in world.entities.items()
                    if entity.get("fmg", {}).get("collection") == "states"
                    and entity.get("attributes", {}).get("i") == state_index)
    world.observations[LAYERING_KEY] = {state_id: "malformed"}
    assert build_trace(world, ward_id)["ward"]["layering"] == "unreadable"


def test_cli_bytes_unchanged_and_exact_error_streams(tmp_path, capsys):
    world, path, burg_id = _world(tmp_path)
    before = path.read_bytes()
    ward_id = next(iter(_wards(world, burg_id)))
    assert main(["why", str(path), ward_id]) == 0
    assert path.read_bytes() == before
    capsys.readouterr()
    assert main(["why", str(path), "unknown:entity"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("error:")



def test_missing_event_and_prior_are_reported_without_guessing(tmp_path):
    world, _, burg_id = _world(tmp_path)
    ward_id = next(iter(_wards(world, burg_id)))
    config = world.provenance[f"entity:{ward_id}"].configuration
    world.events = [
        event for event in world.events
        if not (event.kind == "local_detail.resolved"
                and event.data.get("entity_id") == burg_id)
    ]
    world.observations.pop(PRIOR_KEY)
    trace = build_trace(world, ward_id)["ward"]
    assert trace["prior"] == "not recorded"
    assert trace["resolution_record"]["recorded"] is False
    assert trace["resolution_record"]["source"] == "entity provenance"
    assert trace["resolution_record"]["seed"] == config["seed"]
    assert trace["resolution_record"]["recorded"] is False
    assert trace["resolution_record"]["source"] == "entity provenance"
    assert "reason" not in trace["resolution_record"]


def test_lone_surrogate_is_replaced_for_display(tmp_path):
    world, _, burg_id = _world(tmp_path)
    world.entities[burg_id]["attributes"]["name"] = "\ud800"
    rendered = format_trace(build_trace(world, burg_id))
    assert "\ufffd" in rendered
    assert "\ud800" not in rendered



def test_why_staleness_matches_vault_derived_from_line(tmp_path):
    statuses = set()
    for expected in ("current", "stale (input changed since resolution)", "input missing"):
        world, _, burg_id = _world(tmp_path)
        ward_id = next(iter(_wards(world, burg_id)))
        if expected.startswith("stale"):
            world.entities[burg_id]["attributes"]["population"] += 1
        elif expected == "input missing":
            del world.entities[burg_id]
        vault = tmp_path / expected.replace(" ", "-").replace("(", "").replace(")", "")
        export_markdown_vault(world, vault)
        note = next(path for path in vault.rglob("*.md")
                    if f'worldloom_id: "{ward_id}"' in path.read_text(encoding="utf-8"))
        content = note.read_text(encoding="utf-8")
        derived = content.split("## Derived from", 1)[1].split("## Provenance", 1)[0]
        matching = [line.strip() for line in derived.splitlines()
                    if line.strip().endswith(": " + expected)]
        assert len(matching) == 1
        vault_status = matching[0].rsplit(": ", 1)[1]
        trace_status = build_trace(world, ward_id)["ward"]["burg_input_staleness"]
        assert vault_status == trace_status == expected
        statuses.add(vault_status)
    assert statuses == {"current", "stale (input changed since resolution)", "input missing"}
    for expected in ("no recorded fingerprint", "fingerprint unavailable"):
        world, _, burg_id = _world(tmp_path)
        ward_id = next(iter(_wards(world, burg_id)))
        provenance = world.provenance[f"entity:{ward_id}"]
        config = deepcopy(provenance.configuration)
        if expected == "no recorded fingerprint":
            config.pop("input_fingerprints")
        else:
            world.entities[burg_id]["attributes"]["unfingerprintable"] = object()
        world.provenance[f"entity:{ward_id}"] = Provenance(
            provenance.producer, provenance.inputs, config, provenance.time, provenance.fingerprint
        )
        vault = tmp_path / expected.replace(" ", "-")
        export_markdown_vault(world, vault)
        note = next(path for path in vault.rglob("*.md")
                    if f'worldloom_id: "{ward_id}"' in path.read_text(encoding="utf-8"))
        content = note.read_text(encoding="utf-8")
        derived = content.split("## Derived from", 1)[1].split("## Provenance", 1)[0]
        matching = [line.strip() for line in derived.splitlines()
                    if line.strip().endswith(": " + expected)]
        assert len(matching) == 1
        vault_status = matching[0].rsplit(": ", 1)[1]
        trace_status = build_trace(world, ward_id)["ward"]["burg_input_staleness"]
        assert vault_status == trace_status == expected
        statuses.add(vault_status)
    assert statuses == {"current", "stale (input changed since resolution)", "input missing",
                        "no recorded fingerprint", "fingerprint unavailable"}


def _find_import_source(node):
    if isinstance(node, dict):
        if isinstance(node.get("imported_source"), dict):
            source = node["imported_source"]
            if source.get("status") != "not imported by FMG importer":
                return source
        for value in node.values():
            found = _find_import_source(value)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _find_import_source(value)
            if found is not None:
                return found
    return None


def test_imported_source_is_recorded_for_burg_and_ward_parent(tmp_path):
    world, _, burg_id = _world(tmp_path)
    ward_id = next(iter(_wards(world, burg_id)))
    source = world.fields["fmg.source"]
    burg_import = build_trace(world, burg_id)["burg"]["imported_source"]
    ward_parent_import = _find_import_source(build_trace(world, ward_id)["trace"])
    for imported in (burg_import, ward_parent_import):
        assert imported is not None
        assert imported["fmg.source"]["seed"] == source["seed"]
        assert imported["fmg.source"]["fmg_version"] == source["fmg_version"]
        assert imported["fmg.source"]["seed"]
        assert imported["fmg.source"]["fmg_version"]
        assert imported["importer_version"]


def test_why_cli_has_exact_labelled_ward_lines(tmp_path, capsys):
    world, path, burg_id = _world(tmp_path)
    ward_id = next(iter(_wards(world, burg_id)))
    ward = build_trace(world, ward_id)["ward"]
    assert main(["why", str(path), ward_id]) == 0
    output = capsys.readouterr().out.splitlines()
    for heading in ("Claim:", "Prior:", "Resolved draw:", "Resolution record:",
                    "Staleness:", "Layering check:", "Generic provenance chain:"):
        assert heading in output
    assert f"  burg input: {ward['burg_input_staleness']}" in output
    assert f"  seed: {ward['resolution_record']['seed']}" in output
    assert f"  resolved total: {ward['resolved_draw']['resolved_total']}" in output
    assert f"  claim: {ward['prior']['claim']}" in output
    for key, value in ward["layering"].items():
        assert f"  {key.replace('_', ' ')}: {value}" in output
    assert output.index("Claim:") < output.index("Prior:") < output.index("Resolved draw:") < output.index("Resolution record:") < output.index("Staleness:") < output.index("Layering check:") < output.index("Generic provenance chain:")


def test_safe_stringifies_tuple_observation_keys(tmp_path):
    world, _, burg_id = _world(tmp_path)
    world.observations[PRIOR_KEY][burg_id]["extra"] = {(1, 2): "tuple-keyed"}
    rendered = format_trace(build_trace(world, burg_id))
    assert "(1, 2): tuple-keyed" in rendered
