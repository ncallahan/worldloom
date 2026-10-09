"""Provisional format conversion pipeline for Worldloom."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Callable

from worldloom.adapters import export_markdown_vault
from worldloom.adapters.fmg import import_fmg_snapshot
from worldloom.adapters.fmg.anomalies import format_counts, summarize_anomalies
from worldloom.core import WorldState
from worldloom.core.persistence import load_world, save_world

try:
    import resource
except ImportError:  # pragma: no cover - unavailable on Windows
    resource = None


_EXPECTED_FMG_VERSION = "1.153.1"
_STEM_RE = re.compile(r"[^A-Za-z0-9._-]+")


class ConversionError(ValueError):
    """An expected conversion failure suitable for concise CLI errors."""


def _read_fmg(world: WorldState, path: Path) -> None:
    import_fmg_snapshot(world, path)


def _read_world_json(world: WorldState, path: Path) -> None:
    loaded = load_world(path)
    world.restore(loaded.snapshot())


def _write_markdown(world: WorldState, path: Path, *, overwrite_edited: bool) -> None:
    export_markdown_vault(world, path, overwrite_edited=overwrite_edited)


def _write_world_json(world: WorldState, path: Path, *, overwrite_edited: bool) -> None:
    del overwrite_edited
    save_world(world, path)


_FORMATS: dict[str, dict[str, Any]] = {
    "fmg": {
        "roles": ("source",),
        "description": "Azgaar Fantasy Map Generator full JSON snapshot",
        "reader": _read_fmg,
    },
    "world-json": {
        "roles": ("source", "target"),
        "description": "provisional unversioned Worldloom world save",
        "reader": _read_world_json,
        "writer": _write_world_json,
    },
    "markdown-vault": {
        "roles": ("target",),
        "description": "Obsidian-compatible Markdown projection",
        "writer": _write_markdown,
    },
}


def list_formats() -> tuple[dict[str, Any], ...]:
    """Return the small, provisional conversion-format table."""
    return tuple(
        {
            "name": name,
            "roles": spec["roles"],
            "description": spec["description"],
        }
        for name, spec in _FORMATS.items()
    )


def _validate_request(
    source_format: str | None,
    target_format: str | None,
    inputs: list[Path],
    output: Path | None,
    *,
    overwrite_edited: bool,
    force: bool,
) -> None:
    errors: list[str] = []
    if source_format not in _FORMATS:
        errors.append(f"unknown source format: {source_format!r}")
    if target_format not in _FORMATS:
        errors.append(f"unknown target format: {target_format!r}")
    if source_format in _FORMATS and "source" not in _FORMATS[source_format]["roles"]:
        errors.append(f"format is not a source: {source_format}")
    if target_format in _FORMATS and "target" not in _FORMATS[target_format]["roles"]:
        errors.append(f"format is not a target: {target_format}")
    if source_format == target_format == "world-json":
        errors.append("world-json -> world-json conversion is not supported")
    if overwrite_edited and target_format != "markdown-vault":
        errors.append("--overwrite-edited is only valid with markdown-vault output")
    if force and target_format != "world-json":
        errors.append("--force is only valid with world-json output")
    if not inputs:
        errors.append("at least one input is required")
    if output is None:
        errors.append("an output path is required")
    if errors:
        raise ConversionError("\n".join(errors))


def _safe_stem(path: Path) -> str:
    stem = _STEM_RE.sub("_", path.stem)
    stem = re.sub(r"_+", "_", stem)
    return stem or "_"


def _validate_inputs(inputs: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in inputs:
        if not path.exists():
            errors.append(f"input does not exist: {path}")
        elif not path.is_file():
            errors.append(f"input is not a file: {path}")
    return errors


def _validate_stems(inputs: list[Path]) -> dict[Path, str]:
    stems = {path: _safe_stem(path) for path in inputs}
    by_stem: dict[str, list[Path]] = {}
    for path, stem in stems.items():
        by_stem.setdefault(stem, []).append(path)
    duplicates = {
        stem: paths for stem, paths in by_stem.items() if len(paths) > 1
    }
    if duplicates:
        lines = [
            "duplicate output stem: "
            + f"{stem!r} from "
            + ", ".join(str(path) for path in paths)
            for stem, paths in sorted(duplicates.items())
        ]
        raise ConversionError("\n".join(lines))
    return stems


def _preflight_outputs(
    output_paths: list[Path],
    output_root: Path,
    target_format: str,
    *,
    force: bool,
) -> None:
    errors: list[str] = []
    if len(output_paths) > 1 and output_root.exists() and not output_root.is_dir():
        errors.append(f"output root is not a directory: {output_root}")
    for path in output_paths:
        if target_format == "world-json" and path.exists() and not force:
            errors.append(f"refusing to overwrite existing world-json output: {path}")
        elif target_format == "markdown-vault" and path.exists() and not path.is_dir():
            errors.append(f"vault target is not a directory: {path}")
    if errors:
        raise ConversionError("\n".join(errors))


def _peak_memory() -> int | None:
    if resource is None:
        return None
    try:
        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except (AttributeError, OSError):
        return None


def _entity_counts(world: WorldState) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entity_id, entity in world.entities.items():
        kind: Any = None
        if isinstance(entity, dict):
            fmg = entity.get("fmg")
            if isinstance(fmg, dict):
                kind = fmg.get("collection")
        if not isinstance(kind, str) or not kind:
            kind = entity_id.split(":", 1)[0]
        counts[kind] = counts.get(kind, 0) + 1
    return dict(sorted(counts.items()))


def _fmg_version(world: WorldState) -> str | None:
    source = world.fields.get("fmg.source")
    if not isinstance(source, dict) or "fmg_version" not in source:
        return None
    version = source["fmg_version"]
    return str(version) if version is not None else "unknown"


def _vault_stats(path: Path) -> tuple[int, int]:
    marker = path / ".worldloom-vault.json"
    data = json.loads(marker.read_text(encoding="utf-8"))
    files = data.get("files", {})
    if not isinstance(files, dict):
        raise ValueError(f"Invalid vault marker: {marker}")
    total_bytes = sum((path / relative).stat().st_size for relative in files)
    return len(files), total_bytes


def _result(
    *,
    input_path: Path,
    output_path: Path,
    read_seconds: float,
    write_seconds: float,
    world: WorldState,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "input": str(input_path),
        "output": str(output_path),
        "read_seconds": read_seconds,
        "write_seconds": write_seconds,
        "total_seconds": read_seconds + write_seconds,
        "entity_counts": _entity_counts(world),
        "peak_memory": _peak_memory(),
    }
    anomaly_summary = summarize_anomalies(
        world.observations.get("fmg.import.report")
    )
    result["anomaly_summary"] = (
        format_counts(anomaly_summary) if anomaly_summary is not None else None
    )
    result["unrecognised_report_blocks"] = (
        anomaly_summary.unrecognised_blocks if anomaly_summary is not None else []
    )
    version = _fmg_version(world)
    if version is not None:
        result["fmg_version"] = version
        result["fmg_version_expected"] = _EXPECTED_FMG_VERSION
    if output_path.is_dir():
        notes, total_bytes = _vault_stats(output_path)
        result["notes_written"] = notes
        result["bytes_written"] = total_bytes
    else:
        result["bytes_written"] = output_path.stat().st_size
    return result


def convert(
    source_format: str | None,
    target_format: str | None,
    inputs: list[str | Path],
    output: str | Path | None,
    *,
    overwrite_edited: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Convert each input independently through a fresh WorldState."""
    paths = [Path(item) for item in inputs]
    output_path = Path(output) if output is not None else None
    _validate_request(
        source_format,
        target_format,
        paths,
        output_path,
        overwrite_edited=overwrite_edited,
        force=force,
    )
    input_errors = _validate_inputs(paths)
    if input_errors:
        raise ConversionError("\n".join(input_errors))
    stems = _validate_stems(paths)
    assert output_path is not None
    targets = (
        [output_path]
        if len(paths) == 1
        else [
            output_path
            / (stems[path] + (".json" if target_format == "world-json" else ""))
            for path in paths
        ]
    )
    _preflight_outputs(
        targets,
        output_path,
        target_format,
        force=force,
    )

    reader: Callable[[WorldState, Path], None] = _FORMATS[source_format]["reader"]
    writer: Callable[..., None] = _FORMATS[target_format]["writer"]
    results: list[dict[str, Any]] = []

    for input_path, target_path in zip(paths, targets):
        world = WorldState()
        read_started = time.perf_counter()
        reader(world, input_path)
        read_seconds = time.perf_counter() - read_started

        target_path.parent.mkdir(parents=True, exist_ok=True)
        write_started = time.perf_counter()
        writer(
            world,
            target_path,
            overwrite_edited=overwrite_edited,
        )
        write_seconds = time.perf_counter() - write_started
        results.append(
            _result(
                input_path=input_path,
                output_path=target_path,
                read_seconds=read_seconds,
                write_seconds=write_seconds,
                world=world,
            )
        )

    return {"results": results}
