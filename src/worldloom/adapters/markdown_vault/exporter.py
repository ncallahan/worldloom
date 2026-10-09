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
from worldloom.adapters.markdown_vault.notes import as_items, render_note
from worldloom.adapters.markdown_vault.report import render_import_note
from worldloom.adapters.markdown_vault.version import PROJECTION_VERSION

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
            for item in as_items(value):
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
        generated[paths[eid]] = render_note(
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
    generated["_worldloom/import.md"] = render_import_note(
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
