"""Markdown-vault import-report rendering."""

from __future__ import annotations

from typing import Any

from worldloom.adapters.markdown_vault.markup import safe_text
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
        counts[kind] = counts.get(kind, 0) + 1
    lines = ["", "## Entity counts"]
    for kind in sorted(counts):
        lines.append(f"- {kind}: {counts[kind]}")
    return lines


def _diagnostic_totals(section: dict[str, Any]) -> dict[str, int]:
    diagnostic_values = {
        "sentinels_minus_one": section.get("sentinels_minus_one", 0),
        "out_of_range": section.get("out_of_range", 0),
        "invalid_structure_count": section.get("invalid_structure_count", 0),
        "missing_sections": section.get("missing_sections", []),
    }
    totals: dict[str, int] = {}
    for kind, value in diagnostic_values.items():
        if isinstance(value, dict):
            value = sum(item for item in value.values() if isinstance(item, int))
        elif isinstance(value, list):
            value = len(value)
        elif not isinstance(value, int):
            value = 0
        if value:
            totals[kind] = value
    return totals


def _anomaly_block_lines(block: str, section: dict[str, Any]) -> list[str]:
    anomaly = section.get("anomalies")
    if isinstance(anomaly, dict):
        lines = [f"### {block}", f"- total: {anomaly.get('total', 0)}"]
        for kind in sorted(anomaly.get("counts", {})):
            lines.append(f"- {kind}: {sum(anomaly['counts'][kind].values())}")
        return lines
    totals = _diagnostic_totals(section)
    if not totals:
        return []
    lines = [f"### {block}", f"- total: {sum(totals.values())}"]
    for kind in sorted(totals):
        lines.append(f"- {kind}: {totals[kind]}")
    return lines


def _anomaly_section_lines(world: WorldState) -> list[str]:
    lines = ["", "## Anomalies"]
    report = world.observations.get("fmg.import.report")
    if isinstance(report, dict):
        for block in ("diagnostics", "entities", "features", "biomes", "climate"):
            section = report.get(block)
            if isinstance(section, dict):
                lines.extend(_anomaly_block_lines(block, section))
    return lines


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
