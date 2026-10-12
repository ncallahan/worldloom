from __future__ import annotations

from types import SimpleNamespace

from worldloom.adapters.markdown_vault.notes import render_note


def _note(entity=None, *, entities=None, paths=None, displays=None, inverse=None, provenance=None):
    entity_id = "place:000000000001"
    value = {"_title": "North", "attributes": {"name": "North"}, "refs": {}}
    if entity is not None:
        value.update(entity)
    all_entities = {entity_id: value} if entities is None else entities
    return render_note(
        entity_id, value, all_entities,
        {entity_id: "place/North (000000000001).md"} if paths is None else paths,
        {entity_id: "North"} if displays is None else displays,
        {} if inverse is None else inverse,
        provenance,
    )


def test_frontmatter_order_omissions_and_numeric_coordinates():
    text = _note({"fmg": {"collection": "places", "id": 9}, "attributes": {"name": "North", "x": 2, "y": "3", "z": 4}})
    keys = [line.split(":", 1)[0] for line in text.split("---", 2)[1].splitlines() if line and not line.startswith("  ")]
    assert keys == ["worldloom_generated", "worldloom_id", "worldloom_kind", "worldloom_projection_version", "aliases", "fmg_collection", "fmg_id", "fmg_x"]
    assert "fmg_y:" not in text and "fmg_z:" not in text and "fmg_position:" not in text


def test_long_and_multiline_text_fields_are_summarised_and_fenced():
    value = "line one\nline two " + "`" * 3
    text = _note({"attributes": {"name": "North", "long": "x" * 121, "multi": value}})
    assert "- `long`: text field, 121 characters (see Text fields)" in text
    assert f"- `multi`: text field, {len(value)} characters (see Text fields)" in text
    assert "### `long`" in text and "### `multi`" in text
    assert "````text\n" + value + "\n````" in text


def test_hostile_attribute_keys_and_values_are_fenced():
    text = _note({"attributes": {"name": "North", "[[evil]] | #tag": "x" * 121, "payload": "[[evil]]\n# injected"}})
    assert "### `[[evil]] | #tag`" in text
    assert "```text\n[[evil]]\n# injected\n```" in text


def test_relationship_sort_mesh_plain_text_and_dangling_omitted():
    entities = {
        "place:000000000001": {"_title": "North", "attributes": {"name": "North"}, "refs": {"parent": ["place:000000000003", {"space": "pack.cells", "index": 4}, "missing:000000000000", "place:000000000002"]}},
        "place:000000000002": {"_title": "alpha", "attributes": {"name": "alpha"}, "refs": {}},
        "place:000000000003": {"_title": "Beta", "attributes": {"name": "Beta"}, "refs": {}},
    }
    paths = {key: key.replace(":", "/") + ".md" for key in entities}
    displays = {"place:000000000001": "North", "place:000000000002": "alpha", "place:000000000003": "Beta"}
    text = _note(entity=entities["place:000000000001"], entities=entities, paths=paths, displays=displays)
    section = text.split("## Relationships", 1)[1].split("## Derived", 1)[0]
    assert section.index("|alpha]]") < section.index("|Beta]]") < section.index("pack.cells 4")
    assert "[[pack.cells" not in section and "missing" not in section


def test_none_relationships_non_dict_refs_and_inverse_refs():
    assert "- None" in _note().split("## Relationships", 1)[1].split("## Derived", 1)[0]
    text = _note({"refs": []})
    assert "- None" in text.split("## Relationships", 1)[1].split("## Derived", 1)[0]
    assert "- None" in text.split("Referenced by", 1)[1].split("## Provenance", 1)[0]


def test_referenced_by_groups_and_provenance_variants_and_import_record():
    entity_id = "place:000000000001"
    source_id = "burg:000000000002"
    entities = {
        entity_id: {"_title": "North", "attributes": {"name": "North"}, "refs": {}},
        source_id: {"_title": "Village", "attributes": {"name": "Village"}, "refs": {}},
    }
    provenance = SimpleNamespace(producer="importer", inputs=("source.json",), configuration={"importer_version": "1", "mode": "test"})
    text = render_note(entity_id, entities[entity_id], entities,
        {entity_id: "place/North.md", source_id: "burg/Village.md"},
        {entity_id: "North", source_id: "Village"},
        {entity_id: [("burg", "state", source_id)]}, provenance)
    assert "### burg / `state`" in text and "[[burg/Village|Village]]" in text
    assert "- producer:" in text and "- inputs:" in text and "- configuration:" in text
    assert "- import record: [[_worldloom/import|_worldloom/import]]" in text
    absent = _note()
    assert "## Provenance\n- None" in absent
    assert "- configuration:" not in absent

def _derived_section(text):
    return text.split("## Derived from", 1)[1].split("## Provenance", 1)[0]


