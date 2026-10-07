from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import pytest

from worldloom.adapters import export_markdown_vault
from worldloom.adapters.markdown_vault.exporter import _filename
from worldloom.adapters.fmg import import_fmg_snapshot
from worldloom.core import Address, WorldState
from worldloom.core.persistence import load_world, save_world

REPO_ROOT = Path(__file__).parents[2]
THIMALAND = REPO_ROOT / "examples" / "Thimaland Full 2026-10-02-14-17.json"
PITHIGY = REPO_ROOT / "examples" / "Pithigy Full 2026-10-02-11-35.json"
VIVERIA = REPO_ROOT / "examples" / "Viveria Full 2026-10-02-11-31.json"
PITHIGY_SLICE = REPO_ROOT / "experiments" / "fmg_scale" / "slices" / "Pithigy_burg1_hop3.json"
VIVERIA_SLICE = REPO_ROOT / "experiments" / "fmg_scale" / "slices" / "Viveria_burg1_hop3.json"


def entity(name, digest, kind="test", refs=None):
    return {"attributes": {"name": name}, "refs": {} if refs is None else refs}, f"{kind}:{digest}"


def simple_world(*items):
    world = WorldState()
    for value, entity_id in items:
        world.add_entity(entity_id, value)
    return world


def _mask_code(text):
    return re.sub(chr(96) + r"+[^" + chr(96) + r"]*" + chr(96) + r"+", "", text)


def _links_outside_code(text):
    return re.findall(r"\[\[([^\]]+)\]\]", _mask_code(text))


def test_fmg_vault_example_script(tmp_path, monkeypatch):
    from examples.export_fmg_vault import main

    monkeypatch.setattr(
        sys,
        "argv",
        ["export_fmg_vault.py", str(THIMALAND), str(tmp_path / "vault")],
    )
    main()
    assert (tmp_path / "vault" / ".worldloom-vault.json").exists()
    assert (tmp_path / "vault" / "index.md").exists()


def _index_displays(root: Path, kind: str) -> list[str]:
    text = (root / "indexes" / f"{kind}.md").read_text(encoding="utf-8")
    return [
        link.split("|", 1)[1].removesuffix("]]")
        for link in re.findall(r"\[\[([^\]]+)\]\]", text)
        if "|" in link
    ]


def test_link_display_disambiguation_rules(tmp_path):
    world = simple_world(
        *[
            entity("Same", "000000000001", refs={"parent": "place:000000000001"}),
            entity("Same", "000000000002", refs={"parent": "place:000000000002"}),
            entity("Same", "000000000003", refs={"parent": "place:000000000001"}),
            entity("Same", "000000000004"),
            entity("Unique", "000000000005"),
            entity(
                "Target A",
                "000000000001",
                kind="place",
                refs={"list_ref": ["place:000000000002"], "mesh": {"space": "pack.cells", "index": 7}},
            ),
            entity("Target B", "000000000002", kind="place"),
        ]
    )
    export_markdown_vault(world, tmp_path / "vault")
    index = (tmp_path / "vault" / "indexes" / "test.md").read_text(encoding="utf-8")
    displays = [link.split("|", 1)[1][:-2] for link in re.findall(r"\[\[([^\]]+)\]\]", index)]
    assert any(display == r"Same (Target A, 000000000001)" for display in displays)
    assert any(display == "Same (Target B)" for display in displays)
    assert any(display == "Same (000000000004)" for display in displays)
    assert any(display == "Unique" for display in displays)
    assert len(displays) == len(set(displays))


def test_qualifier_selection_uses_sorted_single_entity_refs(tmp_path):
    world = simple_world(
        *[
            entity(
                "Same",
                "000000000011",
                refs={
                    "z_ref": "place:000000000012",
                    "a_list": ["place:000000000013"],
                    "b_ref": "place:000000000013",
                    "mesh": {"space": "pack.cells", "index": 3},
                },
            ),
            entity("Same", "000000000014", refs={"b_ref": "place:000000000012"}),
            entity("A", "000000000012", kind="place"),
            entity("B", "000000000013", kind="place"),
        ]
    )
    export_markdown_vault(world, tmp_path / "vault")
    index = (tmp_path / "vault" / "indexes" / "test.md").read_text(encoding="utf-8")
    assert "|Same (B)]]" in index
    assert "|Same (A, 000000000014)]]" in index
    assert "pack.cells 3" not in index


def test_display_escape_is_applied_to_final_display_text():
    from worldloom.adapters.markdown_vault.exporter import _link

    assert _link("test/Example (000000000001).md", "Same (North | [West])") == (
        r"[[test/Example (000000000001)|Same (North \| \[West\])]]"
    )


