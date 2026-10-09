"""Direct tests for Markdown-vault naming helpers."""

from __future__ import annotations

import pytest

from worldloom.adapters.markdown_vault.naming import (
    build_display_map,
    entity_filename,
    entity_title,
    id_parts,
)


def test_id_parts_accepts_and_normalises_projection_id():
    assert id_parts("place:ABCDEF012345") == ("place", "abcdef012345")


@pytest.mark.parametrize("value", ["place:123", "place:abcdefghijkl", "place:0123456789ab:cd", ":0123456789ab", "place:0123456789ab\n", "place:0123456789ag"])
def test_id_parts_rejects_noncanonical_shapes_with_existing_message(value):
    with pytest.raises(ValueError, match=r"Entity ID is not a projection-compatible kind:12hex ID"):
        id_parts(value)


@pytest.mark.parametrize(
    ("name", "kind", "expected"),
    [
        ("", "place", "Unnamed place"),
        ("   \t ", "place", "Unnamed place"),
        ("A/B:C*D?E\"F<G>H|I#J^K", "place", "ABCDEFGHIJK"),
        ("x" * 100, "place", "x" * 80),
        ("Cafe\u0301", "place", "Café"),
        ("CON.foo", "place", "CON_.foo"),
        ("con", "place", "con_"),
    ],
)
def test_entity_title_sanitises_and_normalises(name, kind, expected):
    assert entity_title({"attributes": {"name": name}}, kind) == expected


def test_entity_filename_format_and_kind():
    assert entity_filename("place:ABCDEF012345", {"attributes": {"name": "North"}}) == (
        "place",
        "North (abcdef012345).md",
    )


def test_build_display_map_unique_qualifier_and_hex_fallbacks():
    entities = {
        "test:000000000001": {"_title": "Same", "refs": {"parent": "place:000000000010"}},
        "test:000000000002": {"_title": "Same", "refs": {"parent": "place:000000000011"}},
        "test:000000000003": {"_title": "Same", "refs": {"parent": "place:000000000010"}},
        "test:000000000004": {"_title": "Same", "refs": {}},
        "place:000000000010": {"_title": "North", "refs": {}},
        "place:000000000011": {"_title": "South", "refs": {}},
        "river:000000000012": {"_title": "Unique", "refs": {}},
    }
    displays, counts = build_display_map(entities)
    assert displays["river:000000000012"] == "Unique"
    assert displays["test:000000000002"] == "Same (South)"
    assert displays["test:000000000001"] == "Same (North, 000000000001)"
    assert displays["test:000000000003"] == "Same (North, 000000000003)"
    assert displays["test:000000000004"] == "Same (000000000004)"
    assert counts["test"] == {"qualifier": 1, "hex": 3}
    assert counts["place"] == {"qualifier": 0, "hex": 0}
