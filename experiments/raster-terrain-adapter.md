---
type: experiment
status: experiment
summary: Experiment record migrated verbatim from docs/EXPERIMENTS.md.
related: ["[[index]]"]
---

## Raster terrain adapter causal integration experiment

### Question

Can an established external terrain/GIS representation enter Worldloom through a thin adapter, become canonical Worldloom terrain state, and drive the existing hydrology → settlement suitability → settlement resolution pipeline without downstream modules knowing about the external system?

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

**Demonstrated**

An established raster representation can participate in the existing Worldloom module pipeline through a replaceable adapter boundary. The external representation does not need to become part of downstream module contracts, and the adapter is demonstrably in the causal path rather than merely loading unused data.

The experiment therefore strengthens the existing adapter-first architectural conclusion: specialist raster/GIS functionality can remain outside Worldloom while Worldloom owns the canonical state and orchestration boundary.

**Still open**

This experiment does not settle:

- the final spatial data model;
- whether spatial/grid metadata should remain provenance or become part of field semantics when spatial meaning is required downstream;
- final GIS interchange formats;
- coordinate reference system policy;
- spatial indexing;
- raster/vector interoperability;
- large-data handling or streaming/chunking;
- external-tool versioning and reproducible source identity;
- identifier semantics;
- validation semantics;
- whether adapted data should always become canonical state or sometimes remain derived/provisional.

### Limitations

The fixture is deliberately small and uses Rasterio directly rather than a full GIS application. The downstream prototype modules currently operate on simple nested Python values and do not themselves consume CRS or transform metadata. The experiment therefore proves the adapter boundary and causal exchange, not a complete geospatial interoperability model.
