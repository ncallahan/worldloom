---
type: experiment
status: experiment
summary: Experiment record migrated verbatim from docs/EXPERIMENTS.md.
related: ["[[index]]"]
---

## End-to-end GIS export experiment

### Question

Can the existing small Worldloom simulation pipeline produce a tangible, georeferenced map artifact that can be opened directly by an established GIS application?

### Method

The existing deterministic prototype terrain → hydrology → settlement suitability → settlement resolution pipeline is run on a 10×10 grid. The terrain field is given a minimal EPSG:4326 spatial grid using the spatial semantics established by the preceding experiment.

A thin Rasterio-backed export adapter projects three Worldloom outputs into a single GeoTIFF:

- terrain elevation;
- hydrology water mask;
- settlement suitability observation.

The suitability observation is rasterised only at the export boundary. It remains an observation in canonical Worldloom state and is not promoted to canonical spatial state merely because it is visualised.

### Measurements / results

The export test verifies that the resulting file is a readable GeoTIFF with:

- 10×10 dimensions;
- EPSG:4326 CRS;
- the expected affine transform;
- three named bands;
- values matching the Worldloom terrain and water fields;
- suitability values mapped to their corresponding grid cells.

The exporter does not mutate the Worldloom state, and the example can generate the artifact from the command line.

### Interpretation

**Demonstrated**

Worldloom now has a small complete path from procedural world generation through causal simulation to a concrete GIS-ready file. GIS-specific encoding remains behind an adapter boundary, while the simulation modules continue to exchange ordinary Worldloom state.

This is deliberately an integration proof rather than a decision that GeoTIFF is Worldloom's universal interchange format.

**Still open**

This experiment does not settle:

- the final GIS exchange formats;
- vector export;
- packaging of entities and events alongside raster fields;
- whether derived raster observations should eventually carry their own spatial semantics;
- CRS transformation policy;
- large-data or streaming behaviour;
- round-trip editing from GIS back into Worldloom.
