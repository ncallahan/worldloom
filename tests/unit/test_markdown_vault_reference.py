"""Differential checks against the frozen pre-R1 exporter.

Intentional R1b divergences: (1) rollback removes call-created empty directories;
(2) successful stale-file deletion prunes newly-empty managed directories;
(3) unsafe manifest/new-file paths abort with ValueError before path access;
(4) rollback also handles BaseException, including KeyboardInterrupt. These
behaviours are tested directly in test_markdown_vault_writer.py. The frozen
reference is not edited; differential scenarios unrelated to these divergences
must remain byte-for-byte equivalent.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import unicodedata
from copy import deepcopy
from pathlib import Path

import pytest

from worldloom.adapters.fmg import import_fmg_snapshot
from worldloom.core import WorldState
from worldloom.core.provenance import Provenance

REPO_ROOT = Path(__file__).parents[2]
THIMALAND = REPO_ROOT / "examples" / "Thimaland Full 2026-10-02-14-17.json"
PITHIGY = REPO_ROOT / "examples" / "Pithigy Full 2026-10-02-11-35.json"
VIVERIA = REPO_ROOT / "examples" / "Viveria Full 2026-10-02-11-31.json"
PITHIGY_SLICE = REPO_ROOT / "experiments" / "fmg_scale" / "slices" / "Pithigy_burg1_hop3.json"
VIVERIA_SLICE = REPO_ROOT / "experiments" / "fmg_scale" / "slices" / "Viveria_burg1_hop3.json"

_REF_PATH = Path(__file__).parents[1] / "reference" / "markdown_vault_exporter_ref.py"
_SPEC = importlib.util.spec_from_file_location("worldloom_markdown_vault_exporter_ref", _REF_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_REFERENCE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_REFERENCE)


def _entity(name: str, digest: str, kind: str = "test", refs=None):
    return {"attributes": {"name": name}, "refs": {} if refs is None else refs}, f"{kind}:{digest}"


def _world(*items, fields=None, observations=None, provenance=None):
    world = WorldState(
        fields={} if fields is None else fields,
        observations={} if observations is None else observations,
        provenance={} if provenance is None else provenance,
    )
    for value, entity_id in items:
        world.add_entity(entity_id, value)
    return world


def _tree(root: Path):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _normalise_message(message: str, root: Path) -> str:
    return message.replace(str(root), "<ROOT>")


def _invoke(module, world, root: Path, *, overwrite_edited=False):
    try:
        module.export_markdown_vault(world, root, overwrite_edited=overwrite_edited)
    except Exception as exc:
        return ("exception", type(exc).__name__, _normalise_message(str(exc), root))
    return ("tree", _tree(root))


def _edge_world():
    same_a, same_a_id = _entity(
        "Same",
        "000000000001",
        refs={"z_ref": "place:000000000010", "a_list": ["place:000000000011"]},
    )
    same_b, same_b_id = _entity("Same", "000000000002", refs={"parent": "place:000000000011"})
    same_c, same_c_id = _entity("Same", "000000000003", refs={"parent": "place:000000000010"})
    same_d, same_d_id = _entity("Same", "000000000004")
    place_a, place_a_id = _entity("North", "000000000010", kind="place")
    place_b, place_b_id = _entity("South", "000000000011", kind="place")
    source, source_id = _entity(
        "Source",
        "000000000005",
        refs={
            "single": same_a_id,
            "list": [same_b_id, "missing:test"],
            "mesh": {"space": "pack.cells", "index": 7},
            "dangling": "missing:test",
            "inverse": place_a_id,
        },
    )
    source["attributes"].update(
        {
            "[[Evil]] #tag": "short",
            "long": "L" * 121,
            "multiline": "prefix [[Evil]] #tag | --- " + "`" * 3 + "quoted" + "`" * 3 + "\nsecond line",
            "plain_text": "First line.\nSecond line.",
            "group": "",
            "type": "`edged`",
        }
    )
    unnamed, unnamed_id = _entity("", "000000000006")
    reserved, reserved_id = _entity("CON.txt", "000000000007")
    overlong, overlong_id = _entity("x" * 100, "000000000008")
    nfc, nfc_id = _entity(unicodedata.normalize("NFC", "Cafe\u0301"), "000000000009")
    nfd, nfd_id = _entity(unicodedata.normalize("NFD", "Café"), "000000000012")
    none_value, none_value_id = _entity("None value", "000000000013")
    none_value["attributes"].update({"none_value": None, "x": 1.5})
    none_value["fmg"] = {"collection": "test", "id": None}
    non_dict_refs, non_dict_refs_id = _entity("Non-dict refs", "000000000014")
    non_dict_refs["refs"] = []
    values = [same_a, same_b, same_c, same_d, place_a, place_b, source, unnamed, reserved, overlong, nfc, nfd, none_value, non_dict_refs]
    ids = [same_a_id, same_b_id, same_c_id, same_d_id, place_a_id, place_b_id, source_id, unnamed_id, reserved_id, overlong_id, nfc_id, nfd_id, none_value_id, non_dict_refs_id]
    for index, name in enumerate(["PRN", "AUX", "NUL", "COM1", "LPT1"]):
        value, entity_id = _entity(name, f"{30 + index:012x}")
        value["attributes"]["group"] = "`"
        values.append(value)
        ids.append(entity_id)
    source["attributes"]["group"] = "``x``"
    source["attributes"]["type"] = "[[Evil]]`"
    fields = {"fmg.source": {"name": "edge"}}
    observations = {"fmg.import.report": {"entities": {"entity_counts": {"test": len(values)}}, "diagnostics": {"sentinels_minus_one": "unexpected"}}}
    provenance = {
        f"entity:{source_id}": Provenance(
            producer="edge-test",
            inputs=("input",),
            configuration={"importer_version": "test"},
        ),
        f"entity:{none_value_id}": Provenance(producer="no-importer", configuration={"other": "x"}),
        f"entity:{non_dict_refs_id}": Provenance(producer="empty-config", configuration={})
    }
    return _world(*zip(values, ids), fields=fields, observations=observations, provenance=provenance)


def _fmg_world(path: Path):
    world = WorldState()
    import_fmg_snapshot(world, path)
    return world


def _canonical_scenario(module, tmp_path: Path):
    return [_invoke(module, _fmg_world(source), tmp_path / source.stem)
            for source in (THIMALAND, PITHIGY, VIVERIA, PITHIGY_SLICE, VIVERIA_SLICE)]


def _edge_scenario(module, tmp_path: Path):
    return _invoke(module, _edge_world(), tmp_path / "edge")


def _error_scenarios(module, tmp_path: Path):
    outcomes = []
    outcomes.append(_invoke(module, _world(_entity("Bad", "not-a-valid-id")), tmp_path / "bad-id"))

    collision = _world(_entity("A", "000000000001"), _entity("B", "000000000002"))
    filename_name = "entity_filename" if hasattr(module, "entity_filename") else "_filename"
    original = getattr(module, filename_name)
    try:
        setattr(module, filename_name, lambda entity_id, entity: ("test", "same (000000000000).md"))
        outcomes.append(_invoke(module, collision, tmp_path / "collision"))
    finally:
        setattr(module, filename_name, original)

    bad = "x" + chr(0xD800)
    for location in ("entities", "fields", "observations", "provenance"):
        if location == "entities":
            world = _world(_entity(bad, "000000000013"))
        elif location == "fields":
            world = _world(_entity("Plain", "000000000014"), fields={"fmg.source": {"bad": bad}})
        elif location == "observations":
            world = _world(_entity("Plain", "000000000015"), observations={"fmg.import.report": {"bad": bad}})
        else:
            world = _world(
                _entity("Plain", "000000000016"),
                provenance={"entity:test:000000000016": Provenance(producer=bad)},
            )
        outcomes.append(_invoke(module, world, tmp_path / f"surrogate-{location}"))

    non_json = _world(_entity("Plain", "000000000017"))
    non_json.entities["test:000000000017"]["attributes"]["bad"] = {1, 2}
    outcomes.append(_invoke(module, non_json, tmp_path / "non-json"))
    return outcomes


def _lifecycle_scenario(module, tmp_path: Path):
    world = _fmg_world(THIMALAND)
    root = tmp_path / "lifecycle"
    outcomes = [_invoke(module, world, root), _invoke(module, world, root)]

    edited = next(path for path in root.rglob("*.md") if path.name != "index.md")
    edited.write_bytes(edited.read_bytes() + b"edited")
    outcomes.append(_invoke(module, world, root))
    outcomes.append(_invoke(module, world, root, overwrite_edited=True))

    deleted = next(path for path in root.rglob("*.md") if path.name != "index.md")
    deleted.unlink()
    outcomes.append(_invoke(module, world, root))

    foreign = root / "foreign.md"
    foreign.write_text("keep", encoding="utf-8")
    outcomes.append(_invoke(module, world, root))

    unsafe = tmp_path / "unsafe"
    unsafe.mkdir()
    (unsafe / "foreign.md").write_text("keep", encoding="utf-8")
    outcomes.append(_invoke(module, world, unsafe))

    target_file = tmp_path / "target-file"
    target_file.write_text("not a directory", encoding="utf-8")
    outcomes.append(_invoke(module, world, target_file))

    invalid_marker = tmp_path / "invalid-marker"
    invalid_marker.mkdir()
    (invalid_marker / ".worldloom-vault.json").write_text("{not json", encoding="utf-8")
    outcomes.append(_invoke(module, world, invalid_marker))

    unlisted = tmp_path / "unlisted"
    module.export_markdown_vault(world, unlisted)
    new_world = deepcopy(world)
    new_id = "test:000000009999"
    new_world.add_entity(new_id, {"attributes": {"name": "Unlisted collision"}, "refs": {}})
    new_path = unlisted / "test" / "Unlisted collision (000000009999).md"
    new_path.parent.mkdir(parents=True, exist_ok=True)
    new_path.write_text("foreign", encoding="utf-8")
    outcomes.append(_invoke(module, new_world, unlisted))

    changed = deepcopy(world)
    changed_id = next(iter(changed.entities))
    changed.entities[changed_id]["attributes"]["name"] = "Changed World"
    outcomes.append(_invoke(module, changed, root, overwrite_edited=True))

    removed = deepcopy(world)
    removed_id = next(iter(removed.entities))
    removed.entities.pop(removed_id)
    removed_path = next(path for path in root.rglob("*.md") if removed_id.split(":", 1)[1] in path.name)
    removed_path.unlink()
    outcomes.append(_invoke(module, removed, root, overwrite_edited=True))
    return outcomes


def _failure_scenario(module, tmp_path: Path):
    world = _fmg_world(THIMALAND)
    root = tmp_path / "failure"
    module.export_markdown_vault(world, root)
    before = _tree(root)
    marker = json.loads((root / ".worldloom-vault.json").read_text(encoding="utf-8"))
    backup_count = len(marker["files"]) + 1
    generated_count = len(marker["files"]) + 1
    results = []
    for phase, positions in (
        ("backup", (1, max(1, backup_count // 2), backup_count)),
        ("write", (
            backup_count + 1,
            backup_count + max(1, generated_count // 2),
            backup_count + generated_count,
        )),
    ):
        for position in positions:
            module.export_markdown_vault(world, root)
            calls = {"count": 0}
            original = shutil.copy2

            def fail_at(source, destination, *args, _position=position, **kwargs):
                calls["count"] += 1
                if calls["count"] == _position:
                    raise OSError(f"injected {phase} failure at {_position}")
                return original(source, destination, *args, **kwargs)

            try:
                shutil.copy2 = fail_at
                outcome = _invoke(module, world, root)
            finally:
                shutil.copy2 = original
            after = _tree(root)
            assert after == before
            results.append((phase, position, outcome, after))
    return results


@pytest.mark.parametrize(
    "scenario",
    [_edge_scenario, _canonical_scenario, _error_scenarios, _lifecycle_scenario, _failure_scenario],
    ids=["edge", "canonical-fmg", "errors", "lifecycle", "failure-injection"],
)
def test_reference_and_current_exporter_match(tmp_path, scenario):
    reference = scenario(_REFERENCE, tmp_path / "reference")
    current_module = __import__("worldloom.adapters.markdown_vault.exporter", fromlist=["export_markdown_vault"])
    current = scenario(current_module, tmp_path / "current")
    assert reference == current
