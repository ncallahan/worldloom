"""Provisional keyed randomness for deterministic world experiments.

The generator is keyed by the complete experiment context rather than by a
shared sequential stream. This API is experimental and is not yet part of the
normative Worldloom architecture.
"""

from __future__ import annotations

import hashlib
import random
from typing import Union

from .address import Address

Seed = Union[int, str]


def rng_for(
    seed: Seed | None,
    generator_id: str,
    generator_version: str,
    address: Address,
    purpose: str,
) -> random.Random:
    """Return an independent PRNG stream keyed by the supplied context.

    The key includes every argument, so draws at one address do not depend on
    draws performed for another address or purpose. ``seed=None`` is rejected
    deliberately because an unseeded stream would not provide reproducibility.
    """
    if seed is None:
        raise ValueError("rng_for requires a non-None seed")
    if isinstance(seed, bool) or not isinstance(seed, (int, str)):
        raise TypeError("seed must be an integer or string")
    if not isinstance(generator_id, str) or not isinstance(generator_version, str):
        raise TypeError("generator_id and generator_version must be strings")
    if not isinstance(purpose, str):
        raise TypeError("purpose must be a string")
    if not isinstance(address, Address):
        raise TypeError("address must be an Address")

    key = _encode_key(seed, generator_id, generator_version, address.canonical, purpose)
    return random.Random(hashlib.sha256(key).digest())


def _encode_key(seed: Seed, generator_id: str, generator_version: str, address: str, purpose: str) -> bytes:
    seed_tag = b"int:" if isinstance(seed, int) else b"str:"
    values = (seed_tag + str(seed).encode("utf-8"), generator_id.encode("utf-8"),
              generator_version.encode("utf-8"), address.encode("utf-8"), purpose.encode("utf-8"))
    return b"".join(len(value).to_bytes(8, "big") + value for value in values)