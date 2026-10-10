from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

from worldloom.adapters import export_markdown_vault
from worldloom.adapters.markdown_vault.prepare import prepare_projection_input
from worldloom.core import Address, WorldState
from worldloom.core.provenance import Provenance


def world(entities=None, **kwargs):
    return WorldState(entities=entities or {}, **kwargs)


def text_tree(root: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in root.rglob("*.md"))


@pytest.mark.parametrize("eid", ["settlement:001", "not-a-valid-id", ":abc", "../x:0123456789ab", "place-猫:0123456789ab", "p"*60+"猫:0123456789ab"])
def test_nonstandard_ids_export_safely(tmp_path, eid):
    out = tmp_path / "vault"
    summary = export_markdown_vault(world({eid: {"attributes": {"name": "Distinct"}, "refs": {}}}), out)
    note = next(out.rglob("Distinct (*.md"))
    assert ".." not in note.relative_to(out).as_posix()
    assert summary and summary.by_kind["nonstandard-id"]["count"] == 1


def test_non_string_id_and_sanitised_collision_abort(tmp_path):
    with pytest.raises(ValueError, match=r"Entity ID must be a string: 123"):
        export_markdown_vault(world({123: {"attributes": {}, "refs": {}}}), tmp_path / "bad")
    left, right = "bad" + chr(0xD800), "bad\ufffd"
    with pytest.raises(ValueError, match="Sanitized entity ID collision"):
        export_markdown_vault(world({left: {"attributes": {}, "refs": {}}, right: {"attributes": {}, "refs": {}}}), tmp_path / "collision")


def test_reference_to_nonstandard_id_is_rewritten(tmp_path):
    w = world({
        "settlement:001": {"attributes": {"name": "North"}, "refs": {}},
        "test:000000000001": {"attributes": {"name": "South"}, "refs": {"neighbour": "settlement:001"}},
    })
    out = tmp_path / "vault"
    export_markdown_vault(w, out)
    assert "[[settlement/North (" in next(out.glob("test/South*.md")).read_text(encoding="utf-8")


def test_surrogates_in_rendered_sources_are_replaced(tmp_path):
    bad = "x" + chr(0xD800)
    w = world({"test:000000000001": {
        "attributes": {"name": "Plain", "badkey" + chr(0xD800): {"nested" + chr(0xD800): [bad]}},
        "refs": {"raw": bad}, "fmg": {"collection": bad, "id": bad, "position": bad}},
        "test:" + bad: {"attributes": {"name": "Emoji 😀"}, "refs": {}}},
        fields={"fmg.source": {"metadata": bad}},
        observations={"fmg.import.report": {"diagnostics": {"bad" + chr(0xD800): bad}}},
        provenance={"entity:test:000000000001": Provenance(producer=bad, inputs=(bad,), configuration={"bad" + chr(0xD800): bad})})
    out = tmp_path / "vault"
    summary = export_markdown_vault(w, out)
    rendered = text_tree(out)
    assert not any(0xD800 <= ord(ch) <= 0xDFFF for ch in rendered)
    assert "\ufffd" in rendered and "😀" in rendered and summary and summary.by_kind["lone-surrogate"]["count"] == 15
    prepared = prepare_projection_input(w)
    assert "entities[0].attributes.badkey\ufffd" in prepared.anomalies["lone-surrogate"]


def test_sanitised_dict_key_collision_retains_both_entries(tmp_path):
    attrs = {"name": "Plain", "key" + chr(0xD800): "first", "key\ufffd": "second", "key\ufffd (duplicate 2)": "occupied"}
    out = tmp_path / "vault"
    summary = export_markdown_vault(world({"test:000000000001": {"attributes": attrs, "refs": {}}}), out)
    note = next(out.glob("test/*.md")).read_text(encoding="utf-8")
    assert "key\ufffd (duplicate 3)" in note
    assert summary and summary.by_kind["key-collision"]["count"] == 1


