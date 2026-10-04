---
type: experiment
status: experiment
summary: Provisional evidence about explicit FMG spatial representations and boundary transforms.
related: ["[[architecture/adapters]]", "[[architecture/provenance]]", "[[architecture/canonical-state-vs-observation]]"]
---

# FMG spatial representation at the import boundary

## Purpose and question

Test whether the retained Viveria and Pithigy FMG spatial data can cross an explicit Worldloom boundary, pass through an external/geographic representation, and return without ambiguity or meaningful loss, while leaving the future canonical coordinate system open.

This experiment is evidence only. Nothing here is normative architecture.

## Candidate representations

### R1 — FMG map-space retained

FMG x/y is kept verbatim as the provisional Worldloom representation. The geographic transform is explicit and affine.

### R2 — Worldloom-local normalised space

The provisional local representation is centred on the FMG map midpoint, normalised independently in x and y to approximately [-0.5, 0.5], with y increasing northward:

x_local = x / width - 0.5

y_local = 0.5 - y / height

This is deliberately nontrivial so precision, type preservation, and orientation effects are measurable. It is not proposed as the eventual canonical coordinate system.

The external representation is the already-observed FMG mapCoordinates affine longitude/latitude space. No CRS is assigned (crs=None); these are affine geographic values, not a GIS CRS claim.

## Explicit transform object

run.py defines an experiment-local CoordinateTransform with source/target space, affine matrix and offset, axis order, y direction, origin, scale, geographic interpretation, bounds, inversion, and JSON serialisation/reconstruction.

No y flip, origin shift, or scale is implicit.

## Fixture limitation

The slice fixtures do not retain pack-cell centres or pack-vertex coordinates. pack.vertices[].p is absent; pack.cells has no p; and the retained burg records also omit x/y. grid.vertices[].p is retained, so those points are used for distance, centroid, orientation and area-scaling checks, but the slices do not retain enough grid-cell polygon ring membership to reconstruct pack-cell geometry without inventing/reconstructing data.

Accordingly the experiment measures retained marker/route points and grid-vertex points, map bounds, topology, orientation, distances and point-set centroids. Burg coordinate measurements are unavailable in these slice fixtures. It does not fabricate pack-cell polygon areas or pack-vertex positions.

## Reproducibility

Run:

PYTHONPATH=src python experiments/fmg-spatial-boundary/run.py

Configuration is config.yaml. There is no random seed.

Raw output is results/raw-results.json. Raw output must not be overwritten by a later run without recording the change.

## Interpretation boundary

The raw result records measurements only. Conclusions about R1/R2, transform metadata, SpatialGrid, fingerprinting, and whether a canonical system should be fixed are provisional interpretations and belong in the accompanying devwiki draft, not in the raw result.

## Unresolved

- Whether R1 or R2 is preferable at system scale.
- Whether a future Worldloom representation should preserve geographic meaning or remain purely local.
- How full FMG pack-cell geometry should be represented at an importer boundary when complete geometry is available.
- Projection/CRS semantics.
- Canonical-coordinate and world-file choices.


## Execution notes

The first three CI attempts exposed runner defects rather than data failures: the initial scaffold was not on the branch used by the temporary runner workflow; the runner then had a syntax error, used WorldState.restore as a class method instead of an instance method, used the wrong provenance key, and finally had a summary-printing key error. These were corrected before the successful run. The successful experiment run was GitHub Actions run 37181161085 at commit 16f22c5c048599ebbbb877e02fd05635ce6c8dac.

The successful run used Python 3.13.15, worldloom 0.1.0, pytest 9.1.1, and installed numpy 2.5.3 and rasterio 1.5.2 as repository dev dependencies. Rasterio was not imported or used by the experiment.

