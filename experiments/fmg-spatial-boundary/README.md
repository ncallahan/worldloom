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



## Follow-up — 2026-10-04

This dated follow-up extends the original experiment without overwriting its raw output.

Primary input: examples/Thimaland Full 2026-10-02-14-17.json (783,840 bytes). The follow-up reconstructs all 682 real pack-cell polygon rings from cells.v -> pack.vertices[].p, round-trips all 1,430 pack vertices and all 682 stored cell p coordinates, and checks full-size topology.

The original results/raw-results.json is unchanged. New raw output is results/followup-2026-10-04.json.

Successful measurement run: GitHub Actions run 37185577861, runner commit bac83c1db2276f6c8ff49eb681e52dc395d9e600, Python 3.13.15.

The temporary harness had real failures before the valid run: mixed burg-array handling, two newline-encoding mistakes, an incorrect pack-vertex collection reference, and a missing cell-point measurement binding. These were corrected before accepting the successful run and are not treated as FMG evidence.

Main findings:

- Thimaland is isotropic at 0.76 / -0.76.
- All 682 rings were valid, implicitly closed, non-degenerate and consistently wound.
- Vertex max absolute error: 2.842e-14 R1, 4.263e-14 R2, 2.842e-14 R2-control.
- Vertex max ULP: 6 R1, 13 R2, 15 R2-control.
- R2's simple scale control produced up to 1.421e-14 error; the power-of-two R2-control produced zero simple scale noise.
- The earlier apparent R2 advantage is not supported. R1 is slightly better numerically on this full fixture, but not enough to justify a system-level preference.
- Full topology passed: 3,984 directed adjacency references, 1,992 shared-edge pairs, no missing reverse adjacency, no invalid burg/route/river cell references, and integer -1 sentinels preserved.
- Shared vertices had one transformed coordinate each, with no conflicts.
- Stored area does not equal shoelace polygon area; preserve it separately.
- Stored p differs materially from polygon centroid and vertex mean; preserve it separately.
- Stored h is present on all cells, but this experiment does not establish its semantic/unit meaning.

Optional Part C was skipped deliberately. The committed Viveria and Pithigy full exports are approximately 8.1 MB and 7.4 MB; loading them was unnecessary for the primary question.

The follow-up strengthens the provisional case for explicit, testable representation transforms at an import/adapter boundary, but it does not strengthen the case for R2. No canonical coordinate system, CRS, importer representation, or save/load design is adopted.
