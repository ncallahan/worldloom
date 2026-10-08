"""Transactional writer for Worldloom-managed Markdown vault trees.

Known issues, fixed in a later PR:
- A failed export into a fresh vault can leave empty directories behind; a retry is then refused as a non-empty vault without a marker.
- Paths read from an existing manifest are not validated; an entry such as "../x" can make the writer touch files outside root.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any


def _check_target(root: Path, manifest_name: str) -> Path:
    if root.exists() and not root.is_dir():
        raise ValueError(f"Vault target is not a directory: {root}")
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / manifest_name
    if any(root.iterdir()) and not manifest_path.exists():
        raise ValueError(f"Refusing non-empty vault without {manifest_name}: {root}")
    return manifest_path


def _read_manifest_files(manifest_path: Path) -> dict[str, str]:
    if not manifest_path.exists():
        return {}
    try:
        marker_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return dict(marker_data.get("files", {}))
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid vault marker: {manifest_path}") from exc


def _check_hand_edits(root: Path, old_files: dict[str, str], overwrite_edited: bool) -> None:
    if overwrite_edited:
        return
    for relative, expected in sorted(old_files.items()):
        existing = root / relative
        if not existing.exists():
            continue
        actual = hashlib.sha256(existing.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Hand-edited generated file: {relative}")


def _check_unlisted(root: Path, files: dict[str, bytes], old_files: dict[str, str], manifest_name: str) -> None:
    for relative in files:
        if relative != manifest_name and (root / relative).exists() and relative not in old_files:
            raise ValueError(f"Refusing to overwrite unlisted file: {relative}")


def _build_manifest(files: dict[str, bytes], manifest_name: str, manifest_header: dict[str, Any]) -> dict[str, bytes]:
    hashes = {path: hashlib.sha256(data).hexdigest() for path, data in files.items()}
    manifest = {
        **manifest_header,
        "files": {path: hashes[path] for path in sorted(hashes)},
    }
    encoded = (json.dumps(manifest, ensure_ascii=False, indent=2, separators=(",", ": ")) + "\n").encode("utf-8")
    return {**files, manifest_name: encoded}


def _stage(files: dict[str, bytes], stage: Path) -> None:
    for relative, data in files.items():
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def _backup(root: Path, stage: Path, managed_files: set[str]) -> None:
    backup = stage / ".old"
    backup.mkdir()
    for relative in sorted(managed_files):
        target = root / relative
        if target.exists():
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)


def _apply(root: Path, stage: Path, files: dict[str, bytes], old_files: dict[str, str]) -> None:
    for relative in old_files:
        if relative not in files:
            target = root / relative
            if target.exists():
                target.unlink()
    for relative in files:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(stage / relative, target)


def _rollback(root: Path, stage: Path, files: dict[str, bytes], managed_files: set[str]) -> None:
    for relative in files:
        target = root / relative
        if target.exists() and relative not in managed_files:
            target.unlink()
    for relative in sorted(managed_files):
        saved = stage / ".old" / relative
        if saved.exists():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(saved, target)


def write_managed_tree(
    root: Path,
    files: dict[str, bytes],
    *,
    manifest_name: str,
    manifest_header: dict[str, Any],
    overwrite_edited: bool = False,
) -> None:
    """Write files transactionally, tracking managed paths in a JSON manifest."""
    staged_files = _build_manifest(files, manifest_name, manifest_header)
    manifest_path = _check_target(root, manifest_name)
    old_files = _read_manifest_files(manifest_path)
    _check_hand_edits(root, old_files, overwrite_edited)
    _check_unlisted(root, files, old_files, manifest_name)
    with tempfile.TemporaryDirectory(dir=root.parent) as temp_name:
        stage = Path(temp_name)
        _stage(staged_files, stage)
        managed_files = set(old_files)
        if manifest_path.exists():
            managed_files.add(manifest_name)
        try:
            _backup(root, stage, managed_files)
            _apply(root, stage, staged_files, old_files)
        except Exception:
            _rollback(root, stage, staged_files, managed_files)
            raise
