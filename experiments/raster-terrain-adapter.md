---
type: experiment
status: experiment
summary: Migrated documentation page; source material retained verbatim for Phase 3 traceability.
related: ["[[index]]"]
---

# Raster Terrain Adapter

## Raster terrain adapter causal integration experiment

### Question

Can a coarse observation inform a persistent fact while retaining enough information to investigate later invalidation and deterministic re-resolution?

### Implementation

The existing Rasterio-backed terrain adapter is exercised with a small deterministic GeoTIFF fixture. Rasterio handles the external raster representation and its geospatial metadata; the adapter writes the first band to the existing `terrain.elevation` canonical field and records source identity, shape, CRS, transform, and simulation time in existing provenance.

The test wraps the adapter as the terrain provider for the existing `prototype.terrain` module contract. No changes are made to the hydrology, settlement-suitability, or settlement-resolution implementations.

Two otherwise identical 10×10 fixtures place the low-elevation/water cell at different locations. Each fixture is run through the real downstream modules and settlement resolution.

### Configuration

- External representation: single-band GeoTIFF.
- Raster dimensions: 10×10.
- CRS: EPSG:4326.
- Cell size: 0.5 degrees.
- Elevation: 9.0 everywhere except one 4.0 cell.
- Simulation time: 12 for causal and determinism tests.
- No external GUI GIS application is required.

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

### Limitations

The fixture is deliberately small and uses Rasterio directly rather than a full GIS application. The downstream prototype modules currently operate on simple nested Python values and do not themselves consume CRS or transform metadata. The experiment therefore proves the adapter boundary and causal exchange, not a complete geospatial interoperability model.
