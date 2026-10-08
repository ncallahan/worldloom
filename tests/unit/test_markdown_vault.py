from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import shutil
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
    assert "[[test/Same (000000000001)|Same (Target A, 000000000001)]]" in index
    assert "[[test/Same (000000000003)|Same (Target A, 000000000003)]]" in index
    assert "[[test/Same (000000000002)|Same (Target B)]]" in index
    assert "[[test/Same (000000000004)|Same (000000000004)]]" in index
    assert "[[test/Unique (000000000005)|Unique]]" in index


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
    assert "|Same (A)]]" in index
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

    original_copy2 = shutil.copy2
    calls = {"count": 0}

    def fail_once(source, destination, *args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("injected write failure")
        return original_copy2(source, destination, *args, **kwargs)

    monkeypatch.setattr(shutil, "copy2", fail_once)
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

    original_copy2 = shutil.copy2
    calls = {"count": 0}

    def fail_during_write(source, destination, *args, **kwargs):
        calls["count"] += 1
        if calls["count"] == backup_count + 2:
            raise OSError("injected write-phase failure")
        return original_copy2(source, destination, *args, **kwargs)

    monkeypatch.setattr(shutil, "copy2", fail_during_write)
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

def _group_section_counts(root: Path, kind: str, attribute: str) -> list[int]:
    text = (root / "indexes" / f"{kind}-by-{attribute}.md").read_text(encoding="utf-8")
    return [int(count) for count in re.findall(r"^### .* \((\d+)\)$", text, re.MULTILINE)]


def test_long_and_multiline_text_fields_are_fenced_and_not_markdown(tmp_path):
    world = simple_world(*[entity("Plain", "000000001101")])
    value = "prefix [[Evil]] #tag | --- " + "`" * 3 + "quoted" + "`" * 3 + "\nsecond line"
    world.entities["test:000000001101"]["attributes"].update(
        {
            "short": "plain",
            "long": "L" * 121,
            "payload": value,
        }
    )
    target = tmp_path / "vault"
    export_markdown_vault(world, target)
    note = (target / "test" / "Plain (000000001101).md").read_text(encoding="utf-8")

    assert "- `long`: text field, 121 characters (see Text fields)" in note
    assert f"- `payload`: text field, {len(value)} characters (see Text fields)" in note
    section = note.split("## Text fields", 1)[1].split("## Relationships", 1)[0]
    assert "### `long`" in section
    assert "### `payload`" in section
    fence = "`" * 4
    assert f"{fence}text\n{value}\n{fence}" in section
    assert "[[Evil]]" not in _links_outside_code(section)
    assert "[[Evil]]" not in _mask_code(section)
    assert "#tag" not in _mask_code(section)
    assert "---" not in _mask_code(section)
    assert "short" in note
    assert '"plain"' in note


def test_text_fields_without_backticks_use_three_backtick_fences(tmp_path):
    values = {
        "prose": "First line of prose.\nSecond line of prose.",
        "yaml_like": "before\n---\nafter",
        "injection": "[[Evil]] and #tag\nsecond line",
        "exactly_121": "x" * 121,
    }
    world = simple_world(*[entity("Plain", "000000001102")])
    world.entities["test:000000001102"]["attributes"].update(values)
    target = tmp_path / "vault"
    export_markdown_vault(world, target)
    note = (target / "test" / "Plain (000000001102).md").read_text(encoding="utf-8")
    section = note.split("## Text fields", 1)[1].split("## Relationships", 1)[0]

    for key, value in values.items():
        assert f"- `{key}`: text field, {len(value)} characters (see Text fields)" in note
        block = f"```text\n{value}\n```"
        assert section.count(block) == 1
        assert block in section
        outside = section.replace(block, "")
        assert value not in outside


def test_group_by_code_spans_pad_edge_backticks_and_empty_values(tmp_path):
    values = ["`[[Evil]]", "[[Evil]]`", "`", "", "``x``"]
    world = simple_world(*[entity(f"Entity {i}", f"{1301 + i:012x}") for i in range(len(values))])
    for i, value in enumerate(values):
        world.entities[f"test:{1301 + i:012x}"]["attributes"]["group"] = value
    target = tmp_path / "vault"
    export_markdown_vault(world, target)
    index = (target / "indexes" / "test-by-group.md").read_text(encoding="utf-8")

    expected = {
        "`[[Evil]]": "### `` `[[Evil]] `` (1)",
        "[[Evil]]`": "### `` [[Evil]]` `` (1)",
        "`": "### `` ` `` (1)",
        "": "### `  ` (1)",
        "``x``": "### ``` ``x`` ``` (1)",
    }
    for value, heading in expected.items():
        assert heading in index
        heading_line = next(line for line in index.splitlines() if line == heading)
        assert heading_line == heading
        if "[[Evil]]" in value:
            assert "[[Evil]]" in heading_line
            assert heading_line.index("[[Evil]]") > heading_line.index("``")
            assert heading_line.rindex("[[Evil]]") < heading_line.rindex("``")

    assert sum(_group_section_counts(target, "test", "group")) == len(values)


def test_attribute_and_relationship_field_names_are_code_spans(tmp_path):
    world = simple_world(*[entity("Target", "000000001401")])
    source_value, source_id = entity("Source", "000000001402", refs={"[[Evil]] #tag": "test:000000001401"})
    world.add_entity(source_id, source_value)
    world.entities["test:000000001401"]["attributes"]["[[Evil]] #tag"] = "x" * 121
    target = tmp_path / "vault"
    export_markdown_vault(world, target)

    note = (target / "test" / "Target (000000001401).md").read_text(encoding="utf-8")
    source = (target / "test" / "Source (000000001402).md").read_text(encoding="utf-8")
    assert "- `[[Evil]] #tag`: " in note
    assert "### `[[Evil]] #tag`" in note
    assert "### `[[Evil]] #tag`" in source
    assert "[[Evil]]" not in _links_outside_code(note)
    assert "[[Evil]]" not in _links_outside_code(source)


def test_group_by_indexes_are_categorical_by_name_and_safe(tmp_path):
    world = simple_world(
        *[
            entity("A", "000000001201"),
            entity("B", "000000001202"),
            entity("C", "000000001203"),
            entity("D", "000000001204"),
            entity("Plain", "000000001205", kind="plain"),
        ]
    )
    attrs = world.entities
    attrs["test:000000001201"]["attributes"].update({"type": "a`b", "group": "red"})
    attrs["test:000000001202"]["attributes"].update({"type": "a`b", "group": "blue]]#"})
    attrs["test:000000001203"]["attributes"].update({"type": "z", "group": "red"})
    target = tmp_path / "vault"
    export_markdown_vault(world, target)

    type_index = (target / "indexes" / "test-by-type.md").read_text(encoding="utf-8")
    group_index = (target / "indexes" / "test-by-group.md").read_text(encoding="utf-8")
    assert "### ``a`b`` (2)" in type_index
    assert "### `z` (1)" in type_index
    assert "### (none) (1)" in type_index
    assert "### `blue]]#` (1)" in group_index
    assert "### `red` (2)" in group_index
    assert "### (none) (1)" in group_index
    assert sum(_group_section_counts(target, "test", "type")) == 4
    assert sum(_group_section_counts(target, "test", "group")) == 4
    assert not (target / "indexes" / "plain-by-type.md").exists()
    assert not (target / "indexes" / "plain-by-group.md").exists()

    kind_index = (target / "indexes" / "test.md").read_text(encoding="utf-8")
    root_index = (target / "index.md").read_text(encoding="utf-8")
    for relative in ("indexes/test-by-type.md", "indexes/test-by-group.md"):
        assert relative.removesuffix(".md") in kind_index
        assert relative.removesuffix(".md") in root_index
        assert sum(1 for link in _links_outside_code(kind_index + root_index) if link.split("|", 1)[0] == relative.removesuffix(".md")) == 2

    written = {p.relative_to(target).with_suffix("").as_posix() for p in target.rglob("*.md")}
    for path in target.rglob("*.md"):
        for link in _links_outside_code(path.read_text(encoding="utf-8")):
            assert link.split("|", 1)[0] in written, (path, link)


@pytest.mark.parametrize("source", [THIMALAND, PITHIGY, VIVERIA])
def test_canonical_indexes_are_deterministic_and_marker_burg_counts_sum(tmp_path, source):
    world = WorldState()
    import_fmg_snapshot(world, source)
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

    written = {p.relative_to(a).with_suffix("").as_posix() for p in a.rglob("*.md")}
    for path in a.rglob("*.md"):
        for link in _links_outside_code(path.read_text(encoding="utf-8")):
            assert link.split("|", 1)[0] in written, (path, link)

    for collection in ("markers", "burgs"):
        entity_ids = [
            eid for eid, value in world.entities.items()
            if isinstance(value.get("fmg"), dict) and value["fmg"].get("collection") == collection
        ]
        kinds_for_collection = {eid.split(":", 1)[0] for eid in entity_ids}
        assert len(kinds_for_collection) == 1
        kind = next(iter(kinds_for_collection))
        for attribute in ("type", "group"):
            path = a / "indexes" / f"{kind}-by-{attribute}.md"
            if any(isinstance(world.entities[eid].get("attributes", {}).get(attribute), str) for eid in entity_ids):
                assert path.exists()
                assert sum(_group_section_counts(a, kind, attribute)) == len(entity_ids)
            else:
                assert not path.exists()

def test_markdown_vault_export_does_not_mutate_world_state(tmp_path):
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    before = deepcopy(world)
    export_markdown_vault(world, tmp_path / "vault")
    assert world.entities == before.entities
    assert world.fields == before.fields
    assert world.observations == before.observations
    assert world.provenance == before.provenance
