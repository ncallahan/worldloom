"""Direct tests for the managed Markdown-vault tree writer."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from worldloom.adapters.markdown_vault.writer import write_managed_tree

MANIFEST = ".worldloom-vault.json"
HEADER = {"generator": "worldloom", "projection_version": "0.3.1", "world_fingerprint": "known"}


def read_tree(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def tree_state(root: Path):
    if not root.exists():
        return None
    return {
        ".": "directory",
        **{
            path.relative_to(root).as_posix(): (
                ("directory",) if path.is_dir() else ("file", path.read_bytes())
            )
            for path in sorted(root.rglob("*"))
        },
    }


def write(root: Path, files: dict[str, bytes], *, overwrite_edited: bool = False) -> None:
    write_managed_tree(root, files, manifest_name=MANIFEST, manifest_header=HEADER, overwrite_edited=overwrite_edited)


def test_fresh_write_and_identical_rewrite(tmp_path):
    root = tmp_path / "vault"
    files = {"a.md": b"A", "nested/b.md": b"B"}
    write(root, files)
    first = read_tree(root)
    write(root, files)
    assert read_tree(root) == first


def test_changed_content_and_stale_managed_file_removed(tmp_path):
    root = tmp_path / "vault"
    write(root, {"old.md": b"old", "keep.md": b"before"})
    write(root, {"keep.md": b"after", "new.md": b"new"})
    tree = read_tree(root)
    assert "old.md" not in tree
    assert tree["keep.md"] == b"after"
    assert tree["new.md"] == b"new"


def test_foreign_file_preserved(tmp_path):
    root = tmp_path / "vault"
    write(root, {"a.md": b"A"})
    (root / "foreign.md").write_bytes(b"foreign")
    write(root, {"a.md": b"A"})
    assert (root / "foreign.md").read_bytes() == b"foreign"


def test_unlisted_conflicting_file_refused(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    (root / MANIFEST).write_text(json.dumps({"files": {}}), encoding="utf-8")
    (root / "a.md").write_bytes(b"foreign")
    before = read_tree(root)
    with pytest.raises(ValueError, match="Refusing to overwrite unlisted file: a.md"):
        write(root, {"a.md": b"new"})
    assert read_tree(root) == before


def test_non_empty_directory_without_manifest_refused_and_untouched(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    (root / "foreign.md").write_bytes(b"foreign")
    before = read_tree(root)
    with pytest.raises(ValueError, match="Refusing non-empty vault without .worldloom-vault.json"):
        write(root, {"a.md": b"A"})
    assert read_tree(root) == before


def test_invalid_manifest_json(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    (root / MANIFEST).write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid vault marker") as error:
        write(root, {"a.md": b"A"})
    assert isinstance(error.value.__cause__, json.JSONDecodeError)


def test_target_is_file(tmp_path):
    root = tmp_path / "vault"
    root.write_bytes(b"file")
    with pytest.raises(ValueError, match="Vault target is not a directory"):
        write(root, {"a.md": b"A"})
    assert root.read_bytes() == b"file"


def test_hand_edited_managed_file_refused_then_overwritten(tmp_path):
    root = tmp_path / "vault"
    write(root, {"a.md": b"A"})
    (root / "a.md").write_bytes(b"edited")
    with pytest.raises(ValueError, match="Hand-edited generated file: a.md"):
        write(root, {"a.md": b"A"})
    write(root, {"a.md": b"A"}, overwrite_edited=True)
    assert (root / "a.md").read_bytes() == b"A"


def test_deleted_managed_file_regenerated(tmp_path):
    root = tmp_path / "vault"
    write(root, {"a.md": b"A"})
    (root / "a.md").unlink()
    write(root, {"a.md": b"A"})
    assert (root / "a.md").read_bytes() == b"A"


def test_manifest_contents_are_byte_exact(tmp_path):
    root = tmp_path / "vault"
    files = {"z.md": "雪".encode("utf-8"), "a.md": b"A"}
    write(root, files)
    expected_manifest = {
        **HEADER,
        "files": {name: hashlib.sha256(files[name]).hexdigest() for name in sorted(files)},
    }
    expected = (json.dumps(expected_manifest, ensure_ascii=False, indent=2, separators=(",", ": ")) + "\n").encode("utf-8")
    assert (root / MANIFEST).read_bytes() == expected


@pytest.mark.parametrize("existing", [False, True], ids=["fresh", "existing"])
@pytest.mark.parametrize("phase", ["backup", "write"])
@pytest.mark.parametrize("failure_index", ["first", "middle", "last"])
def test_copy_failure_rolls_back_file_set_and_bytes(tmp_path, monkeypatch, existing, phase, failure_index):
    root = tmp_path / "vault"
    initial = {"old/a.md": b"old-a", "old/b.md": b"old-b", "same.md": b"old-same"}
    if existing:
        write(root, initial)
    before = tree_state(root) if existing else None
    next_files = {"same.md": b"new-same", "new/a.md": b"new-a", "new/b.md": b"new-b"}
    # For a fresh tree there are no backup copies; the backup phase has no copy2 calls.
    backup_count = (len(initial) + 1) if existing else 0
    write_count = len(next_files) + 1
    phase_count = backup_count if phase == "backup" else write_count
    if phase == "backup" and not existing:
        pytest.skip("fresh tree has no backup-phase copy2 calls")
    call_index = {"first": 1, "middle": max(1, (phase_count + 1) // 2), "last": phase_count}[failure_index]
    original = shutil.copy2
    calls = {"n": 0}

    def fail_at(source, destination, *args, **kwargs):
        calls["n"] += 1
        if (phase == "backup" and calls["n"] == call_index) or (phase == "write" and calls["n"] == backup_count + call_index):
            raise OSError("injected copy2 failure")
        return original(source, destination, *args, **kwargs)

    monkeypatch.setattr(shutil, "copy2", fail_at)
    with pytest.raises(OSError, match="injected copy2 failure"):
        write(root, next_files)
    assert tree_state(root) == before


def test_failed_fresh_write_removes_created_tree_and_retry_succeeds(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    before = tree_state(root)
    original = shutil.copy2

    def fail_write(source, destination, *args, **kwargs):
        if Path(source).name == "a.md":
            raise OSError("injected first-write failure")
        return original(source, destination, *args, **kwargs)

    monkeypatch.setattr(shutil, "copy2", fail_write)
    with pytest.raises(OSError, match="injected first-write failure"):
        write(root, {"nested/a.md": b"A"})
    assert tree_state(root) == before
    monkeypatch.setattr(shutil, "copy2", original)
    write(root, {"nested/a.md": b"A"})
    assert tree_state(root) == {
        ".": "directory",
        "nested": ("directory",),
        "nested/a.md": ("file", b"A"),
        MANIFEST: ("file", (root / MANIFEST).read_bytes()),
    }


def test_manifest_path_outside_root_is_rejected_without_changes(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    outside = tmp_path / "x"
    outside.write_bytes(b"outside-original")
    marker_path = root / MANIFEST
    marker_path.write_text(json.dumps({"files": {"../x": hashlib.sha256(b"outside-original").hexdigest()}}), encoding="utf-8")
    before_outside = outside.read_bytes()
    before_marker = marker_path.read_bytes()
    before_vault = tree_state(root)
    with pytest.raises(ValueError, match=r"^Invalid vault marker:"):
        write(root, {"a.md": b"A"})
    assert outside.read_bytes() == before_outside
    assert marker_path.read_bytes() == before_marker
    assert tree_state(root) == before_vault


UNSAFE_PATHS = [
    "../x", "a/../../x", "a/../b", "/abs", "C:/x", "a\\b", "", ".", "a//b", "a\x00b",
]


@pytest.mark.parametrize("unsafe", UNSAFE_PATHS)
def test_unsafe_manifest_paths_are_rejected_before_filesystem_changes(tmp_path, unsafe):
    root = tmp_path / "vault"
    root.mkdir()
    marker_path = root / MANIFEST
    marker_path.write_text(json.dumps({"files": {unsafe: "hash"}}), encoding="utf-8")
    before = tree_state(root)
    with pytest.raises(ValueError, match=r"^Invalid vault marker:"):
        write(root, {"a.md": b"A"})
    assert tree_state(root) == before


def test_non_string_manifest_key_is_rejected(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    root.mkdir()
    marker_path = root / MANIFEST
    marker_path.write_text('{"files":{}}', encoding="utf-8")
    monkeypatch.setattr(json, "loads", lambda *args, **kwargs: {"files": {7: "hash"}})
    before = tree_state(root)
    with pytest.raises(ValueError, match=r"^Invalid vault marker:"):
        write(root, {"a.md": b"A"})
    assert tree_state(root) == before


def test_non_string_manifest_hash_is_rejected(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    marker_path = root / MANIFEST
    marker_path.write_text(json.dumps({"files": {"a.md": 7}}), encoding="utf-8")
    before = tree_state(root)
    with pytest.raises(ValueError, match=r"^Invalid vault marker:"):
        write(root, {"a.md": b"A"})
    assert tree_state(root) == before


@pytest.mark.parametrize("unsafe", UNSAFE_PATHS + [None])
def test_unsafe_new_file_paths_are_rejected(tmp_path, unsafe):
    root = tmp_path / "vault"
    before = tree_state(root)
    with pytest.raises(ValueError, match=r"^Unsafe path:"):
        write(root, {unsafe: b"A"})
    assert tree_state(root) == before


def test_manifest_name_must_be_plain_filename(tmp_path):
    root = tmp_path / "vault"
    before = tree_state(root)
    with pytest.raises(ValueError, match=r"^Unsafe path:"):
        write_managed_tree(root, {"a.md": b"A"}, manifest_name="nested/marker.json", manifest_header=HEADER)
    assert tree_state(root) == before


def test_manifest_symlink_escape_is_rejected_when_symlinks_available(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_file = outside / "target.md"
    outside_file.write_bytes(b"outside")
    try:
        (root / "link").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"directory symlinks unavailable: {exc}")
    marker = {"files": {"link/target.md": hashlib.sha256(b"outside").hexdigest()}}
    (root / MANIFEST).write_text(json.dumps(marker), encoding="utf-8")
    before = tree_state(root)
    before_outside = outside_file.read_bytes()
    with pytest.raises(ValueError, match=r"^Invalid vault marker:"):
        write(root, {"a.md": b"A"})
    assert tree_state(root) == before
    assert outside_file.read_bytes() == before_outside


def test_stale_empty_directories_are_pruned_but_foreign_content_and_root_remain(tmp_path):
    root = tmp_path / "vault"
    write(root, {"deep/nested/a.md": b"A", "deep/nested/b.md": b"B", "keep/c.md": b"C"})
    (root / "keep" / "foreign.txt").write_bytes(b"foreign")
    write(root, {"deep/nested/b.md": b"B", "keep/c.md": b"C"})
    assert (root / "deep" / "nested").is_dir()
    write(root, {"keep/c.md": b"C"})
    assert not (root / "deep").exists()
    assert (root / "keep").is_dir()
    assert (root / "keep" / "foreign.txt").read_bytes() == b"foreign"
    assert root.is_dir()


def test_keyboard_interrupt_during_write_rolls_back_and_propagates(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    write(root, {"old/nested.md": b"old", "same.md": b"before"})
    before = tree_state(root)
    original = shutil.copy2
    calls = {"count": 0}

    def interrupt_once(source, destination, *args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 5:
            raise KeyboardInterrupt()
        return original(source, destination, *args, **kwargs)

    monkeypatch.setattr(shutil, "copy2", interrupt_once)
    with pytest.raises(KeyboardInterrupt):
        write(root, {"new/nested.md": b"new", "same.md": b"after"})
    assert tree_state(root) == before
