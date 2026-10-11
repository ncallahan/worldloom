"""Provisional deterministic burg-to-ward population resolution."""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

from worldloom.core import Address, Event, Provenance, WorldState, derive_entity_id, rng_for
from worldloom.core.hashing import fingerprint

GENERATOR_ID = "worldloom.detail.burg_wards"
GENERATOR_VERSION = "0.1.0"
QUESTION_ID = "burg.wards"
PRIOR_KEY = "local.burg_wards.prior"
LAYERING_KEY = "local.burg_wards.layering_check"


def _valid_claim(entity: dict[str, Any]) -> tuple[float | None, str | None]:
    attributes = entity.get("attributes")
    if not isinstance(attributes, dict) or "population" not in attributes:
        return None, "missing-population"
    claim = attributes["population"]
    if isinstance(claim, bool) or not isinstance(claim, (int, float)):
        return None, "non-numeric-population"
    if not math.isfinite(claim):
        return None, "non-finite-population"
    if claim <= 0:
        return None, "non-positive-population"
    return float(claim), None


def _burg_ids(world: WorldState, requested: Iterable[str] | None) -> list[str]:
    if requested is not None:
        return sorted(set(requested))
    return sorted(
        entity_id for entity_id, entity in world.entities.items()
        if isinstance(entity.get("fmg"), dict) and entity["fmg"].get("collection") == "burgs"
    )


def _prior(world: WorldState, burg_id: str, claim: float, sigma: float) -> dict[str, Any]:
    prior = world.observations.setdefault(PRIOR_KEY, {})
    if burg_id not in prior:
        prior[burg_id] = {
            "claim": claim, "family": "lognormal",
            "mu": math.log(claim) - sigma * sigma / 2,
            "sigma": sigma, "policy": "mean-preserving",
        }
    return prior[burg_id]


def _resolved_event(world: WorldState, burg_id: str) -> Event | None:
    return next((
        event for event in world.events
        if event.kind == "local_detail.resolved"
        and event.data.get("entity_id") == burg_id
        and event.data.get("question_id") == QUESTION_ID
    ), None)


def _ward_values(seed: int | str, burg_id: str, total: float, count: int, sigma: float) -> list[float]:
    weights = [
        rng_for(
            seed, GENERATOR_ID, GENERATOR_VERSION,
            Address(("entity", burg_id, "ward", f"{slot:03d}")), "population-weight",
        ).lognormvariate(0.0, sigma)
        for slot in range(1, count + 1)
    ]
    weight_sum = sum(weights)
    return [total * weight / weight_sum for weight in weights]


def _add_wards(
    world: WorldState, burg_id: str, burg_fingerprint: str, total: float,
    values: list[float], seed: int | str, burg_sigma: float, ward_sigma: float,
    target_ward_size: float, max_wards: int,
) -> None:
    base_parts = ("question:burg.wards", f"burg:{burg_id}")
    for slot, value in enumerate(values, start=1):
        slot_part = f"slot:{slot:03d}"
        ward_id = derive_entity_id("ward", *base_parts, slot_part)
        world.entities[ward_id] = {
            "kind": "ward",
            "attributes": {"population": value},
            "refs": {"burg": burg_id},
            "local_detail": {"parent_burg_id": burg_id, "slot": slot},
        }
        config = {
            "producer": GENERATOR_ID, "version": GENERATOR_VERSION, "seed": seed,
            "burg_sigma": burg_sigma, "ward_sigma": ward_sigma,
            "target_ward_size": target_ward_size, "max_wards": max_wards,
            "identity_parts": [*base_parts, slot_part],
            "burg_fingerprint": burg_fingerprint, "resolved_total": total,
        }
        world.provenance[ward_id] = Provenance(
            producer=GENERATOR_ID, inputs=(burg_id,), configuration=config,
            time=0.0, fingerprint=burg_fingerprint,
        )


def _resolved_totals(world: WorldState) -> dict[str, float]:
    return {
        event.data["entity_id"]: event.data["resolved_total"]
        for event in world.events
        if event.kind == "local_detail.resolved"
        and event.data.get("question_id") == QUESTION_ID
        and isinstance(event.data.get("entity_id"), str)
        and isinstance(event.data.get("resolved_total"), (int, float))
    }