@pytest.mark.parametrize("source", [THIMALAND, PITHIGY, VIVERIA, PITHIGY_SLICE, VIVERIA_SLICE])
def test_display_text_is_unique_within_kind_for_canonical_exports_and_slices(tmp_path, source):
    world = WorldState()
    import_fmg_snapshot(world, source)
    target = tmp_path / source.stem
    export_markdown_vault(world, target)
    for kind in sorted({eid.split(":", 1)[0] for eid in world.entities}):
        displays = _index_displays(target, kind)
        assert len(displays) == len(set(displays))


def test_markdown_vault_filenames_remain_entity_id_based(tmp_path):
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    target = tmp_path / "vault"
    export_markdown_vault(world, target)
    for entity_id in list(world.entities)[:3]:
        kind, filename = _filename(entity_id, world.entities[entity_id])
        assert (target / kind / filename).exists()


def test_filename_sanitisation_and_reserved_names(tmp_path):
    forbidden = '\\/:*?"<>|#^[]'
    for index, char in enumerate(forbidden):
        world = simple_world(*[entity(f"A{char}B", f"{index + 1:012x}")])
        export_markdown_vault(world, tmp_path / str(index))
        name = next((tmp_path / str(index) / "test").glob("*.md")).name
        assert char not in name

    for index, name in enumerate(["", "   ", "CON", "PRN", "AUX", "NUL", "COM1", "LPT1"], 100):
        world = simple_world(*[entity(name, f"{index:012x}")])
        export_markdown_vault(world, tmp_path / str(index))
        names = list((tmp_path / str(index) / "test").glob("*.md"))
        assert len(names) == 1
        base = names[0].name.split(".", 1)[0].split(" (", 1)[0].upper()
        assert base not in {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1"}

    reserved_with_extension = simple_world(*[entity("CON.txt", "000000000122")])
    export_markdown_vault(reserved_with_extension, tmp_path / "reserved-extension")
    reserved_filename = next((tmp_path / "reserved-extension" / "test").glob("*.md")).name
    assert reserved_filename.split(".", 1)[0].upper() == "CON_"

    world = simple_world(*[entity("x" * 100, "000000000123")])
    export_markdown_vault(world, tmp_path / "long")
    filename = next((tmp_path / "long" / "test").glob("*.md")).name
    assert len(filename.split(" (", 1)[0]) == 80

    nfc = unicodedata.normalize("NFC", "Cafe\u0301")
    nfd = unicodedata.normalize("NFD", "Café")
    export_markdown_vault(simple_world(*[entity(nfc, "000000000124")]), tmp_path / "nfc")
    export_markdown_vault(simple_world(*[entity(nfd, "000000000125")]), tmp_path / "nfd")
    assert next((tmp_path / "nfc" / "test").glob("*.md")).name.split(" (")[0] == next((tmp_path / "nfd" / "test").glob("*.md")).name.split(" (" )[0]


def test_thimaland_import_note_diagnostics_are_integer_totals(tmp_path):
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    target = tmp_path / "vault"
    export_markdown_vault(world, target)
    text = (target / "_worldloom" / "import.md").read_text(encoding="utf-8")
    diagnostics = text.split("## Anomalies", 1)[1].split("## DUPLICATE-TITLE COUNTS", 1)[0]
    values = re.findall(r"- ([A-Za-z0-9_]+): (\d+)$", diagnostics, re.MULTILINE)
    assert values
    assert all(value.isdigit() for _, value in values)


def test_duplicate_titles_are_unique_and_forced_collision_aborts(tmp_path, monkeypatch):
    world = simple_world(*[entity("Same", "000000000001"), entity("Same", "000000000002")])
    export_markdown_vault(world, tmp_path / "unique")
    assert len(list((tmp_path / "unique" / "test").glob("*.md"))) == 2

    import worldloom.adapters.markdown_vault.exporter as exporter
    monkeypatch.setattr(exporter, "_filename", lambda eid, value: ("test", "same (000000000000).md"))
    target = tmp_path / "collision"
    with pytest.raises(ValueError, match="Projected path collision"):
        export_markdown_vault(world, target)
    assert not target.exists()


def test_thimaland_one_note_per_entity(tmp_path):
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    target = tmp_path / "vault"
    export_markdown_vault(world, target)
    note_files = [
        p for p in target.rglob("*.md")
        if not p.relative_to(target).as_posix().startswith("indexes/")
        and p.relative_to(target).as_posix() not in {"index.md", "_worldloom/import.md"}
    ]
    assert len(note_files) == len(world.entities)
    assert sum(world.observations["fmg.import.report"]["entities"]["entity_counts"].values()) == len(world.entities)


@pytest.mark.parametrize("source", [THIMALAND, PITHIGY, VIVERIA])
def test_all_wikilinks_resolve_and_report_duplicate_titles(tmp_path, source):
    world = WorldState()
    import_fmg_snapshot(world, source)
    target = tmp_path / source.stem
    export_markdown_vault(world, target)

    written = {p.relative_to(target).with_suffix("").as_posix() for p in target.rglob("*.md")}
    for path in target.rglob("*.md"):
        for link in _links_outside_code(path.read_text(encoding="utf-8")):
            assert link.split("|", 1)[0] in written, (path, link)

    by_kind = {}
    for eid, value in world.entities.items():
        kind = eid.split(":", 1)[0]
        title = value.get("attributes", {}).get("name")
        if not isinstance(title, str) or not title:
            title = f"Unnamed {kind}"
        by_kind.setdefault(kind, {}).setdefault(title, 0)
        by_kind[kind][title] += 1
    counts = {kind: sum(n > 1 for n in titles.values()) for kind, titles in by_kind.items()}
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(f"\n### Markdown vault duplicate-title counts: {source.name}\n")
            for kind in sorted(counts):
                handle.write(f"- {kind}: {counts[kind]}\n")


def test_inverse_relationships_and_mesh_refs(tmp_path):
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    target = tmp_path / "vault"
    export_markdown_vault(world, target)

    state_titles = {}
    for eid, value in world.entities.items():
        if value["fmg"]["collection"] == "states":
            state_titles[eid] = value["attributes"].get("name") or "Unnamed state"
    assert state_titles

    for path in target.rglob("*.md"):
        masked = _mask_code(path.read_text(encoding="utf-8"))
        assert not re.search(r"\[\[[^\]]*pack\.cells", masked)

    for state_id, title in state_titles.items():
        kind, filename = _filename(state_id, world.entities[state_id])
        note = target / kind / filename
        assert note.exists()
        expected = sorted(
            value["attributes"].get("name") or "Unnamed burg"
            for eid, value in world.entities.items()
            if value["fmg"]["collection"] == "burgs"
            and value.get("refs", {}).get("state") == state_id
        )
        text = note.read_text(encoding="utf-8")
        for burg_title in expected:
            burg_id = next(
                eid for eid, value in world.entities.items()
                if value["fmg"]["collection"] == "burgs"
                and value.get("refs", {}).get("state") == state_id
                and (value["attributes"].get("name") or "Unnamed burg") == burg_title
            )
            burg_kind, burg_filename = _filename(burg_id, world.entities[burg_id])
            assert f"[[{burg_kind}/{burg_filename[:-3]}|{burg_title}]]" in text


def test_frontmatter_order_and_markdown_injection(tmp_path):
    world = simple_world(*[entity("A|[[B]]", "000000000321")])
    world.entities["test:000000000321"]["attributes"]["payload"] = (
        "[[Evil]] | # --- " + chr(96) + "x" + chr(96) + "\nsecond"
    )
    export_markdown_vault(world, tmp_path / "vault")
    note = next((tmp_path / "vault" / "test").glob("*.md")).read_text(encoding="utf-8")
    frontmatter = note.split("---", 2)[1].splitlines()
    keys = [line.split(":", 1)[0] for line in frontmatter if line and not line.startswith("  ")]
    assert keys[:5] == ["worldloom_generated", "worldloom_id", "worldloom_kind", "worldloom_projection_version", "aliases"]
    body = note.split("## Imported facts", 1)[1].split("## Relationships", 1)[0]
    assert "[[Evil]]" not in _mask_code(body)
    assert "---" in body


def test_marker_safety_determinism_and_roundtrip(tmp_path):
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    a, b = tmp_path / "a", tmp_path / "b"
    export_markdown_vault(world, a)
    export_markdown_vault(world, b)
    read = lambda root: {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert read(a) == read(b)
    saved = tmp_path / "roundtrip.json"
    save_world(world, saved)
    loaded = load_world(saved)
    c = tmp_path / "c"
    export_markdown_vault(loaded, c)
    assert read(a) == read(c)

    marker = json.loads((a / ".worldloom-vault.json").read_text(encoding="utf-8"))
    for relative, digest in marker["files"].items():
        assert hashlib.sha256((a / relative).read_bytes()).hexdigest() == digest

    edited = next(p for p in a.rglob("*.md") if p.name != "index.md")
    original = edited.read_bytes()
    edited.write_bytes(original + b"edited")
    before = read(a)
    with pytest.raises(ValueError, match="Hand-edited generated file"):
        export_markdown_vault(world, a)
    assert before == read(a)
    export_markdown_vault(world, a, overwrite_edited=True)
    assert edited.read_bytes() == original

    deleted = next(p for p in a.rglob("*.md") if p.name != "index.md")
    deleted.unlink()
    export_markdown_vault(world, a)
    assert deleted.exists()

    foreign = a / "foreign.md"
    foreign.write_text("keep", encoding="utf-8")
    export_markdown_vault(world, a)
    assert foreign.read_text(encoding="utf-8") == "keep"

    unsafe = tmp_path / "unsafe"
    unsafe.mkdir()
    (unsafe / "foreign.md").write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError, match="without .worldloom-vault.json"):
        export_markdown_vault(world, unsafe)
    assert (unsafe / "foreign.md").read_text(encoding="utf-8") == "keep"


def test_injected_write_failure_leaves_existing_vault_unchanged(tmp_path, monkeypatch):
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    target = tmp_path / "vault"
    export_markdown_vault(world, target)
    before = {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob("*") if p.is_file()}

    import worldloom.adapters.markdown_vault.exporter as exporter
    original_copy2 = exporter.shutil.copy2
    calls = {"count": 0}

    def fail_once(source, destination, *args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("injected write failure")
        return original_copy2(source, destination, *args, **kwargs)

    monkeypatch.setattr(exporter.shutil, "copy2", fail_once)
    with pytest.raises(OSError, match="injected write failure"):
        export_markdown_vault(world, target)
    assert before == {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob("*") if p.is_file()}


def test_kind_and_hex_validation(tmp_path):
    world = simple_world(*[entity("Bad", "0123456789ab", kind="../x")])
    with pytest.raises(ValueError, match="projection-compatible"):
        export_markdown_vault(world, tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


@pytest.mark.parametrize("location", ["fields", "observations", "provenance"])
def test_surrogate_in_written_world_sources(tmp_path, location):
    bad = "x" + chr(0xD800)
    if location == "fields":
        world = WorldState(fields={"fmg.source": {"bad": bad}}, observations={}, provenance={})
    elif location == "observations":
        world = WorldState(fields={}, observations={"fmg.import.report": {"diagnostics": {"bad": bad}}}, provenance={})
    else:
        from worldloom.core.provenance import Provenance
        world = WorldState(fields={}, observations={}, provenance={"entity:test:000000000999": Provenance(producer=bad)})
        world.add_entity("test:000000000999", {"attributes": {"name": "Plain"}, "refs": {}})
    with pytest.raises(ValueError, match="Lone surrogate"):
        export_markdown_vault(world, tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


def test_injected_write_failure_during_write_restores_marker_and_vault(tmp_path, monkeypatch):
    world_a = WorldState()
    import_fmg_snapshot(world_a, THIMALAND)
    target = tmp_path / "vault"
    export_markdown_vault(world_a, target)
    before = {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob("*") if p.is_file()}

    world_b = deepcopy(world_a)
    changed_id = next(iter(world_b.entities))
    world_b.entities[changed_id]["attributes"]["name"] = "Changed World B Name"
    world_b.entities[changed_id]["attributes"]["changed_attribute"] = "world B"
    expected_b = tmp_path / "world-b"
    export_markdown_vault(world_b, expected_b)
    b_files = {p.relative_to(expected_b).as_posix() for p in expected_b.rglob("*") if p.is_file()}
    assert b_files != set(before)

    marker = json.loads((target / ".worldloom-vault.json").read_text(encoding="utf-8"))
    backup_count = len(marker["files"]) + 1

    import worldloom.adapters.markdown_vault.exporter as exporter
    original_copy2 = exporter.shutil.copy2
    calls = {"count": 0}

    def fail_during_write(source, destination, *args, **kwargs):
        calls["count"] += 1
        if calls["count"] == backup_count + 2:
            raise OSError("injected write-phase failure")
        return original_copy2(source, destination, *args, **kwargs)

    monkeypatch.setattr(exporter.shutil, "copy2", fail_during_write)
    with pytest.raises(OSError, match="injected write-phase failure"):
        export_markdown_vault(world_b, target)

    after = {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob("*") if p.is_file()}
    assert after == before
    assert not (set(after) & (b_files - set(before)))


@pytest.mark.parametrize("bad_value", [{1, 2}, Address.cell(1, 2)])
def test_non_json_serialisable_attribute_reports_entity_path(tmp_path, bad_value):
    world = simple_world(*[entity("Plain", "000000000998")])
    world.entities["test:000000000998"]["attributes"]["bad"] = bad_value
    with pytest.raises(ValueError, match=r"entity test:000000000998\.attributes\['bad'\].*JSON-serialisable"):
        export_markdown_vault(world, tmp_path / "bad")


def test_surrogate_and_non_fmg_world(tmp_path):
    bad_name = "bad" + chr(0xD800)
    bad = simple_world(*[entity(bad_name, "000000000999")])
    with pytest.raises(ValueError, match="Lone surrogate"):
        export_markdown_vault(bad, tmp_path / "bad")
    assert not (tmp_path / "bad").exists()

    good = simple_world(*[entity("Plain", "000000001000")])
    export_markdown_vault(good, tmp_path / "good")
    import_note = (tmp_path / "good" / "_worldloom" / "import.md").read_text(encoding="utf-8")
    assert "fmg.source" not in import_note
