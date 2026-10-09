"""Markdown-vault entity-note rendering."""

from __future__ import annotations

from typing import Any

from worldloom.adapters.markdown_vault.markup import as_items, code_span, frontmatter, link, safe_text, text_field
from worldloom.adapters.markdown_vault.naming import id_parts
from worldloom.adapters.markdown_vault.version import PROJECTION_VERSION


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
    for item in as_items(value):
        if isinstance(item, str) and item in entities:
            title = entities[item]["_title"]
            display = displays[item]
            result.append((title, display, item, link(paths[item], display)))
        else:
            mesh = _mesh(item)
            if mesh is not None:
                result.append((mesh, mesh, "", mesh))
    return result


def _frontmatter_entries(
    entity_id: str, entity: dict[str, Any], provenance: Any
) -> tuple[str, list[tuple[str, Any]], dict[str, Any]]:
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
    return title, entries, attrs


def _imported_facts_lines(
    entity_id: str, attrs: Any
) -> tuple[list[str], list[tuple[str, str]]]:
    text_fields: list[tuple[str, str]] = []
    lines: list[str] = []
    for key in sorted(attrs):
        value = attrs[key]
        value_path = f"entity {entity_id}.attributes[{key!r}]"
        if isinstance(value, str) and ("\n" in value or len(value) > 120):
            text_fields.append((key, value))
            lines.append(f"- {code_span(key)}: text field, {len(value)} characters (see Text fields)")
        else:
            lines.append(f"- {code_span(key)}: {safe_text(value, value_path)}")
    return lines, text_fields


def _text_fields_lines(text_fields: list[tuple[str, str]]) -> list[str]:
    if not text_fields:
        return []
    lines = ["", "## Text fields"]
    for key, value in text_fields:
        lines.extend([f"### {code_span(key)}", text_field(value)])
    return lines


def _relationship_lines(
    entity: dict[str, Any], entities: dict[str, dict[str, Any]],
    paths: dict[str, str], displays: dict[str, str]
) -> list[str]:
    lines = ["", "## Relationships"]
    refs = entity.get("refs", {})
    if not isinstance(refs, dict):
        lines.append("- None")
        return lines
    any_refs = False
    for field in sorted(refs):
        links = _reference_links(refs[field], entities, paths, displays)
        if not links:
            continue
        any_refs = True
        lines.append(f"### {code_span(field)}")
        for _, _, _, rendered in sorted(
            links, key=lambda item: (item[0].casefold(), item[1].casefold(), item[2])
        ):
            lines.append(f"- {rendered}")
    if not any_refs:
        lines.append("- None")
    return lines


def _referenced_by_lines(
    entity_id: str, entities: dict[str, dict[str, Any]], paths: dict[str, str],
    displays: dict[str, str], inverse: dict[str, list[tuple[str, str, str]]]
) -> list[str]:
    lines = ["", "## Derived by the projection", "", "Referenced by"]
    groups: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    for source_kind, ref_field, source_id in inverse.get(entity_id, []):
        groups.setdefault((source_kind, ref_field), []).append(
            (entities[source_id]["_title"], displays[source_id], source_id)
        )
    if groups:
        for group in sorted(groups):
            lines.append(f"### {group[0]} / {code_span(group[1])}")
            for title_value, display_value, source_id in sorted(
                groups[group], key=lambda item: (item[0].casefold(), item[1].casefold(), item[2])
            ):
                lines.append(f"- {link(paths[source_id], display_value)}")
    else:
        lines.append("- None")
    return lines


def _provenance_lines(entity_id: str, provenance: Any) -> list[str]:
    lines = ["", "## Provenance"]
    if provenance is None:
        lines.append("- None")
        return lines
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
    return lines


def render_note(
    entity_id: str,
    entity: dict[str, Any],
    entities: dict[str, dict[str, Any]],
    paths: dict[str, str],
    displays: dict[str, str],
    inverse: dict[str, list[tuple[str, str, str]]],
    provenance: Any,
) -> str:
    title, entries, attrs = _frontmatter_entries(entity_id, entity, provenance)
    lines = [frontmatter(entries), "", f"# {title}", "", "## Imported facts (uninterpreted FMG values)"]
    imported_lines, text_fields = _imported_facts_lines(entity_id, attrs)
    lines.extend(imported_lines)
    lines.extend(_text_fields_lines(text_fields))
    lines.extend(_relationship_lines(entity, entities, paths, displays))
    lines.extend(_referenced_by_lines(entity_id, entities, paths, displays, inverse))
    lines.extend(_provenance_lines(entity_id, provenance))
    lines.append("- import record: [[_worldloom/import|_worldloom/import]]")
    return "\n".join(lines) + "\n"
