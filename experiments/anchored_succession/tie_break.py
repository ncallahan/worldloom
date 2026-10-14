"""Keyed tie-break coefficients shared by solver adapters and integrity tests."""
from __future__ import annotations
from worldloom.core import Address, rng_for

def cp_sat_tie_coefficient(seed: int, layer: str, person_id: str, year: int) -> int:
    address=Address(("anchored-succession","cp-sat-tie",layer,person_id,str(year)))
    return rng_for(seed,"worldloom.anchored_succession.cp_sat","1",address,"coefficient").randint(1,100)

def clingo_tie_weight(seed: int, generator_id: str, generator_version: str,
                      layer: str, person_id: str, year: int) -> int:
    address=Address(("anchored-succession","clingo-tie",layer,person_id,str(year)))
    return rng_for(seed,generator_id,generator_version,address,"coefficient").randint(1,100)
