from __future__ import annotations

import pytest

from worldloom.core.address import Address, row_column_to_xy, xy_to_row_column


def test_address_round_trip_and_hierarchy():
    address = Address(("world", "region", "north south"))

    assert address.canonical == "/world/region/north%20south"
    assert Address.parse(address.canonical) == address
    assert address.parent() == Address(("world", "region"))
    assert address.child("settlement") == Address(("world", "region", "north south", "settlement"))
    assert hash(address) == hash(Address.parse(str(address)))


def test_address_escaping_reserved_characters():
    address = Address(("a/b", "percent%value", "question?hash#"))

    assert address.canonical == "/a%2Fb/percent%25value/question%3Fhash%23"
    assert Address.parse(address.canonical) == address


def test_address_rejects_noncanonical_paths():
    with pytest.raises(ValueError):
        Address.parse("world/region")
    with pytest.raises(ValueError):
        Address.parse("/world//region")
    with pytest.raises(ValueError):
        Address.parse("/world/region/")


def test_root_has_no_parent_and_can_have_children():
    root = Address(())
    assert root.canonical == "/"
    assert Address.parse("/") == root
    with pytest.raises(ValueError, match="no parent"):
        root.parent()
    assert root.child("world") == Address(("world",))


def test_address_parse_rejects_noncanonical_lowercase_escape():
    with pytest.raises(ValueError, match="canonical"):
        Address.parse("/a%2fb")


def test_unicode_address_round_trip():
    address = Address(("世界", "café", "naïve"))
    assert Address.parse(address.canonical) == address


def test_address_rejects_non_string_segments():
    with pytest.raises(TypeError, match="segments must be strings"):
        Address(("world", 1))


def test_lone_surrogate_canonicalisation_raises_unicode_encode_error():
    with pytest.raises(UnicodeEncodeError):
        Address(("\\ud800",)).canonical


def test_cell_address_validation_rejects_noncanonical_and_invalid_shapes():
    with pytest.raises(ValueError, match="canonical"):
        Address.parse("/cell/007/1").as_cell()
    with pytest.raises(ValueError, match="grid-cell"):
        Address(("tile", "1", "2")).as_cell()
    with pytest.raises(ValueError, match="non-integer"):
        Address(("cell", "row", "2")).as_cell()


def test_cell_address_uses_row_column_convention():
    address = Address.cell(4, 7)

    assert address.canonical == "/cell/4/7"
    assert address.as_cell() == (4, 7)


def test_cell_xy_conversion_is_explicit_and_does_not_change_existing_convention():
    assert xy_to_row_column(7, 4) == (4, 7)
    assert row_column_to_xy(4, 7) == (7, 4)


@pytest.mark.parametrize(
    "constructor",
    [
        lambda: Address.cell(-1, 0),
        lambda: Address.cell(0, -1),
    ],
)
def test_cell_coordinates_are_nonnegative(constructor):
    with pytest.raises(ValueError, match="non-negative"):
        constructor()


def test_address_is_immutable():
    address = Address(("world",))
    with pytest.raises(AttributeError):
        address.segments = ("other",)


def test_empty_segments_are_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        Address(("world", ""))