def test_derived_from_section_links_inputs_and_reports_fingerprint_status():
    from worldloom.core.hashing import fingerprint

    parent_id = "burg:000000000001"
    ward_id = "ward:000000000002"
    parent = {"_title": "Harbour", "attributes": {"population": 10}, "refs": {}}
    ward = {"_title": "Ward", "attributes": {"population": 10}, "refs": {}}
    entities = {parent_id: parent, ward_id: ward}
    paths = {parent_id: "burg/Harbour.md", ward_id: "ward/Ward.md"}
    displays = {parent_id: "Harbour", ward_id: "Ward"}
    provenance = SimpleNamespace(
        producer="test.generator",
        inputs=(f"entity:{parent_id}",),
        configuration={"version": "1", "input_fingerprints": {f"entity:{parent_id}": fingerprint(parent)}},
    )
    text = render_note(ward_id, ward, entities, paths, displays, {}, provenance,
                       {parent_id: provenance.configuration["input_fingerprints"][f"entity:{parent_id}"]})
    section = _derived_section(text)
    assert section.strip() == "- [[burg/Harbour|Harbour]]: current"
    assert "producer" not in section and "configuration" not in section
    assert f"- version: {safe_text(\"1\")}" in text.split("## Provenance", 1)[1]

    stale = render_note(ward_id, ward, entities, paths, displays, {}, provenance, {parent_id: "different"})
    stale_section = _derived_section(stale)
    assert stale_section.strip() == "- [[burg/Harbour|Harbour]]: stale (input changed since resolution)"
    assert "current" not in stale_section
    missing = render_note(
        ward_id, ward, {ward_id: ward}, {ward_id: paths[ward_id]},
        {ward_id: displays[ward_id]}, {}, provenance, {}
    )
    assert _derived_section(missing).strip() == f"- {safe_text(parent_id)}: input missing"
    no_fp = SimpleNamespace(producer="test.generator", inputs=(f"entity:{parent_id}",), configuration={"version": "1"})
    no_record = render_note(ward_id, ward, entities, paths, displays, {}, no_fp, {parent_id: fingerprint(parent)})
    assert _derived_section(no_record).strip() == "- [[burg/Harbour|Harbour]]: no recorded fingerprint"


def test_derived_from_tolerates_malformed_provenance_and_unavailable_fingerprints():
    ward_id = "ward:000000000002"
    parent_id = "burg:000000000001"
    ward = {"_title": "Ward", "attributes": {}, "refs": {}}
    parent = {"_title": "Harbour", "attributes": {}, "refs": {}}
    entities = {ward_id: ward, parent_id: parent}
    paths = {ward_id: "ward/Ward.md", parent_id: "burg/Harbour.md"}
    displays = {ward_id: "Ward", parent_id: "Harbour"}
    inputs = (f"entity:{parent_id}",)
    malformed = [
        SimpleNamespace(producer="test", inputs=inputs, configuration="not-a-mapping"),
        SimpleNamespace(producer="test", inputs=inputs, configuration={"input_fingerprints": []}),
        SimpleNamespace(producer="test", inputs=inputs, configuration={"input_fingerprints": {f"entity:{parent_id}": 42}}),
    ]
    for provenance in malformed:
        text = render_note(ward_id, ward, entities, paths, displays, {}, provenance, {parent_id: "fingerprint"})
        assert _derived_section(text).strip() == "- [[burg/Harbour|Harbour]]: no recorded fingerprint"

    unavailable = render_note(
        ward_id, ward, entities, paths, displays, {}, malformed[2], {}
    )
    assert _derived_section(unavailable).strip() == "- [[burg/Harbour|Harbour]]: fingerprint unavailable"


def test_missing_input_status_precedes_missing_recorded_fingerprint():
    ward_id = "ward:000000000002"
    parent_id = "burg:000000000001"
    ward = {"_title": "Ward", "attributes": {}, "refs": {}}
    provenance = SimpleNamespace(
        producer="test", inputs=(f"entity:{parent_id}",), configuration={}
    )
    text = render_note(
        ward_id, ward, {ward_id: ward}, {ward_id: "ward/Ward.md"},
        {ward_id: "Ward"}, {}, provenance, {}
    )
    assert _derived_section(text).strip() == f"- {safe_text(parent_id)}: input missing"


def test_derived_from_ignores_malformed_input_list():
    ward_id = "ward:000000000002"
    ward = {"_title": "Ward", "attributes": {}, "refs": {}}
    provenance = SimpleNamespace(producer="test", inputs=(object(),),
                                 configuration="not-a-mapping")
    text = render_note(ward_id, ward, {ward_id: ward}, {ward_id: "ward/Ward.md"},
                       {ward_id: "Ward"}, {}, provenance, {})
    assert "## Derived from" not in text
