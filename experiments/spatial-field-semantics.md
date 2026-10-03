---
type: experiment
status: experiment
summary: Migrated documentation page; source material retained verbatim for Phase 3 traceability.
related: ["[[index]]"]
---

# Spatial Field Semantics

## Spatial field semantics experiment

### Question

Can a coarse observation inform a persistent fact while retaining enough information to investigate later invalidation and deterministic re-resolution?

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

Write-in-place observations are sufficient for this first feasibility experiment. A fingerprint is a useful minimal foundation: later code can compare the current observation payload with the payload that informed a resolved fact. The experiment does not establish whether invalidation should be query-based, event-based, or explicit, nor whether stale facts should be marked, removed, or reconciled.
