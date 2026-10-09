"""Deterministic, read-only Markdown vault projection of WorldState."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from worldloom.core import WorldState
from worldloom.adapters.markdown_vault.writer import write_managed_tree
from worldloom.adapters.markdown_vault.notes import render_note
from worldloom.adapters.fmg.anomalies import summarize_anomalies
from worldloom.adapters.markdown_vault.report import render_anomalies_note, render_import_note
from worldloom.adapters.markdown_vault.version import PROJECTION_VERSION
from worldloom.adapters.markdown_vault.plan import build_projection_plan
from worldloom.adapters.markdown_vault.indexes import render_indexes

_MARKER = ".worldloom-vault.json"


def _validate_strings(value: Any, path: str) -> None:
    if isinstance(value, str):
        if any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            raise ValueError(f"Lone surrogate in string to be written at {path}")
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_strings(key, f"{path}.key")
            _validate_strings(item, f"{path}[{key!r}]")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_strings(item, f"{path}[{index}]")


def export_markdown_vault(world: WorldState, path: str | Path, *, overwrite_edited: bool = False) -> None:
    """Write a deterministic Obsidian-compatible projection of WorldState."""
    root = Path(path)
    plan = build_projection_plan(world.entities)

    _validate_strings(world.entities, "entities")
    _validate_strings(world.fields, "fields")
    _validate_strings(world.observations, "observations")
    for provenance_id, provenance in world.provenance.items():
        _validate_strings(provenance.producer, f"provenance[{provenance_id!r}].producer")
        _validate_strings(provenance.inputs, f"provenance[{provenance_id!r}].inputs")
        _validate_strings(provenance.configuration, f"provenance[{provenance_id!r}].configuration")

    generated: dict[str, bytes] = {}
    for eid, entity in plan.entities.items():
        _validate_strings(entity, f"entity {eid}")
        generated[plan.paths[eid]] = render_note(
            eid,
            entity,
            plan.entities,
            plan.paths,
            plan.displays,
            plan.inverse,
            world.provenance.get(f"entity:{eid}"),
        ).encode("utf-8")

    generated.update(render_indexes(plan))
    report = world.observations.get("fmg.import.report")
    generated["_worldloom/import.md"] = render_import_note(
        world,
        plan.duplicate_counts,
        plan.disambiguation_counts,
    ).encode("utf-8")
    if isinstance(report, Mapping):
        summary = summarize_anomalies(report)
        generated["_worldloom/anomalies.md"] = render_anomalies_note(
            report
        ).encode("utf-8")
        if summary is not None:
            errors = summary.by_severity["error"]
            warnings = summary.by_severity["warning"]
            if errors + warnings:
                banner = (
                    f"Import anomalies: {errors} errors, {warnings} warnings "
                    "(see [[_worldloom/anomalies|anomalies]])"
                )
                generated["index.md"] = (
                    banner.encode("utf-8") + b"\n\n" + generated["index.md"]
                )

    fingerprint = world.fingerprint({"entities": world.entities, "fields": world.fields, "observations": world.observations})
    write_managed_tree(
        root,
        generated,
        manifest_name=_MARKER,
        manifest_header={
            "generator": "worldloom",
            "projection_version": PROJECTION_VERSION,
            "world_fingerprint": fingerprint,
        },
        overwrite_edited=overwrite_edited,
    )
