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
from worldloom.adapters.markdown_vault.prepare import prepare_projection_input

_MARKER = ".worldloom-vault.json"


def _has_lone_surrogate(value: str) -> bool:
    return any(0xD800 <= ord(char) <= 0xDFFF for char in value)


def _assert_generated_strings_safe(generated: dict[str, str]) -> None:
    for relative_path, text in generated.items():
        if _has_lone_surrogate(relative_path) or _has_lone_surrogate(text):
            raise ValueError(
                f"Internal error: unsanitised lone surrogate in generated file {relative_path}"
            )


def export_markdown_vault(
    world: WorldState, path: str | Path, *, overwrite_edited: bool = False
):
    """Write a deterministic Obsidian-compatible projection of WorldState.

    Returns the merged anomaly summary, or None when no report is available.
    """
    root = Path(path)
    prepared = prepare_projection_input(world)
    view = prepared.view
    anomalies = prepared.anomalies

    try:
        fingerprint = world.fingerprint({
            "entities": world.entities,
            "fields": world.fields,
            "observations": world.observations,
        })
    except (TypeError, ValueError, UnicodeError):
        fingerprint = view.fingerprint({
            "entities": view.entities,
            "fields": view.fields,
            "observations": view.observations,
        })
        anomalies.setdefault("fingerprint-fallback", {})["world"] = 1

    plan = build_projection_plan(view.entities)
    generated: dict[str, str] = {}
    for entity_id, entity in plan.entities.items():
        generated[plan.paths[entity_id]] = render_note(
            entity_id, entity, plan.entities, plan.paths, plan.displays, plan.inverse,
            view.provenance.get(f"entity:{entity_id}"),
        )

    generated.update({path: text.decode("utf-8") for path, text in render_indexes(plan).items()})
    report = view.observations.get("fmg.import.report")
    if isinstance(report, Mapping):
        merged_report: dict[str, Any] = dict(report)
    else:
        merged_report = {}
    if anomalies:
        merged_report["projection"] = {
            "anomalies": {
                "counts": {
                    kind: {path: counts[path] for path in sorted(counts)}
                    for kind, counts in sorted(anomalies.items())
                },
                "total": sum(sum(paths.values()) for paths in anomalies.values()),
                "examples": [],
            }
        }
        view.observations["fmg.import.report"] = merged_report
        report = merged_report

    generated["_worldloom/import.md"] = render_import_note(
        view, plan.duplicate_counts, plan.disambiguation_counts
    )
    summary = summarize_anomalies(report) if isinstance(report, Mapping) else None
    if isinstance(report, Mapping):
        generated["_worldloom/anomalies.md"] = render_anomalies_note(report)
        if summary is not None:
            errors = summary.by_severity["error"]
            warnings = summary.by_severity["warning"]
            if errors + warnings:
                banner = (
                    f"Import anomalies: {errors} errors, {warnings} warnings "
                    "(see [[_worldloom/anomalies|anomalies]])"
                )
                generated["index.md"] = banner + "\n\n" + generated["index.md"]

    _assert_generated_strings_safe(generated)
    generated_bytes = {relative: text.encode("utf-8") for relative, text in generated.items()}
    write_managed_tree(
        root, generated_bytes, manifest_name=_MARKER,
        manifest_header={
            "generator": "worldloom",
            "projection_version": PROJECTION_VERSION,
            "world_fingerprint": fingerprint,
        },
        overwrite_edited=overwrite_edited,
    )
    return summary
