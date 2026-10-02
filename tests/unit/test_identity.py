from __future__ import annotations

from tests.test_support import SETTLEMENT_IDENTITY

import pytest

from worldloom.core import derive_entity_id, find_entity_by_alias


def test_derived_entity_id_has_stable_format():
    assert derive_entity_id("settlement", *SETTLEMENT_IDENTITY) == (
        "settlement:249f0b1fa0e6"
    )


def test_identity_does_not_depend_on_selected_answer():
    identity = SETTLEMENT_IDENTITY
    first = derive_entity_id("settlement", *identity)
    second = derive_entity_id("settlement", *identity)
    assert first == second


def test_identity_changes_when_resolution_question_changes():
    baseline = derive_entity_id("settlement", *SETTLEMENT_IDENTITY)
    assert derive_entity_id("settlement", "region:b", *SETTLEMENT_IDENTITY[1:]) != baseline
    assert derive_entity_id("settlement", SETTLEMENT_IDENTITY[0], "role:market", SETTLEMENT_IDENTITY[2]) != baseline
    assert derive_entity_id("settlement", SETTLEMENT_IDENTITY[0], SETTLEMENT_IDENTITY[1], "slot:002") != baseline


def test_entity_id_kind_is_validated():
    with pytest.raises(ValueError, match="must not contain"):
        derive_entity_id("settlement:bad", "slot:001")


def test_alias_lookup_returns_entity_id():
    entities = {
        "settlement:abcdef012345": {"alias": "settlement:001"},
        "settlement:fedcba987654": {"alias": "settlement:002"},
    }

    assert find_entity_by_alias(entities, "settlement:001") == "settlement:abcdef012345"
    assert find_entity_by_alias(entities, "settlement:missing") is None


def test_duplicate_aliases_are_rejected():
    entities = {
        "settlement:abcdef012345": {"alias": "settlement:001"},
        "settlement:fedcba987654": {"alias": "settlement:001"},
    }

    with pytest.raises(ValueError, match="Duplicate entity alias"):
        find_entity_by_alias(entities, "settlement:001")
