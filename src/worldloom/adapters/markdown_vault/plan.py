"""Projection planning for the Markdown-vault adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from worldloom.adapters.markdown_vault.naming import (
    build_display_map,
    entity_filename,
    entity_title,
    id_parts,
)
from worldloom.adapters.markdown_vault.markup import as_items


@dataclass
class ProjectionPlan:
    entities: dict[str, dict[str, Any]]
    paths: dict[str, str]
    displays: dict[str, str]
    disambiguation_counts: dict[str, dict[str, int]]
    inverse: dict[str, list[tuple[str, str, str]]]
    duplicate_counts: dict[str, int]


def _copy_entities_with_titles(
    world_entities: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    entities = {eid: dict(value) for eid, value in world_entities.items()}
    for eid, entity in entities.items():
        kind, _ = id_parts(eid)
        entity["_title"] = entity_title(entity, kind)
        entity["_path"] = f"{kind}/{entity_filename(eid, entity)[1]}"
    paths = {eid: entity["_path"] for eid, entity in entities.items()}
    return entities, paths


def _check_path_collisions(paths: dict[str, str]) -> None:
    collisions: dict[str, list[str]] = {}
    for eid, relative in paths.items():
        collisions.setdefault(relative, []).append(eid)
    for relative, ids in collisions.items():
        if len(ids) > 1:
            raise ValueError(f"Projected path collision: {relative}")


def _build_inverse(
    entities: dict[str, dict[str, Any]],
) -> dict[str, list[tuple[str, str, str]]]:
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
    return inverse


def _duplicate_title_counts(
    entities: dict[str, dict[str, Any]],
) -> dict[str, int]:
    titles: dict[str, dict[str, list[str]]] = {}
    for eid, entity in entities.items():
        kind = id_parts(eid)[0]
        titles.setdefault(kind, {}).setdefault(entity["_title"], []).append(eid)
    return {
        kind: sum(len(ids) > 1 for ids in values.values())
        for kind, values in titles.items()
    }


def build_projection_plan(
    world_entities: dict[str, dict[str, Any]],
) -> ProjectionPlan:
    """Build projection data in the same order as the original exporter."""
    entities, paths = _copy_entities_with_titles(world_entities)
    _check_path_collisions(paths)
    displays, disambiguation_counts = build_display_map(entities)
    inverse = _build_inverse(entities)
    duplicate_counts = _duplicate_title_counts(entities)
    return ProjectionPlan(
        entities=entities,
        paths=paths,
        displays=displays,
        disambiguation_counts=disambiguation_counts,
        inverse=inverse,
        duplicate_counts=duplicate_counts,
    )
