---
type: experiment
status: experiment
summary: Migrated documentation page; source material retained verbatim for Phase 3 traceability.
related: ["[[index]]"]
---

# Competing Producers

## Competing canonical-state producers experiment

### Question

Can a coarse observation inform a persistent fact while retaining enough information to investigate later invalidation and deterministic re-resolution?

### Method

The existing deterministic prototype terrain → hydrology → settlement suitability → settlement resolution pipeline is run on a 10×10 grid. The terrain field is given a minimal EPSG:4326 spatial grid using the spatial semantics established by the preceding experiment.

A thin Rasterio-backed export adapter projects three Worldloom outputs into a single GeoTIFF:

- terrain elevation;
- hydrology water mask;
- settlement suitability observation.

The suitability observation is rasterised only at the export boundary. It remains an observation in canonical Worldloom state and is not promoted to canonical spatial state merely because it is visualised.

### Measurements / results

The experiment verifies that:

- the adapter imports representative terrain values and spatial metadata;
- provenance identifies the adapter and external source;
- the existing hydrology module consumes the canonical terrain field;
- settlement suitability consumes Worldloom state rather than Rasterio objects;
- changing only the external terrain fixture changes hydrology;
- the hydrology change propagates to settlement suitability;
- the suitability change propagates to the resolved settlement location and founding event;
- repeating the same fixture and configuration produces the same canonical state, observations, entities, events, and provenance;
- the existing production vertical slice remains covered separately in `tests/test_prototype.py`.

### Interpretation

Write-in-place observations are sufficient for this first feasibility experiment. A fingerprint is a useful minimal foundation: later code can compare the current observation payload with the payload that informed a resolved fact. The experiment does not establish whether invalidation should be query-based, event-based, or explicit, nor whether stale facts should be marked, removed, or reconciled.

### Scope

This is deliberately an experiment, not a proposal for a general router or a final composition model. The harness and tests exist to expose current engine behaviour before those broader architectural decisions are made.
