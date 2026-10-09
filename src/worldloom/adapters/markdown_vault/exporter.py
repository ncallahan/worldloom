"""Deterministic, read-only Markdown vault projection of WorldState."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from worldloom.core import WorldState
from worldloom.adapters.markdown_vault.markup import (
    code_span,
    frontmatter,
    link,
    safe_text,
    text_field,
)
from worldloom.adapters.markdown_vault.naming import (
    build_display_map,
    entity_filename,
    entity_title,
    id_parts,
)
from worldloom.adapters.markdown_vault.writer import write_managed_tree

PROJECTION_VERSION = "0.3.1"
_MARKER = ".worldloom-vault.json"


def _items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else [value]


def _mesh(value: Any) -> str | None:
    if isinstance(value, dict) and set(value) == {"space", "index"}:
        return f"{value['space']} {value['index']}"
    return None


def _reference_links(
    value: Any,
    entities: dict[str, dict[str, Any]],
    paths: dict[str, str],
    displays: dict[str, str],
) -> list[tuple[str, str, str, str]]:
    result = []
    for item in _items(value):
        if isinstance(item, str) and item in entities:
            title = entities[item]["_title"]
            display = displays[item]
            result.append((title, display, item, link(paths[item], display)))
        else:
            mesh = _mesh(item)
            if mesh is not None:
                result.append((mesh, mesh, "", mesh))
    return result


def _note(
    entity_id: str,
    entity: dict[str, Any],
    entities: dict[str, dict[str, Any]],
    paths: dict[str, str],
    displays: dict[str, str],
    inverse: dict[str, list[tuple[str, str, str]]],
    provenance: Any,
) -> str:
    title = entity["_title"]
    kind, _ = id_parts(entity_id)
    entries: list[tuple[str, Any]] = [
        ("worldloom_generated", True),
        ("worldloom_id", entity_id),
        ("worldloom_kind", kind),
        ("worldloom_projection_version", PROJECTION_VERSION),
        ("aliases", [title]),
    ]
    fmg = entity.get("fmg")
    if isinstance(fmg, dict):
        for key, front_key in (("collection", "fmg_collection"), ("id", "fmg_id"), ("position", "fmg_position")):
            if key in fmg:
                entries.append((front_key, fmg[key]))
    attrs = entity.get("attributes", {})
    if isinstance(attrs, dict):
        for key in ("x", "y"):
            value = attrs.get(key)
            if type(value) in (int, float):
                entries.append((f"fmg_{key}", value))
    if provenance is not None:
        entries.extend([
            ("provenance_producer", provenance.producer),
            ("provenance_inputs", list(provenance.inputs)),
        ])
        importer_version = provenance.configuration.get("importer_version")
        if importer_version is not None:
            entries.append(("importer_version", importer_version))

    text_fields: list[tuple[str, str]] = []
    lines = [frontmatter(entries), "", f"# {title}", "", "## Imported facts (uninterpreted FMG values)"]
    for key in sorted(attrs):
        value = attrs[key]
        value_path = f"entity {entity_id}.attributes[{key!r}]"
        if isinstance(value, str) and ("\n" in value or len(value) > 120):
            text_fields.append((key, value))
            lines.append(f"- {code_span(key)}: text field, {len(value)} characters (see Text fields)")
        else:
            lines.append(f"- {code_span(key)}: {safe_text(value, value_path)}")

    if text_fields:
        lines.extend(["", "## Text fields"])
        for key, value in text_fields:
            lines.extend([f"### {code_span(key)}", text_field(value)])

    lines.extend(["", "## Relationships"])
    refs = entity.get("refs", {})
    if isinstance(refs, dict):
        any_refs = False
        for field in sorted(refs):
            links = _reference_links(refs[field], entities, paths, displays)
            if not links:
                continue
            any_refs = True
            lines.append(f"### {code_span(field)}")
            for _, _, _, rendered in sorted(
                links,
                key=lambda item: (item[0].casefold(), item[1].casefold(), item[2]),
            ):
                lines.append(f"- {rendered}")
        if not any_refs:
            lines.append("- None")
    else:
        lines.append("- None")

    lines.extend(["", "## Derived by the projection", "", "Referenced by"])
    groups: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    for source_kind, ref_field, source_id in inverse.get(entity_id, []):
        groups.setdefault((source_kind, ref_field), []).append(
            (entities[source_id]["_title"], displays[source_id], source_id)
        )
    if groups:
        for group in sorted(groups):
            lines.append(f"### {group[0]} / {code_span(group[1])}")
            for title_value, display_value, source_id in sorted(
                groups[group],
                key=lambda item: (item[0].casefold(), item[1].casefold(), item[2]),
            ):
                lines.append(f"- {link(paths[source_id], display_value)}")
    else:
        lines.append("- None")

    lines.extend(["", "## Provenance"])
    if provenance is None:
        lines.append("- None")
    else:
        value_path = f"entity {entity_id}.provenance.producer"
        lines.append(f"- producer: {safe_text(provenance.producer, value_path)}")
        lines.append("- inputs:")
        for index, item in enumerate(provenance.inputs):
            value_path = f"entity {entity_id}.provenance.inputs[{index}]"
            lines.append(f"  - {safe_text(item, value_path)}")
        if provenance.configuration:
            lines.append("- configuration:")
            for key in sorted(provenance.configuration):
                value_path = f"entity {entity_id}.provenance.configuration[{key!r}]"
                lines.append(f"  - {key}: {safe_text(provenance.configuration[key], value_path)}")
    lines.append("- import record: [[_worldloom/import|_worldloom/import]]")
    return "\n".join(lines) + "\n"


def _import_note(
    world: WorldState,
    duplicate_counts: dict[str, int],
    disambiguation_counts: dict[str, dict[str, int]],
) -> str:
    lines = ["# Worldloom import", "", f"- projection_version: {safe_text(PROJECTION_VERSION)}"]
    source = world.fields.get("fmg.source")
    if isinstance(source, dict):
        lines.extend(["", "## Source metadata"])
        for key in sorted(source):
            lines.append(f"- {key}: {safe_text(source[key])}")
    counts: dict[str, int] = {}
    for entity_id, entity in world.entities.items():
        fmg = entity.get("fmg")
        kind = fmg.get("collection") if isinstance(fmg, dict) else id_parts(entity_id)[0]
        counts[kind] = counts.get(kind, 0) + 1
    lines.extend(["", "## Entity counts"])
    for kind in sorted(counts):
        lines.append(f"- {kind}: {counts[kind]}")
    lines.extend(["", "## Anomalies"])
    report = world.observations.get("fmg.import.report")
    if isinstance(report, dict):
        for block in ("diagnostics", "entities", "features", "biomes", "climate"):
            section = report.get(block)
            if not isinstance(section, dict):
                continue
            anomaly = section.get("anomalies")
            if isinstance(anomaly, dict):
                lines.append(f"### {block}")
                lines.append(f"- total: {anomaly.get('total', 0)}")
                for kind in sorted(anomaly.get("counts", {})):
                    lines.append(f"- {kind}: {sum(anomaly['counts'][kind].values())}")
                continue
            diagnostic_values = {
                "sentinels_minus_one": section.get("sentinels_minus_one", 0),
                "out_of_range": section.get("out_of_range", 0),
                "invalid_structure_count": section.get("invalid_structure_count", 0),
                "missing_sections": section.get("missing_sections", []),
            }
            totals = {}
            for kind, value in diagnostic_values.items():
                if isinstance(value, dict):
                    value = sum(item for item in value.values() if isinstance(item, int))
                elif isinstance(value, list):
                    value = len(value)
                elif not isinstance(value, int):
                    value = 0
                if value:
                    totals[kind] = value
            if totals:
                lines.append(f"### {block}")
                lines.append(f"- total: {sum(totals.values())}")
                for kind in sorted(totals):
                    lines.append(f"- {kind}: {totals[kind]}")
    lines.extend(["", "## DUPLICATE-TITLE COUNTS"])
    for kind in sorted(duplicate_counts):
        counts = disambiguation_counts.get(kind, {"qualifier": 0, "hex": 0})
        lines.append(
            f"- {kind}: {duplicate_counts[kind]} "
            f"(qualifier: {counts['qualifier']}, hex: {counts['hex']})"
        )
    return "\n".join(lines) + "\n"


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
    entities = {eid: dict(value) for eid, value in world.entities.items()}
    for eid, entity in entities.items():
        kind, _ = id_parts(eid)
        entity["_title"] = entity_title(entity, kind)
        entity["_path"] = f"{kind}/{entity_filename(eid, entity)[1]}"
    paths = {eid: entity["_path"] for eid, entity in entities.items()}

    collisions: dict[str, list[str]] = {}
    for eid, relative in paths.items():
        collisions.setdefault(relative, []).append(eid)
    for relative, ids in collisions.items():
        if len(ids) > 1:
            raise ValueError(f"Projected path collision: {relative}")

    displays, disambiguation_counts = build_display_map(entities)

    inverse: dict[str, list[tuple[str, str, str]]] = {}
    for source_id, entity in entities.items():
        refs = entity.get("refs", {})
        if not isinstance(refs, dict):
            continue
        source_kind = id_parts(source_id)[0]
        for field, value in refs.items():
            for item in _items(value):
                if isinstance(item, str) and item in entities:
                    inverse.setdefault(item, []).append((source_kind, field, source_id))

    titles: dict[str, dict[str, list[str]]] = {}
    for eid, entity in entities.items():
        kind = id_parts(eid)[0]
        titles.setdefault(kind, {}).setdefault(entity["_title"], []).append(eid)
    duplicate_counts = {kind: sum(len(ids) > 1 for ids in values.values()) for kind, values in titles.items()}

    _validate_strings(world.entities, "entities")
    _validate_strings(world.fields, "fields")
    _validate_strings(world.observations, "observations")
    for provenance_id, provenance in world.provenance.items():
        _validate_strings(provenance.producer, f"provenance[{provenance_id!r}].producer")
        _validate_strings(provenance.inputs, f"provenance[{provenance_id!r}].inputs")
        _validate_strings(provenance.configuration, f"provenance[{provenance_id!r}].configuration")

    generated: dict[str, bytes] = {}
    for eid, entity in entities.items():
        _validate_strings(entity, f"entity {eid}")
        generated[paths[eid]] = _note(
            eid,
            entity,
            entities,
            paths,
            displays,
            inverse,
            world.provenance.get(f"entity:{eid}"),
        ).encode("utf-8")

    kinds = sorted({path.split("/", 1)[0] for path in paths.values()})
    group_index_paths: dict[str, list[tuple[str, str, int]]] = {}
    kind_counts: dict[str, int] = {}
    for kind in kinds:
        ids = sorted(
            (eid for eid in entities if paths[eid].startswith(kind + "/")),
            key=lambda eid: (
                entities[eid]["_title"].casefold(),
                displays[eid].casefold(),
                eid,
            ),
        )
        kind_counts[kind] = len(ids)
        group_indexes: list[tuple[str, str, int]] = []
        for attribute in ("type", "group"):
            values: dict[str, list[str]] = {}
            missing: list[str] = []
            for eid in ids:
                attrs = entities[eid].get("attributes", {})
                value = attrs.get(attribute) if isinstance(attrs, dict) else None
                if isinstance(value, str):
                    values.setdefault(value, []).append(eid)
                else:
                    missing.append(eid)
            if not values:
                continue
            relative = f"indexes/{kind}-by-{attribute}.md"
            group_indexes.append((relative, attribute, len(ids)))
            sections: list[str] = [f"# {kind} by {attribute}", ""]
            for value in sorted(values, key=lambda item: (item.casefold(), item)):
                members = sorted(
                    values[value],
                    key=lambda eid: (
                        entities[eid]["_title"].casefold(),
                        displays[eid].casefold(),
                        eid,
                    ),
                )
                sections.extend(
                    [f"### {code_span(value)} ({len(members)})", ""]
                    + [f"- {link(paths[eid], displays[eid])}" for eid in members]
                    + [""]
                )
            if missing:
                members = sorted(
                    missing,
                    key=lambda eid: (
                        entities[eid]["_title"].casefold(),
                        displays[eid].casefold(),
                        eid,
                    ),
                )
                sections.extend(
                    [f"### (none) ({len(members)})", ""]
                    + [f"- {link(paths[eid], displays[eid])}" for eid in members]
                    + [""]
                )
            generated[relative] = "\n".join(sections).encode("utf-8")
        group_index_paths[kind] = group_indexes

        lines = ["# " + kind, ""]
        lines.extend(f"- {link(paths[eid], displays[eid])}" for eid in ids)
        for relative, attribute, count in group_indexes:
            lines.append(f"- {link(relative, f'{kind} by {attribute}')} ({count})")
        lines.append("")
        generated[f"indexes/{kind}.md"] = "\n".join(lines).encode("utf-8")

    index = ["# Worldloom", "", "Generated note indexes:", ""]
    index.extend(
        f"- {link(f'indexes/{kind}.md', kind)} ({kind_counts[kind]})"
        for kind in kinds
    )
    index.extend(["", "Generated group-by indexes:", ""])
    for kind in kinds:
        index.extend(
            f"- {link(relative, f'{kind} by {attribute}')} ({count})"
            for relative, attribute, count in group_index_paths[kind]
        )
    index.append("")
    generated["index.md"] = "\n".join(index).encode("utf-8")
    generated["_worldloom/import.md"] = _import_note(
        world,
        duplicate_counts,
        disambiguation_counts,
    ).encode("utf-8")

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
