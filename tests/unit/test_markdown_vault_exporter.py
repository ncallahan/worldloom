from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from worldloom.adapters import export_markdown_vault
from worldloom.adapters.fmg import import_fmg_snapshot
from worldloom.core import WorldState
from worldloom.core.persistence import load_world, save_world

REPO_ROOT = Path(__file__).parents[2]
THIMALAND = REPO_ROOT / "examples" / "Thimaland Full 2026-10-02-14-17.json"
PITHIGY_SLICE = REPO_ROOT / "experiments" / "fmg_scale" / "slices" / "Pithigy_burg1_hop3.json"
VIVERIA_SLICE = REPO_ROOT / "experiments" / "fmg_scale" / "slices" / "Viveria_burg1_hop3.json"


def _world(*items):
    world = WorldState()
    for entity_id, entity in items:
        world.add_entity(entity_id, entity)
    return world


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _entity(name: str, digest: str) -> tuple[str, dict]:
    return f"test:{digest}", {"attributes": {"name": name}, "refs": {}}


def test_generated_files_order_includes_group_indexes_before_kind_indexes(monkeypatch, tmp_path):
    import worldloom.adapters.markdown_vault.exporter as exporter

    captured = {}

    def capture(root, files, **kwargs):
        captured["keys"] = list(files)

    monkeypatch.setattr(exporter, "write_managed_tree", capture)
    world = _world(
        ("zeta:000000000001", {"attributes": {"name": "Z", "type": "b", "group": "g"}, "refs": {}}),
        ("alpha:000000000002", {"attributes": {"name": "A", "type": "a", "group": "h"}, "refs": {}}),
    )
    world.observations["fmg.import.report"] = {}
    exporter.export_markdown_vault(world, tmp_path / "unused")
    assert captured["keys"] == [
        "zeta/Z (000000000001).md",
        "alpha/A (000000000002).md",
        "indexes/alpha-by-type.md",
        "indexes/alpha-by-group.md",
        "indexes/alpha.md",
        "indexes/zeta-by-type.md",
        "indexes/zeta-by-group.md",
        "indexes/zeta.md",
        "index.md",
        "_worldloom/import.md",
        "_worldloom/anomalies.md",
    ]


@pytest.mark.parametrize("source", [PITHIGY_SLICE, VIVERIA_SLICE], ids=["pithigy-slice", "viveria-slice"])
def test_fmg_slice_exports_are_deterministic_and_save_load_round_trip(tmp_path, source):
    world = WorldState()
    import_fmg_snapshot(world, source)
    first, second = tmp_path / "first", tmp_path / "second"
    export_markdown_vault(world, first)
    export_markdown_vault(world, second)
    first_tree = _tree(first)
    assert first_tree
    assert first_tree == _tree(second)

    saved = tmp_path / "roundtrip.json"
    save_world(world, saved)
    loaded = load_world(saved)
    restored = tmp_path / "restored"
    export_markdown_vault(loaded, restored)
    assert first_tree == _tree(restored)


def test_exporter_rejects_target_file_without_changing_it(tmp_path):
    world = _world(_entity("North", "000000000001"))
    target = tmp_path / "target-file"
    target.write_bytes(b"not a directory")

    with pytest.raises(ValueError, match="Vault target is not a directory"):
        export_markdown_vault(world, target)

    assert target.read_bytes() == b"not a directory"


def test_exporter_rejects_malformed_marker_without_changing_vault(tmp_path):
    world = _world(_entity("North", "000000000001"))
    target = tmp_path / "vault"
    export_markdown_vault(world, target)
    marker = target / ".worldloom-vault.json"
    marker.write_text("{not json", encoding="utf-8")
    before = _tree(target)

    with pytest.raises(ValueError, match="Invalid vault marker"):
        export_markdown_vault(world, target)

    assert _tree(target) == before


def test_exporter_refuses_unlisted_projected_path_without_changes(tmp_path):
    world = _world(_entity("North", "000000000001"))
    target = tmp_path / "vault"
    export_markdown_vault(world, target)

    new_id, new_entity = _entity("Unlisted collision", "000000009999")
    new_world = deepcopy(world)
    new_world.add_entity(new_id, new_entity)
    collision_path = target / "test" / "Unlisted collision (000000009999).md"
    collision_path.parent.mkdir(parents=True, exist_ok=True)
    collision_path.write_bytes(b"foreign")
    before = _tree(target)

    with pytest.raises(ValueError, match=r"Refusing to overwrite unlisted file: test/Unlisted collision"):
        export_markdown_vault(new_world, target)

    assert _tree(target) == before
    assert collision_path.read_bytes() == b"foreign"


def test_exporter_overwrite_edited_changed_world_matches_fresh_tree(tmp_path):
    world = _world(_entity("North", "000000000001"))
    target = tmp_path / "existing"
    export_markdown_vault(world, target)
    old_note = target / "test" / "North (000000000001).md"
    old_note.write_bytes(old_note.read_bytes() + b"manual edit")

    changed = deepcopy(world)
    changed.entities["test:000000000001"]["attributes"]["name"] = "Changed World"
    export_markdown_vault(changed, target, overwrite_edited=True)

    expected = tmp_path / "expected"
    export_markdown_vault(changed, expected)
    assert _tree(target) == _tree(expected)
    assert not old_note.exists()


def test_exporter_removes_stale_note_when_entity_is_removed(tmp_path):
    world = _world(
        _entity("North", "000000000001"),
        _entity("South", "000000000002"),
    )
    target = tmp_path / "existing"
    export_markdown_vault(world, target)
    removed_note = target / "test" / "South (000000000002).md"
    assert removed_note.exists()

    reduced = deepcopy(world)
    reduced.entities.pop("test:000000000002")
    export_markdown_vault(reduced, target)

    expected = tmp_path / "expected"
    export_markdown_vault(reduced, expected)
    assert not removed_note.exists()
    assert _tree(target) == _tree(expected)
    marker = json.loads((target / ".worldloom-vault.json").read_text(encoding="utf-8"))
    assert "test/South (000000000002).md" not in marker["files"]


def test_exporter_failure_injection_restores_tree_at_backup_and_write_positions(tmp_path, monkeypatch):
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    target = tmp_path / "vault"
    export_markdown_vault(world, target)
    before = _tree(target)
    marker = json.loads((target / ".worldloom-vault.json").read_text(encoding="utf-8"))
    backup_count = len(marker["files"]) + 1
    generated_count = len(marker["files"]) + 1

    for phase, positions in (
        ("backup", (1, max(1, backup_count // 2), backup_count)),
        ("write", (
            backup_count + 1,
            backup_count + max(1, generated_count // 2),
            backup_count + generated_count,
        )),
    ):
        for position in positions:
            calls = {"count": 0}
            original_copy2 = shutil.copy2

            def fail_at(source, destination, *args, _position=position, _phase=phase, **kwargs):
                calls["count"] += 1
                if calls["count"] == _position:
                    raise OSError(f"injected {_phase} failure at {_position}")
                return original_copy2(source, destination, *args, **kwargs)

            monkeypatch.setattr(shutil, "copy2", fail_at)
            with pytest.raises(OSError, match=f"injected {phase} failure at {position}"):
                export_markdown_vault(world, target)
            monkeypatch.setattr(shutil, "copy2", original_copy2)
            assert _tree(target) == before
