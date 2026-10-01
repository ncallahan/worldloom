from __future__ import annotations

from worldloom.core import Address, rng_for


GENERATOR_ID = "experiment.keyed_randomness"
GENERATOR_VERSION = "1"
SEED = 12345


def _value_for(address: Address, purpose: str) -> tuple[float, float]:
    rng = rng_for(SEED, GENERATOR_ID, GENERATOR_VERSION, address, purpose)
    return rng.random(), rng.random()


def _resolve(addresses: tuple[Address, ...]) -> dict[str, tuple[float, float]]:
    return {
        str(address): _value_for(address, "candidate")
        for address in addresses
    }


def test_experiment_resolves_same_addresses_independently_of_order():
    address_a = Address(("experiment", "region", "a"))
    address_b = Address(("experiment", "region", "b"))

    forward = _resolve((address_a, address_b))
    reverse = _resolve((address_b, address_a))

    assert forward == reverse


def test_experiment_isolated_from_unrelated_addresses():
    address_a = Address(("experiment", "region", "a"))
    address_b = Address(("experiment", "region", "b"))
    unrelated = Address(("experiment", "region", "unrelated"))

    before = _resolve((address_a, address_b))
    _resolve((unrelated, address_a, address_b))
    after = _resolve((address_a, address_b))

    assert after == before


def test_experiment_keeps_purposes_as_independent_random_streams():
    address = Address(("experiment", "region", "a"))

    candidate = _value_for(address, "candidate")
    climate = _value_for(address, "climate")

    assert candidate != climate
