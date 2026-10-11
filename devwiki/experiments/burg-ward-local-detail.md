---
type: experiment
status: experiment
summary: Provisional deterministic resolution of claimed FMG burg populations into ward-level local detail.
related: ["[[devwiki/experiments/fmg-layering-and-references]]", "[[devwiki/experiments/fmg-export-scale-and-structure]]"]
---

# Burg-to-ward local-detail experiment

## Status and scope

This is an experiment record, not architecture. The resolver and defaults are provisional placeholders for testing local detail. It does not alter imported canon, infer population units, modify rural population, or change the importer, SimulationEngine, CLI, vault, or persistence format.

## Measurement context

The prior measurement experiment read the three canonical full exports directly: Thimaland, Pithigy, and Viveria. All are FMG 1.153.1 exports made with identical settings (populationRate = 1000, urbanization = 1, urbanDensity = 10). It observed these aggregate relationships in all three files:

- For each state, states[i].urban equals the sum of burgs[b].population for burgs assigned to that state within floating-point rounding; the maximum relative difference is about 1e-15.
- For each state, states[i].rural equals the sum of cells[c].pop for cells assigned to that state exactly.

These are measured field relationships only. They do not establish that burg or cell values are persons, that values are in the same interpretable unit, or that the fields have a particular semantic meaning.

## Unverified points

- The unit of burgs.population is unverified and is treated as an uninterpreted FMG value. The resolver does no rounding or unit conversion.
- Whether populationRate, urbanization, urbanDensity, or other settings affect the observed relations has not been established.
- FMG 1.154.0 behaviour has not been measured.
- Results from three exports do not establish a general FMG guarantee.

## Resolver design

The function worldloom.detail.burg_wards.resolve_burg_wards(world, seed, *, burgs=None, burg_sigma=0.15, ward_sigma=0.5, target_ward_size=2.0, max_wards=12) is a deterministic, explicitly seeded experiment:

1. It reads the claimed population from the imported burg entity's attributes.population. Missing, non-numeric, non-finite, and non-positive claims are skipped and reported.
2. A burg with a local_detail.resolved event for question burg.wards is already resolved and is a no-op. Matching uses both burg entity ID and question ID.
3. A local.burg_wards.prior derived observation stores the claim and a mean-preserving lognormal prior: mu = ln(claim) - sigma²/2. Existing prior entries are retained and control later draws. A stored prior's claim is not refreshed if the imported burg's claim later changes; this is intentional provisional behaviour.
4. Population and ward-weight draws use rng_for with explicit seed, generator ID/version, and addresses derived from the burg ID or ward slot. IDs depend on the question and slot, never on the sampled answer.
5. Ward count is clamp(ceil(resolved / target_ward_size), 1, max_wards). Independent lognormal ward weights are normalised to sum to the resolved burg total. Wards are unnamed.
6. Ward provenance records producer/version, seed, sigma values, target size, maximum ward count, identity parts, burg fingerprint, and resolved total. The resolution event records the total, seed, the prior sigma actually used, ward sigma, target size, and maximum ward count.
7. local.burg_wards.layering_check is recomputed on each call. It records each state's urban claim, resolved-burg total, signed relative difference where defined, and burg coverage counts. This is informational, not a validation or severity classification.

## Placeholder defaults

- burg_sigma = 0.15
- ward_sigma = 0.5
- target_ward_size = 2.0
- max_wards = 12
- generator version 0.1.0

These defaults are not calibrated, normative, or a commitment to the final identity/address model. The observation does not settle how missing values should eventually be represented. CLI anomaly-severity integration is deferred.

## Negative results and limitations

No inference about units, persons, real ward sizes, FMG settings causality, or FMG 1.154.0 is supported by this experiment. The layering check is a descriptive comparison only. No architecture or persistence decision follows from this page.