def _state_entities(world: WorldState) -> dict[Any, tuple[str, dict[str, Any]]]:
    return {
        entity["attributes"].get("i"): (entity_id, entity)
        for entity_id, entity in world.entities.items()
        if isinstance(entity.get("fmg"), dict)
        and entity["fmg"].get("collection") == "states"
        and isinstance(entity.get("attributes"), dict)
    }


def _burgs_in_state(world: WorldState, state_index: Any) -> list[tuple[str, dict[str, Any]]]:
    return [
        (burg_id, burg) for burg_id, burg in world.entities.items()
        if isinstance(burg.get("fmg"), dict)
        and burg["fmg"].get("collection") == "burgs"
        and isinstance(burg.get("attributes"), dict)
        and burg["attributes"].get("state") == state_index
    ]


def _relative_difference(total: float, urban: Any) -> float | None:
    if isinstance(urban, bool) or not isinstance(urban, (int, float)):
        return None
    if not math.isfinite(urban) or urban == 0:
        return None
    return (total - urban) / urban


def _state_layering_check(world: WorldState) -> dict[str, dict[str, Any]]:
    resolved = _resolved_totals(world)
    result = {}
    for state_index, (state_id, state) in _state_entities(world).items():
        burgs = _burgs_in_state(world, state_index)
        totals = [resolved[burg_id] for burg_id, _ in burgs if burg_id in resolved]
        total = sum(totals)
        urban = state["attributes"].get("urban")
        result[state_id] = {
            "urban_claim": urban, "resolved_burg_sum": total,
            "relative_difference": _relative_difference(total, urban),
            "burgs_covered": len(totals), "burgs_total": len(burgs),
        }
    return result


def resolve_burg_wards(
    world: WorldState, seed: int | str, *, burgs: Iterable[str] | None = None,
    burg_sigma: float = 0.15, ward_sigma: float = 0.5,
    target_ward_size: float = 2.0, max_wards: int = 12,
) -> dict[str, Any]:
    """Resolve claimed burg population into deterministic provisional ward entities."""
    if isinstance(seed, bool) or not isinstance(seed, (int, str)):
        raise TypeError("seed must be an integer or string")
    for name, value in (("burg_sigma", burg_sigma), ("ward_sigma", ward_sigma)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and non-negative")
    if isinstance(target_ward_size, bool) or not isinstance(target_ward_size, (int, float)) or not math.isfinite(target_ward_size) or target_ward_size <= 0:
        raise ValueError("target_ward_size must be finite and positive")
    if isinstance(max_wards, bool) or not isinstance(max_wards, int) or max_wards < 1:
        raise ValueError("max_wards must be a positive integer")

    summary: dict[str, Any] = {"resolved": 0, "skipped": [], "already_resolved": 0}
    for burg_id in _burg_ids(world, burgs):
        entity = world.entities.get(burg_id)
        if entity is None:
            summary["skipped"].append({"burg_id": burg_id, "reason": "unknown-burg"})
            continue
        fmg = entity.get("fmg")
        if not isinstance(fmg, dict) or fmg.get("collection") != "burgs":
            summary["skipped"].append({"burg_id": burg_id, "reason": "not-a-burg"})
            continue
        if _resolved_event(world, burg_id) is not None:
            summary["already_resolved"] += 1
            continue
        claim, reason = _valid_claim(entity)
        if reason is not None:
            summary["skipped"].append({"burg_id": burg_id, "reason": reason})
            continue
        assert claim is not None
        burg_fp = fingerprint(entity)
        prior = _prior(world, burg_id, claim, burg_sigma)
        used_sigma = prior["sigma"]
        total = rng_for(
            seed, GENERATOR_ID, GENERATOR_VERSION, Address(("entity", burg_id)), "population"
        ).lognormvariate(prior["mu"], used_sigma)
        count = min(max(math.ceil(total / target_ward_size), 1), max_wards)
        values = _ward_values(seed, burg_id, total, count, ward_sigma)
        _add_wards(
            world, burg_id, burg_fp, total, values, seed, used_sigma,
            ward_sigma, target_ward_size, max_wards,
        )
        world.events.append(Event(
            kind="local_detail.resolved", time=0.0,
            data={
                "entity_id": burg_id, "question_id": QUESTION_ID,
                "resolved_total": total, "producer": GENERATOR_ID,
                "version": GENERATOR_VERSION,
            },
        ))
        summary["resolved"] += 1
    world.observations[LAYERING_KEY] = _state_layering_check(world)
    return summary
