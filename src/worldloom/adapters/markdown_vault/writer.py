"""Transactional writer for Worldloom-managed Markdown vault trees.

R1b fixes rollback directory cleanup and validates managed paths before
manifest-derived paths are read, hashed, copied, or deleted.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any


def _ensure_directory(path: Path, created: list[Path]) -> None:
    missing = []
    current = path
    while not current.exists():
        missing.append(current)
        parent = current.parent
        if parent == current:
            break
        current = parent
    for directory in reversed(missing):
        created.append(directory)
        directory.mkdir()


def _remove_empty_directories(directories: list[Path]) -> None:
    for directory in reversed(directories):
        try:
            directory.rmdir()
        except OSError:
            pass


def _check_target(root: Path, manifest_name: str, created: list[Path]) -> Path:
    if root.exists() and not root.is_dir():
        raise ValueError(f"Vault target is not a directory: {root}")
    _ensure_directory(root, created)
    manifest_path = root / manifest_name
    if any(root.iterdir()) and not manifest_path.exists():
        raise ValueError(f"Refusing non-empty vault without {manifest_name}: {root}")
    return manifest_path


def _validate_relative_path(relative: object, root: Path, prefix: str) -> str:
    if not isinstance(relative, str):
        raise ValueError(f"{prefix} {relative!r}")
    parts = relative.split("/")
    drive_prefix = len(relative) >= 2 and relative[0].isalpha() and relative[1] == ":"
    if (
        not relative
        or relative.startswith("/")
        or "\\" in relative
        or "\x00" in relative
        or drive_prefix
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ValueError(f"{prefix} {relative!r}")
    try:
        candidate = (root / relative).resolve()
        candidate.relative_to(root.resolve())
    except (OSError, RuntimeError, ValueError):
        raise ValueError(f"{prefix} {relative!r}") from None
    return relative


def _validate_manifest_name(manifest_name: str) -> None:
    if (
        not isinstance(manifest_name, str)
        or not manifest_name
        or manifest_name in {".", ".."}
        or "/" in manifest_name
        or "\\" in manifest_name
        or "\x00" in manifest_name
        or (len(manifest_name) >= 2 and manifest_name[0].isalpha() and manifest_name[1] == ":")
    ):
        raise ValueError(f"Unsafe path: {manifest_name!r}")


def _read_manifest_files(manifest_path: Path, root: Path) -> dict[str, str]:
    if not manifest_path.exists():
        return {}
    try:
        marker_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(marker_data, dict):
            raise ValueError("marker must be a mapping")
        raw_files = marker_data.get("files", {})
        if not isinstance(raw_files, dict):
            raise ValueError("files must be a mapping")
        validated = {}
        for relative, expected in raw_files.items():
            path = _validate_relative_path(relative, root, "Invalid vault marker:")
            if not isinstance(expected, str):
                raise ValueError(f"Invalid vault marker: {path!r}")
            validated[path] = expected
        return validated
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith("Invalid vault marker:"):
            raise
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


def _backup(root: Path, backup: Path, managed_files: set[str]) -> None:
    for relative in sorted(managed_files):
        target = root / relative
        if target.exists():
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)


def _apply(
    root: Path,
    stage: Path,
    files: dict[str, bytes],
    old_files: dict[str, str],
    created: list[Path],
) -> list[Path]:
    deleted = []
    for relative in old_files:
        if relative not in files:
            target = root / relative
            if target.exists():
                target.unlink()
                deleted.append(target)
    for relative in files:
        target = root / relative
        _ensure_directory(target.parent, created)
        shutil.copy2(stage / relative, target)
    return deleted


def _rollback(
    root: Path,
    stage: Path,
    files: dict[str, bytes],
    managed_files: set[str],
    created: list[Path],
) -> None:
    for relative in files:
        target = root / relative
        if target.exists() and relative not in managed_files:
            target.unlink()
    for relative in sorted(managed_files):
        saved = stage / ".old" / relative
        if saved.exists():
            target = root / relative
            _ensure_directory(target.parent, created)
            shutil.copy2(saved, target)


def _prune_stale_directories(root: Path, deleted: list[Path]) -> None:
    candidates = set()
    for target in deleted:
        parent = target.parent
        while parent != root and parent != parent.parent:
            candidates.add(parent)
            parent = parent.parent
    for directory in sorted(candidates, key=lambda item: len(item.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            continue


def write_managed_tree(
    root: Path,
    files: dict[str, bytes],
    *,
    manifest_name: str,
    manifest_header: dict[str, Any],
    overwrite_edited: bool = False,
) -> None:
    """Write files transactionally, tracking managed paths in a JSON manifest."""
    created: list[Path] = []
    try:
        _validate_manifest_name(manifest_name)
        _validate_relative_path(manifest_name, root, "Unsafe path:")
        for relative, data in files.items():
            _validate_relative_path(relative, root, "Unsafe path:")
            if not isinstance(data, bytes):
                raise ValueError(f"Unsafe path: {relative!r}")
        staged_files = _build_manifest(files, manifest_name, manifest_header)
        manifest_path = _check_target(root, manifest_name, created)
        old_files = _read_manifest_files(manifest_path, root)
        _check_hand_edits(root, old_files, overwrite_edited)
        _check_unlisted(root, files, old_files, manifest_name)
        with tempfile.TemporaryDirectory(dir=root.parent) as temp_name:
            stage = Path(temp_name)
            _stage(staged_files, stage)
            backup = stage / ".old"
            backup.mkdir()
            managed_files = set(old_files)
            if manifest_path.exists():
                managed_files.add(manifest_name)
            try:
                _backup(root, backup, managed_files)
                deleted = _apply(root, stage, staged_files, old_files, created)
            except BaseException:
                _rollback(root, stage, staged_files, managed_files, created)
                raise
            _prune_stale_directories(root, deleted)
    except BaseException:
        _remove_empty_directories(created)
        raise
