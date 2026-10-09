"""Index rendering for the Markdown-vault projection."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from worldloom.adapters.markdown_vault.markup import code_span, link
from worldloom.adapters.markdown_vault.plan import ProjectionPlan


def _member_sort_key(
    entities: dict[str, dict[str, Any]], displays: dict[str, str]
) -> Callable[[str], tuple[str, str, str]]:
    return lambda eid: (
        entities[eid]["_title"].casefold(),
        displays[eid].casefold(),
        eid,
    )


def _group_index_lines(
    kind: str,
    attribute: str,
    ids: list[str],
    plan: ProjectionPlan,
    member_key: Callable[[str], tuple[str, str, str]],
) -> list[str] | None:
    values: dict[str, list[str]] = {}
    missing: list[str] = []
    for eid in ids:
        attrs = plan.entities[eid].get("attributes", {})
        value = attrs.get(attribute) if isinstance(attrs, dict) else None
        if isinstance(value, str):
            values.setdefault(value, []).append(eid)
        else:
            missing.append(eid)
    if not values:
        return None

    sections = [f"# {kind} by {attribute}", ""]
    for value in sorted(values, key=lambda item: (item.casefold(), item)):
        members = sorted(values[value], key=member_key)
        sections.extend(
            [f"### {code_span(value)} ({len(members)})", ""]
            + [f"- {link(plan.paths[eid], plan.displays[eid])}" for eid in members]
            + [""]
        )
    if missing:
        members = sorted(missing, key=member_key)
        sections.extend(
            [f"### (none) ({len(members)})", ""]
            + [f"- {link(plan.paths[eid], plan.displays[eid])}" for eid in members]
            + [""]
        )
    return sections


def _kind_index_lines(
    kind: str,
    ids: list[str],
    group_indexes: list[tuple[str, str, int]],
    plan: ProjectionPlan,
) -> list[str]:
    lines = ["# " + kind, ""]
    lines.extend(f"- {link(plan.paths[eid], plan.displays[eid])}" for eid in ids)
    for relative, attribute, count in group_indexes:
        lines.append(f"- {link(relative, f'{kind} by {attribute}')} ({count})")
    lines.append("")
    return lines


def _root_index_lines(
    kinds: list[str],
    kind_counts: dict[str, int],
    group_index_paths: dict[str, list[tuple[str, str, int]]],
) -> list[str]:
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
    return index


def render_indexes(plan: ProjectionPlan) -> dict[str, bytes]:
    """Render group-by indexes, kind indexes, and the root index in insertion order."""
    generated: dict[str, bytes] = {}
    kinds = sorted({path.split("/", 1)[0] for path in plan.paths.values()})
    group_index_paths: dict[str, list[tuple[str, str, int]]] = {}
    kind_counts: dict[str, int] = {}
    member_key = _member_sort_key(plan.entities, plan.displays)

    for kind in kinds:
        ids = sorted(
            (eid for eid in plan.entities if plan.paths[eid].startswith(kind + "/")),
            key=member_key,
        )
        kind_counts[kind] = len(ids)
        group_indexes: list[tuple[str, str, int]] = []
        for attribute in ("type", "group"):
            sections = _group_index_lines(kind, attribute, ids, plan, member_key)
            if sections is None:
                continue
            relative = f"indexes/{kind}-by-{attribute}.md"
            group_indexes.append((relative, attribute, len(ids)))
            generated[relative] = "\n".join(sections).encode("utf-8")
        group_index_paths[kind] = group_indexes
        lines = _kind_index_lines(kind, ids, group_indexes, plan)
        generated[f"indexes/{kind}.md"] = "\n".join(lines).encode("utf-8")

    generated["index.md"] = "\n".join(
        _root_index_lines(kinds, kind_counts, group_index_paths)
    ).encode("utf-8")
    return generated
