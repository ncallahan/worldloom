from __future__ import annotations

import pytest

from worldloom.core.address import Address
from worldloom.core.rng import rng_for


ADDRESS_A = Address(("world", "region", "a"))
ADDRESS_B = Address(("world", "region", "b"))


def draws(rng):
    return (rng.random(), rng.randrange(1_000_000), rng.random())


def test_same_key_reproduces_identical_draws():
    assert draws(rng_for(42, "terrain", "1", ADDRESS_A, "elevation")) == draws(
        rng_for(42, "terrain", "1", ADDRESS_A, "elevation")
    )


def test_draws_at_one_address_are_independent_of_other_draws():
    expected = draws(rng_for(42, "terrain", "1", ADDRESS_A, "elevation"))

    other = rng_for(42, "terrain", "1", ADDRESS_B, "elevation")
    other.random()
    other.random()
    actual = draws(rng_for(42, "terrain", "1", ADDRESS_A, "elevation"))

    assert actual == expected


@pytest.mark.parametrize(
    "changed",
    [
        {"generator_id": "hydrology"},
        {"generator_version": "2"},
        {"purpose": "temperature"},
        {"seed": 43},
        {"address": ADDRESS_B},
    ],
)
def test_changing_any_key_changes_the_stream(changed):
    kwargs = {
        "seed": 42,
        "generator_id": "terrain",
        "generator_version": "1",
        "address": ADDRESS_A,
        "purpose": "elevation",
    }
    baseline = draws(rng_for(**kwargs))
    kwargs.update(changed)
    assert draws(rng_for(**kwargs)) != baseline


def test_none_seed_is_rejected():
    with pytest.raises(ValueError, match="non-None seed"):
        rng_for(None, "terrain", "1", ADDRESS_A, "elevation")


def test_stream_is_independent_of_request_order():
    first_a = draws(rng_for(42, "terrain", "1", ADDRESS_A, "elevation"))
    first_b = draws(rng_for(42, "terrain", "1", ADDRESS_B, "elevation"))

    second_b = draws(rng_for(42, "terrain", "1", ADDRESS_B, "elevation"))
    second_a = draws(rng_for(42, "terrain", "1", ADDRESS_A, "elevation"))

    assert (first_a, first_b) == (second_a, second_b)