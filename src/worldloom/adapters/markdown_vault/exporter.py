"""Deterministic, read-only Markdown vault projection of WorldState."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

from worldloom.core import WorldState

PROJECTION_VERSION = "0.1.0"
_MARKER = ".worldloom-vault.json"
_FORBIDDEN = re.compile(r'[\\/:*?"<>|#^\[\]\x00-\x1f\x7f]')
_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
_ID_RE = re.compile(r"^([^:]+):([0-9a-fA-F]{12})$")


def _id_parts(entity_id: str) -> tuple[str, str]:
    match = _ID_RE.fullmatch(entity_id)
    if not match:
        raise ValueError(f"Entity ID is not a projection-compatible kind:12hex ID: {entity_id!r}")
    return match.group(1), match.group(2).lower()


def _title(entity: dict[str, Any], kind: str) -> str:
    value = entity.get("attributes", {}).get("name")
    raw = value if isinstance(value, str) and value else f"Unnamed {kind}"
    raw = unicodedata.normalize("NFC", raw)
    raw = _FORBIDDEN.sub("", raw)
    raw = " ".join(raw.split()).strip(" .")
    raw = raw[:80].rstrip(" .")
    return raw or f"Unnamed {kind}"


def _filename(entity_id: str, entity: dict[str, Any]) -> tuple[str, str]:
    kind, digest = _id_parts(entity_id)
    title = _title(entity, kind)
    if title.upper() in _RESERVED:
        title = f"{title} [{digest}]"
    return kind, f"{title} ({digest}).md"


def _yaml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if type(value) in (int, float):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    return json.dumps(str(value), ensure_ascii=False)


def _frontmatter(entries: list[tuple[str, Any]]) -> str:
    lines = ["---"]
    for key, value in entries:
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {_yaml_value(item)}" for item in value)
        else:
            lines.append(f"{key}: {_yaml_value(value)}")
    lines.append("---")
    return "\n".join(lines)


def _safe_text(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    longest = max((len(run) for run in re.findall(chr(96) + "+", text)), default=0)
    fence = chr(96) * (longest + 1)
    return f"{fence}{text}{fence}"


def _display(value: str) -> str:
    return value.replace("|", r"\|").replace("[", r"\[").replace("]", r"\]")


def _link(path: str, display: str) -> str:
    return f"[[{path.removesuffix('.md')}|{_display(display)}]]"


def _items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else [value]


def _mesh(value: Any) -> str | None:
    if isinstance(value, dict) and set(value) == {"space", "index"}:
        return f"{value['space']} {value['index']}"
    return None


def _reference_links(value: Any, entities: dict[str, dict[str, Any]], paths: dict[str, str]) -> list[tuple[str, str]]:
    result = []
    for item in _items(value):
        if isinstance(item, str) and item in entities:
            title = entities[item]["_title"]
            result.append((title, _link(paths[item], title)))
        else:
            mesh = _mesh(item)
            if mesh is not None:
                result.append((mesh, mesh))
    return result


def _note(entity_id: str, entity: dict[str, Any], entities: dict[str, dict[str, Any]], paths: dict[str, str],
          inverse: dict[str, list[tuple[str, str, str]]], provenance: Any) -> str:
    title = entity["_title"]
    kind, _ = _id_parts(entity_id)
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

    lines = [_frontmatter(entries), "", f"# {title}", "", "## Imported facts (uninterpreted FMG values)"]
    for key in sorted(attrs):
        lines.append(f"- {key}: {_safe_text(attrs[key])}")

    lines.extend(["", "## Relationships"])
    refs = entity.get("refs", {})
    if isinstance(refs, dict):
        any_refs = False
        for field in sorted(refs):
            links = _reference_links(refs[field], entities, paths)
            if not links:
                continue
            any_refs = True
            lines.append(f"### {field}")
            for _, rendered in sorted(links, key=lambda item: (item[0].casefold(), item[0])):
                lines.append(f"- {rendered}")
        if not any_refs:
            lines.append("- None")
    else:
        lines.append("- None")

    lines.extend(["", "## Derived by the projection", "", "Referenced by"])
    groups: dict[tuple[str, str], list[str]] = {}
    for source_kind, ref_field, source_id in inverse.get(entity_id, []):
        groups.setdefault((source_kind, ref_field), []).append(_link(paths[source_id], entities[source_id]["_title"]))
    if groups:
        for group in sorted(groups):
            lines.append(f"### {group[0]} / {group[1]}")
            for rendered in sorted(groups[group], key=str.casefold):
                lines.append(f"- {rendered}")
    else:
        lines.append("- None")

    lines.extend(["", "## Provenance"])
    if provenance is None:
        lines.append("- None")
    else:
        lines.append(f"- producer: {_safe_text(provenance.producer)}")
        lines.append("- inputs:")
        for item in provenance.inputs:
            lines.append(f"  - {_safe_text(item)}")
        if provenance.configuration:
            lines.append("- configuration:")
            for key in sorted(provenance.configuration):
                lines.append(f"  - {key}: {_safe_text(provenance.configuration[key])}")
    lines.append("- import record: [[_worldloom/import|_worldloom/import]]")
    return "\n".join(lines) + "\n"


def _import_note(world: WorldState, duplicate_counts: dict[str, int]) -> str:
    lines = ["# Worldloom import", "", f"- projection_version: {_safe_text(PROJECTION_VERSION)}"]
    source = world.fields.get("fmg.source")
    if isinstance(source, dict):
        lines.extend(["", "## Source metadata"])
        for key in sorted(source):
            lines.append(f"- {key}: {_safe_text(source[key])}")
    counts: dict[str, int] = {}
    for entity_id, entity in world.entities.items():
        fmg = entity.get("fmg")
        kind = fmg.get("collection") if isinstance(fmg, dict) else _id_parts(entity_id)[0]
        counts[kind] = counts.get(kind, 0) + 1
    lines.extend(["", "## Entity counts"])
    for kind in sorted(counts):
        lines.append(f"- {kind}: {counts[kind]}")
    lines.extend(["", "## Anomalies"])
    report = world.observations.get("fmg.import.report")
    if isinstance(report, dict):
        for block in ("diagnostics", "entities", "features", "biomes", "climate"):
            section = report.get(block)
            anomaly = section.get("anomalies") if isinstance(section, dict) else None
            if not isinstance(anomaly, dict):
                continue
            lines.append(f"### {block}")
            lines.append(f"- total: {anomaly.get('total', 0)}")
            for kind in sorted(anomaly.get("counts", {})):
                lines.append(f"- {kind}: {sum(anomaly['counts'][kind].values())}")
    lines.extend(["", "## DUPLICATE-TITLE COUNTS"])
    for kind in sorted(duplicate_counts):
        lines.append(f"- {kind}: {duplicate_counts[kind]}")
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
        kind, _ = _id_parts(eid)
        entity["_title"] = _title(entity, kind)
        entity["_path"] = f"{kind}/{_filename(eid, entity)[1]}"
    paths = {eid: entity["_path"] for eid, entity in entities.items()}

    collisions: dict[str, list[str]] = {}
    for eid, relative in paths.items():
        collisions.setdefault(relative, []).append(eid)
    for relative, ids in collisions.items():
        if len(ids) > 1:
            raise ValueError(f"Projected path collision: {relative}")

    inverse: dict[str, list[tuple[str, str, str]]] = {}
    for source_id, entity in entities.items():
        refs = entity.get("refs", {})
        if not isinstance(refs, dict):
            continue
        source_kind = _id_parts(source_id)[0]
        for field, value in refs.items():
            for item in _items(value):
                if isinstance(item, str) and item in entities:
                    inverse.setdefault(item, []).append((source_kind, field, source_id))

    titles: dict[str, dict[str, list[str]]] = {}
    for eid, entity in entities.items():
        kind = _id_parts(eid)[0]
        titles.setdefault(kind, {}).setdefault(entity["_title"], []).append(eid)
    duplicate_counts = {kind: sum(len(ids) > 1 for ids in values.values()) for kind, values in titles.items()}

    generated: dict[str, bytes] = {}
    for eid, entity in entities.items():
        _validate_strings(entity, f"entity {eid}")
        generated[paths[eid]] = _note(eid, entity, entities, paths, inverse, world.provenance.get(f"entity:{eid}")).encode("utf-8")

    kinds = sorted({path.split("/", 1)[0] for path in paths.values()})
    for kind in kinds:
        ids = sorted((eid for eid in entities if paths[eid].startswith(kind + "/")),
                     key=lambda eid: (entities[eid]["_title"].casefold(), eid))
        text = "\n".join(["# " + kind, ""] + [f"- {_link(paths[eid], entities[eid]['_title'])}" for eid in ids] + [""])
        generated[f"indexes/{kind}.md"] = text.encode("utf-8")
    index = ["# Worldloom", "", "Generated note indexes:", ""] + [
        f"- {_link(f'indexes/{kind}.md', kind)} ({sum(p.startswith(kind + '/') for p in paths.values())})" for kind in kinds
    ] + [""]
    generated["index.md"] = "\n".join(index).encode("utf-8")
    generated["_worldloom/import.md"] = _import_note(world, duplicate_counts).encode("utf-8")

    fingerprint = world.fingerprint({"entities": world.entities, "fields": world.fields, "observations": world.observations})
    hashes = {path: hashlib.sha256(data).hexdigest() for path, data in generated.items()}
    marker = {
        "generator": "worldloom",
        "projection_version": PROJECTION_VERSION,
        "world_fingerprint": fingerprint,
        "files": {path: hashes[path] for path in sorted(hashes)},
    }
    generated[_MARKER] = (json.dumps(marker, ensure_ascii=False, indent=2, separators=(",", ": ")) + "\n").encode("utf-8")

    if root.exists() and not root.is_dir():
        raise ValueError(f"Vault target is not a directory: {root}")
    root.mkdir(parents=True, exist_ok=True)
    marker_path = root / _MARKER
    if any(root.iterdir()) and not marker_path.exists():
        raise ValueError(f"Refusing non-empty vault without {_MARKER}: {root}")

    old_files: dict[str, str] = {}
    if marker_path.exists():
        try:
            marker_data = json.loads(marker_path.read_text(encoding="utf-8"))
            old_files = dict(marker_data.get("files", {}))
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid vault marker: {marker_path}") from exc
        if not overwrite_edited:
            for relative, expected in sorted(old_files.items()):
                existing = root / relative
                if not existing.exists():
                    continue
                actual = hashlib.sha256(existing.read_bytes()).hexdigest()
                if actual != expected:
                    raise ValueError(f"Hand-edited generated file: {relative}")

    for relative in generated:
        if relative != _MARKER and (root / relative).exists() and relative not in old_files:
            raise ValueError(f"Refusing to overwrite unlisted file: {relative}")

    with tempfile.TemporaryDirectory(dir=root.parent) as temp_name:
        stage = Path(temp_name)
        for relative, data in generated.items():
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)

        backup = stage / ".old"
        backup.mkdir()
        try:
            for relative in old_files:
                target = root / relative
                if target.exists():
                    saved = backup / relative
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, saved)
            for relative in old_files:
                if relative not in generated:
                    target = root / relative
                    if target.exists():
                        target.unlink()
            for relative in generated:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(stage / relative, target)
        except Exception:
            for relative in generated:
                target = root / relative
                if target.exists() and relative not in old_files:
                    target.unlink()
            for relative in old_files:
                saved = backup / relative
                if saved.exists():
                    target = root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(saved, target)
            raise
