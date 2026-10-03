---
type: experiment
status: experiment
summary: Experiment record migrated verbatim from docs/EXPERIMENTS.md.
related: ["[[index]]"]
---

## Spatial field semantics experiment

### Question

When spatial metadata is part of the meaning of a Worldloom value, rather than merely provenance about where it came from, can a downstream Worldloom module use that meaning without knowing the specialist system that produced the value?

### Candidate representation

This experiment deliberately tests one small representation rather than selecting the final spatial model:

- ordinary non-spatial fields remain plain values;
- a spatial field may have an associated typed SpatialGrid semantic object;
- the grid records shape, CRS, and a six-coefficient affine transform;
- Worldloom exposes cell-centre coordinate lookup through its own state API;
- the specialist adapter remains responsible for translating native GIS metadata into this representation.

The spatial semantic object is stored with canonical world state and is included in snapshots. It is not stored only in provenance.

### Causal test

The Rasterio terrain adapter imports the existing 10×10 GeoTIFF fixture and attaches its grid semantics to terrain.elevation. A downstream test module asks Worldloom for the world coordinate of a selected terrain cell using only the Worldloom field API. The downstream module does not import Rasterio or inspect provenance.

The experiment also verifies that:

- the grid shape, CRS, and derived bounds are available from canonical state;
- cell-centre coordinates are deterministically derived from the grid transform;
- ordinary scalar fields do not acquire spatial wrappers;
- spatial semantics survive snapshot/restore;
- the existing raster → hydrology → suitability → settlement causal path remains intact.

### Interpretation

**Demonstrated**

A small, typed spatial-semantic sidecar can carry enough meaning for a downstream Worldloom module to interpret a grid-backed field without coupling that module to Rasterio or provenance structure.

This is evidence that spatial meaning need not be encoded solely as provenance. It also preserves a simple representation for ordinary scalar/entity values.

**Not decided**

This experiment does not establish the final Worldloom spatial model. In particular, it does not decide:

- whether all spatial data should use this representation;
- how vector geometries should be represented;
- whether fields should eventually be wrapped directly rather than associated with spatial semantics;
- CRS policy and transformation services;
- spatial indexing/query semantics;
- temporal/spatial reference systems beyond this minimal grid case;
- interoperability with external GIS data structures;
- identifier or validation semantics.

The result should therefore inform the eventual spatial-data contract without prematurely fixing it.