def test_json_coercion_and_safe_value_preservation(tmp_path):
    class Odd:
        pass
    attrs = {"name": "Values", "set": {"z", "a", "m"}, "frozen": frozenset({3, 1}),
        "bytes": b"\x00\xff", "address": Address.cell(1, 2), "tuple": ("a", 2),
        "integer_keys": {2: "two", 1: "one"}, "mixed_keys": {1: "int", "1": "str"},
        "nan": math.nan, "infinity": math.inf, "odd": Odd()}
    w = world({"test:000000000001": {"attributes": attrs, "refs": {}}})
    prepared = prepare_projection_input(w)
    assert prepared.anomalies["coerced-value"]["entities[0].attributes.set"] == 1
    assert prepared.anomalies["coerced-value"]["entities[0].attributes.frozen"] == 1
    assert prepared.anomalies["coerced-value"]["entities[0].attributes.bytes"] == 1
    assert prepared.anomalies["coerced-value"]["entities[0].attributes.address"] == 1
    assert "entities[0].attributes.integer_keys" not in prepared.anomalies.get("coerced-value", {})
    assert prepared.anomalies["nonserialisable-value"]["entities[0].attributes.nan"] == 1
    assert prepared.anomalies["nonserialisable-value"]["entities[0].attributes.odd"] == 1
    assert prepared.anomalies["key-collision"]["entities[0].attributes.mixed_keys"] == 1
    a, b = tmp_path / "a", tmp_path / "b"
    export_markdown_vault(w, a); export_markdown_vault(w, b)
    files = lambda root: {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert files(a) == files(b)
    note = next(a.glob("test/*.md")).read_text(encoding="utf-8")
    assert "bytes:00ff" in note
    assert Address.cell(1, 2).canonical in note
    assert f"<{Odd.__module__}.{Odd.__qualname__}>" in note


def test_malformed_entity_shapes_are_tolerated(tmp_path):
    w = world({
        "test:000000000001": "scalar",
        "test:000000000002": {"attributes": ["bad"], "refs": "bad"},
        "test:000000000003": {"attributes": {"name": "Refs"}, "refs": None},
    })
    out = tmp_path / "vault"
    summary = export_markdown_vault(w, out)
    assert summary and summary.by_kind["nonstandard-entity-shape"]["count"] == 4
    assert "- None" in next(out.glob("test/Unnamed test*.md")).read_text(encoding="utf-8")
    assert "## Relationships\n- None" in next(out.glob("test/Refs*.md")).read_text(encoding="utf-8")


def test_fingerprint_fallback_and_projection_anomaly_surface(tmp_path):
    w = world({"test:000000000001": {"attributes": {"name": "Plain", "value": {1, 2}}, "refs": {}}},
        fields={"unrendered": "bad" + chr(0xD800)})
    a, b = tmp_path / "a", tmp_path / "b"
    summary = export_markdown_vault(w, a); export_markdown_vault(w, b)
    assert summary and summary.by_kind["fingerprint-fallback"]["count"] == 1
    ma = json.loads((a / ".worldloom-vault.json").read_text())
    mb = json.loads((b / ".worldloom-vault.json").read_text())
    assert ma["world_fingerprint"] == mb["world_fingerprint"]
    assert (a / "_worldloom/anomalies.md").is_file()
    assert "Import anomalies: 0 errors, 1 warnings" in (a / "index.md").read_text(encoding="utf-8")


def test_projection_anomalies_merge_with_import_report(tmp_path):
    report = {"entities": {"anomalies": {"counts": {"sentinel": {"pack.cells[0]": 1}}}}}
    w = world({"test:000000000001": {"attributes": {"name": "Plain", "value": {1, 2}}, "refs": {}}},
        observations={"fmg.import.report": report})
    summary = export_markdown_vault(w, tmp_path / "vault")
    assert summary and summary.by_block["projection"] == 1 and summary.by_kind["sentinel"]["count"] == 1
    import_note = (tmp_path / "vault/_worldloom/import.md").read_text(encoding="utf-8")
    anomalies_note = (tmp_path / "vault/_worldloom/anomalies.md").read_text(encoding="utf-8")
    index = (tmp_path / "vault/index.md").read_text(encoding="utf-8")
    assert "### Info (2)" in import_note
    assert "coerced-value" in anomalies_note and "sentinel" in anomalies_note
    assert index.startswith("# Worldloom")


def test_integer_keyed_mappings_remain_json_safe_and_renderable(tmp_path):
    w = world({
        "test:000000000001": {"attributes": {1: "one", 2: "two"}, "refs": {1: "place:000000000002"}},
        "place:000000000002": {"attributes": {"name": "North"}, "refs": {}},
    })
    out = tmp_path / "vault"
    summary = export_markdown_vault(w, out)
    assert summary is None
    note = next(out.glob("test/Unnamed test*.md")).read_text(encoding="utf-8")
    assert "`1`: " in note
    assert "Referenced by" in next(out.glob("place/North*.md")).read_text(encoding="utf-8")


def test_raw_world_fingerprint_is_preserved_for_valid_world(tmp_path):
    report = {"entities": {"anomalies": {"counts": {}}}}
    w = world(
        {"test:000000000001": {"attributes": {"name": "Plain"}, "refs": {}}},
        fields={"fmg.source": {"map_id": "valid"}},
        observations={"fmg.import.report": report},
    )
    expected = w.fingerprint({
        "entities": w.entities, "fields": w.fields, "observations": w.observations
    })
    out = tmp_path / "vault"
    summary = export_markdown_vault(w, out)
    marker = json.loads((out / ".worldloom-vault.json").read_text(encoding="utf-8"))
    assert marker["world_fingerprint"] == expected
    assert summary is not None and summary.total == 0
    assert "projection" not in w.observations["fmg.import.report"]


def test_json_safe_nonstring_fmg_collection_does_not_abort(tmp_path):
    w = world({
        "test:000000000001": {
            "attributes": {"name": "Odd collection"},
            "refs": {},
            "fmg": {"collection": ["odd", "collection"]},
        }
    })
    out = tmp_path / "vault"
    summary = export_markdown_vault(w, out)
    assert summary is None
    import_note = (out / "_worldloom/import.md").read_text(encoding="utf-8")
    assert '- ["odd","collection"]: 1' in import_note


def test_set_coercion_is_stable_across_hash_seeds(tmp_path):
    script = textwrap.dedent("""
        import sys
        from pathlib import Path
        from worldloom.adapters import export_markdown_vault
        from worldloom.core import WorldState

        output = Path(sys.argv[1])
        values = set(sys.argv[2].split(","))
        world = WorldState(entities={
            "test:000000000001": {
                "attributes": {"name": "Stable", "values": values},
                "refs": {},
            }
        })
        export_markdown_vault(world, output)
    """)
    outputs = [tmp_path / "seed-one", tmp_path / "seed-two"]
    for output, seed, order in zip(outputs, ("1", "2"), ("z,a,m", "m,z,a")):
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = seed
        subprocess.run(
            [sys.executable, "-c", script, str(output), order],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
    files = lambda root: {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    assert files(outputs[0]) == files(outputs[1])


def test_extra_entity_fields_are_prepared_and_fingerprint_fallback_is_stable(tmp_path):
    class Odd:
        pass

    bad = "source" + chr(0xD800)
    entity = {
        "attributes": {"name": "Extra fields"},
        "refs": {},
        "extra_object": Odd(),
        "extra_set": {"z", "a", "m"},
        "extra_surrogate": bad,
    }
    outputs = [tmp_path / "extra-a", tmp_path / "extra-b"]
    summaries = [
        export_markdown_vault(world({"test:000000000001": entity}), output)
        for output in outputs
    ]
    markers = [
        json.loads((output / ".worldloom-vault.json").read_text(encoding="utf-8"))
        for output in outputs
    ]
    assert markers[0]["world_fingerprint"] == markers[1]["world_fingerprint"]
    assert summaries[0] and summaries[0].by_kind["fingerprint-fallback"]["count"] == 1
    assert summaries[0].by_kind["nonserialisable-value"]["patterns"]["entities[].extra_object"]["paths"] == ["entities[0].extra_object"]
    assert summaries[0].by_kind["coerced-value"]["patterns"]["entities[].extra_set"]["paths"] == ["entities[0].extra_set"]
    assert summaries[0].by_kind["lone-surrogate"]["patterns"]["entities[].extra_surrogate"]["paths"] == ["entities[0].extra_surrogate"]


def test_nonmapping_fmg_is_prepared_and_fingerprint_fallback_is_stable(tmp_path):
    class Odd:
        pass

    outputs = [tmp_path / "fmg-a", tmp_path / "fmg-b"]
    summaries = [
        export_markdown_vault(
            world({"test:000000000001": {
                "attributes": {"name": "Bad FMG"}, "refs": {}, "fmg": Odd()
            }}),
            output,
        )
        for output in outputs
    ]
    markers = [
        json.loads((output / ".worldloom-vault.json").read_text(encoding="utf-8"))
        for output in outputs
    ]
    assert markers[0]["world_fingerprint"] == markers[1]["world_fingerprint"]
    assert summaries[0] and summaries[0].by_kind["fingerprint-fallback"]["count"] == 1
    assert summaries[0].by_kind["nonstandard-entity-shape"]["patterns"]["entities[].fmg"]["paths"] == ["entities[0].fmg"]
    assert summaries[0].by_kind["nonserialisable-value"]["patterns"]["entities[].fmg"]["paths"] == ["entities[0].fmg"]


def test_long_string_surrogate_fast_paths_preserve_exact_text():
    from worldloom.adapters.markdown_vault.prepare import _clean_key, _clean_string
    from worldloom.adapters.markdown_vault.exporter import _has_lone_surrogate

    ascii_text = "a" * 100_000
    unicode_text = "é猫" * 50_000
    bad_ascii = ascii_text + chr(0xD800)
    bad_unicode = unicode_text + chr(0xDFFF)
    anomalies = {}
    assert _clean_string(ascii_text, "ascii", anomalies) is ascii_text
    assert _clean_string(unicode_text, "unicode", anomalies) is unicode_text
    assert _clean_string(bad_ascii, "bad-ascii", anomalies) == ascii_text + "\ufffd"
    assert _clean_key(bad_unicode, "keys", anomalies) == unicode_text + "\ufffd"
    assert anomalies == {
        "lone-surrogate": {"bad-ascii": 1, "keys." + unicode_text + "\ufffd": 1}
    }
    assert not _has_lone_surrogate(ascii_text)
    assert not _has_lone_surrogate(unicode_text)
    assert _has_lone_surrogate(bad_ascii)
    assert _has_lone_surrogate(bad_unicode)


@pytest.mark.parametrize("inputs,expected_kind", [
    (7, "nonserialisable-value"),
    (None, "nonserialisable-value"),
    ({"z", "a"}, "coerced-value"),
])
def test_duck_typed_provenance_inputs_are_prepared_independently(
    tmp_path, inputs, expected_kind
):
    provenance = SimpleNamespace(
        producer="test producer",
        inputs=inputs,
        configuration={"mode": "test"},
    )
    w = world(
        {"test:000000000001": {"attributes": {"name": "Provenance"}, "refs": {}}},
        provenance={"entity:test:000000000001": provenance},
    )
    summary = export_markdown_vault(w, tmp_path / "vault")
    assert summary is not None
    assert summary.by_kind[expected_kind]["patterns"]["provenance[].inputs"]["paths"] == ["provenance[0].inputs"]
    note = next((tmp_path / "vault").glob("test/*.md")).read_text(encoding="utf-8")
    assert "## Provenance" in note
