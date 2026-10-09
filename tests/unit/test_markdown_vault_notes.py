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
