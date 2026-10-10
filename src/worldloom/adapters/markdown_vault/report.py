"""Markdown-vault import and anomaly report rendering."""

from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any

from worldloom.adapters.fmg.anomalies import summarize_anomalies
from worldloom.adapters.markdown_vault.markup import code_span, safe_text
from worldloom.adapters.markdown_vault.naming import id_parts
from worldloom.adapters.markdown_vault.version import PROJECTION_VERSION
from worldloom.core import WorldState


def _source_metadata_lines(world: WorldState) -> list[str]:
    lines: list[str] = []
    source = world.fields.get("fmg.source")
    if isinstance(source, dict):
        lines.extend(["", "## Source metadata"])
        for key in sorted(source):
            lines.append(f"- {key}: {safe_text(source[key])}")
    return lines


def _entity_count_lines(world: WorldState) -> list[str]:
    counts: dict[str, int] = {}
    for entity_id, entity in world.entities.items():
        fmg = entity.get("fmg")
        kind = fmg.get("collection") if isinstance(fmg, dict) else id_parts(entity_id)[0]
        if not isinstance(kind, str):
            kind = json.dumps(kind, ensure_ascii=False, separators=(",", ":"), allow_nan=False, sort_keys=True)
        counts[kind] = counts.get(kind, 0) + 1
    lines = ["", "## Entity counts"]
    for kind in sorted(counts):
        lines.append(f"- {kind}: {counts[kind]}")
    return lines


def _anomaly_section_lines(world: WorldState) -> list[str]:
    lines = ["", "## Anomalies"]
    report = world.observations.get("fmg.import.report")
    summary = summarize_anomalies(report)
    if summary is None:
        lines.append("- None")
        return lines
    if summary.total == 0:
        lines.append("- No anomalies recorded")
        return lines

    for severity in ("error", "warning", "info"):
        count = summary.by_severity[severity]
        if not count:
            continue
        lines.extend(["", f"### {severity.title()} ({count})"])
        for kind, detail in summary.by_kind.items():
            if detail["severity"] == severity and detail["count"]:
                lines.append(f"- {kind}: {detail['count']}")
    return lines


def render_anomalies_note(report: Mapping[str, Any]) -> str:
    """Render deterministic severity, kind, pattern, and path details."""
    summary = summarize_anomalies(report)
    lines = ["# Import anomalies", ""]
    if summary is None or summary.total == 0:
        lines.append("No anomalies recorded")
    else:
        for severity in ("error", "warning", "info"):
            count = summary.by_severity[severity]
            if not count:
                continue
            lines.extend([f"## {severity.title()} ({count})", ""])
            for kind, detail in summary.by_kind.items():
                if detail["severity"] != severity or not detail["count"]:
                    continue
                lines.extend([f"### {code_span(kind)} ({detail['count']})", ""])
                for pattern, pattern_detail in detail["patterns"].items():
                    lines.append(
                        f"- {code_span(pattern)}: {pattern_detail['count']}"
                    )
                    lines.extend(
                        f"  - {code_span(path)}" for path in pattern_detail["paths"]
                    )
                lines.append("")

    if summary is not None and summary.unrecognised_blocks:
        names = ", ".join(code_span(name) for name in summary.unrecognised_blocks)
        lines.extend(["", f"Unrecognised report blocks: {names}"])
    return "\n".join(lines).rstrip() + "\n"


def _duplicate_title_lines(
    duplicate_counts: dict[str, int], disambiguation_counts: dict[str, dict[str, int]]
) -> list[str]:
    lines = ["", "## DUPLICATE-TITLE COUNTS"]
    for kind in sorted(duplicate_counts):
        counts = disambiguation_counts.get(kind, {"qualifier": 0, "hex": 0})
        lines.append(
            f"- {kind}: {duplicate_counts[kind]} "
            f"(qualifier: {counts['qualifier']}, hex: {counts['hex']})"
        )
    return lines


def render_import_note(
    world: WorldState,
    duplicate_counts: dict[str, int],
    disambiguation_counts: dict[str, dict[str, int]],
) -> str:
    lines = ["# Worldloom import", "", f"- projection_version: {safe_text(PROJECTION_VERSION)}"]
    lines.extend(_source_metadata_lines(world))
    lines.extend(_entity_count_lines(world))
    lines.extend(_anomaly_section_lines(world))
    lines.extend(_duplicate_title_lines(duplicate_counts, disambiguation_counts))
    return "\n".join(lines) + "\n"
