---
type: experiment
status: experiment
summary: Provisional results for explicit FMG spatial representations at the import boundary.
related: ["[[architecture/adapters]]", "[[architecture/provenance]]", "[[architecture/canonical-state-vs-observation]]"]
---

# FMG spatial representation at the import boundary

## Status and scope

This is a provisional experiment record. It is evidence, not architecture. It does not choose a canonical coordinate system, define a CRS, define a world-file format, or add an importer.

The original experiment phase used the retained Viveria and Pithigy slice fixtures and the repository's existing FMG schema evidence. The 2026-10-04 follow-up additionally used the committed Thimaland FMG export to test real pack-cell polygon geometry and the full mesh. It did not use the historical CAMPAIGN DIRECTION document.

The experiment implementation remains in experiments/fmg-spatial-boundary/ because the repository permits that layout for substantial experiments. This record lives under devwiki/experiments/ as the experiment's documentation record.

## Question

Can retained FMG spatial data cross the explicit pipeline

FMG -> Worldloom spatial representation -> external/geographic representation -> Worldloom -> FMG

without ambiguity or meaningful loss, while leaving the canonical coordinate choice open?

Two and only two candidate Worldloom representations were tested.

### R1 — FMG map-space retained

FMG x/y is retained verbatim. The Worldloom-to-external transform is the observed FMG mapCoordinates affine mapping.

### R2 — Worldloom-local normalised space

The local representation is centred on the FMG map midpoint, normalised independently in x and y to approximately [-0.5, 0.5], with north-up orientation:

x_local = x / width - 0.5

y_local = 0.5 - y / height

This is an experiment-local candidate only.

## Source-space evidence

The existing schema digest establishes:

- FMG pack coordinates are map-space x/y.
- y increases north-to-south.
- longitude and latitude are affine functions of x/y.
- the observed coordinate residuals are approximately 1e-14 or smaller.
- -1 is a sentinel in the observed river-cell and pack/grid vertex adjacency structures and is not an entity or coordinate.

The slice fixtures contain the expected pack/grid topology and diagnostic original-to-slice remaps.

A significant fixture limitation emerged on direct inspection: the slices do not retain pack-vertex coordinates. pack.vertices has only c, i and v; pack.cells has no p or area. Burg records in these slices also omit x/y. grid.vertices does retain p, so grid-vertex points were used for point-distance, centroid, orientation and affine area-scaling measurements. Pack-cell polygon area and pack-vertex coordinate measurements were therefore not fabricated.

## Reference spaces

The experiment treated the tested references as:

| Reference | Space |
|---|---|
| pack.cells[].c | pack-cell, slice-local |
| pack.cells[].v | pack-vertex, slice-local |
| pack.cells[].g | grid-cell, slice-local |
| pack.vertices[].v | grid-vertex, slice-local |
| pack.vertices[].c | grid-cell, slice-local |
| pack.routes[].points[][2] | pack-cell, slice-local |
| pack.burgs[].cell | pack-cell, slice-local |
| -1 | sentinel, never an index |
| .remap.json mappings | original FMG ID to slice-local ID; diagnostic provenance only |

## Raw execution

Successful experiment run: GitHub Actions run 37181200021.

Successful implementation commit: dd2eaf4b20ffd36cba481510465c912ad6031d25.

Environment recorded by the run:

- Python 3.13.15
- worldloom 0.1.0
- pytest 9.1.1
- numpy 2.5.3 was installed as a repository development dependency and was used only for the explicit fingerprint-behaviour check; no numpy object entered fingerprinted experiment data.
- rasterio 1.5.2 was installed by repository development dependencies but was not imported or used.

There was no random seed.

Raw output is recorded at experiments/fmg-spatial-boundary/results/raw-results.json. The raw artifact from run 37181200021 had SHA-256 d1e00dca8a6512f61cd458bf7d403e0be11d7713fa33e148d2a47d72c934c7a6.

The temporary CI runner exposed four implementation defects before the successful run: the initial scaffold commit was not on the branch used by the runner, followed by a Python syntax error, an incorrect class-method use of WorldState.restore, an incorrect provenance lookup key, and a summary-printing key error. These were corrected; the successful run then completed. None of those failures was a negative result from the FMG data itself.

## Raw measurements

### Topology

Both slices preserved, exactly:

- pack-cell count
- pack-vertex count
- grid-cell count
- grid-vertex count
- cells.c adjacency
- cells.v membership
- cells.g pack/grid association
- pack-vertex v/c references
- burg cell/state references
- route point cell references
- the -1 sentinel as integer -1

The remap sidecars contained the expected local mappings: Viveria 39 cells, 117 pack vertices, 33 grid cells and 260 grid vertices; Pithigy 52, 148, 47 and 335 respectively.

### Coordinate round trips

The largest FMG -> Worldloom -> FMG coordinate errors over the retained point sets were:

| Slice | R1 | R2 | Documented residual maximum | Ratio R1/R2 |
|---|---:|---:|---:|---:|
| Viveria | 5.684341886080802e-14 | 2.842170943040401e-14 | 7.105427357601002e-15 | 8x / 4x |
| Pithigy | 8.526512829121202e-14 | 7.105427357601002e-14 | 7.105427357601002e-15 | 12x / 10x |

Thus neither representation was bit-exact through the complete FMG -> WL -> external -> WL -> FMG path for the grid-vertex data.

R1 is exact for the Worldloom identity step, but the geographic round trip introduces floating-point error. R2 introduces a nontrivial normalisation/inversion and was still bounded to approximately 1e-14 in the tested fixtures.

The WL -> external -> WL step alone was much tighter for R2: 1.11e-16 maximum in Viveria and 3.33e-16 in Pithigy for grid vertices. R1 inherited the larger geographic round-trip error.

No transformed output contained NaN or infinity, and the experiment's exact-type walk found no non-built-in numeric objects in fingerprinted transformed data.

### Orientation and anisotropy

Viveria's observed geographic slopes are +0.2 and -0.2. The sample grid-vertex angle changed by only about 4.05e-13 degrees. The measured triangle area ratio was 0.04000000000000043 against the affine determinant magnitude 0.04000000000000001.

Pithigy's slopes differ: +0.1175 and -0.11739130434782608. The sample angle changed by about -0.002151686 degrees. The measured triangle area ratio was 0.01379347826086996 against determinant magnitude 0.013793478260869563. Thus the determinant area-scaling rule held to about 4e-16 absolute difference, while angle preservation did not.

These are coordinate-space area measurements only, not physical lon/lat areas.

### SpatialGrid

SpatialGrid could be instantiated with shape=(height,width), crs=None, and the documented affine transform.

For Pithigy its computed bounds matched the documented geographic bounds exactly. For Viveria the computed south bound was 1.8000000000000007 rather than 1.8, so exact tuple equality failed by approximately 7e-16.

SpatialGrid therefore expresses the regular affine bounding-box relationship, but it does not represent the irregular pack/grid polygons, has no continuous point inverse or point-to-cell lookup, and its cell_center operation has the cell-index +0.5 semantics that must not be applied to continuous FMG coordinates.

### Fingerprinting

The executed assertions found:

- tuple and list fingerprint equal: yes;
- int and float fingerprint equal: no;
- bool and int fingerprint equal: no;
- -0.0 and 0.0 fingerprint equal: no;
- dict insertion order: ignored;
- NaN: fingerprinted successfully;
- numpy.float64: accepted by fingerprinting even though its exact type was not Python float under numpy 2.5.3;
- numpy.int64 and numpy.bool_: rejected with TypeError.

This confirms that fingerprint equality is not a sufficient fidelity test because tuple/list structure is invisible to the fingerprint. The experiment therefore used both fingerprint equality and a recursive type-strict comparison.

### Transform reconstruction and provenance

The transform description was converted to JSON and rebuilt from that JSON alone. JSON represented matrix/offset/etc. as lists; the experiment-local constructor restored the transform's tuple representation.

The rebuilt transform had identical point results under both strict comparison and fingerprint comparison. The inverse also reconstructed correctly.

A scratch WorldState field stored the serialised transform description in Provenance.configuration. Snapshot/restore preserved the configuration and provenance fingerprint, and the inverse could be rebuilt from the restored Provenance alone. No metadata was missing for this reconstruction.

## Interpretation

The evidence does not support a claim of mathematically lossless floating-point round-tripping through the full geographic boundary. It does support a stronger practical observation: the tested coordinate error remained extremely small, topology remained exact, the transforms were deterministic and reconstructible, and no semantic/topological attachment was lost.

R2 reduced the FMG round-trip error in both fixtures, but it did not eliminate floating-point error. R1 has the attractive property that the Worldloom representation is the FMG source representation verbatim, while R2 demonstrates that a Worldloom-local representation can be explicit and reversible without embedding its choice in the topology.

The evidence therefore provisionally favours the boundary pattern represented by A3 — multiple explicit representations with provenance-bearing transforms — over treating one coordinate representation as inherently authoritative. This is a non-binding experiment recommendation, not an architectural decision.

The adapter boundary is the least surprising place for such transforms in this experiment because the transformations are properties of the exchange between spaces rather than of the topology itself. Again, this is a provisional recommendation only.

Minimum transform metadata demonstrated as useful was more than scale/origin/axis alone: source and target space, affine matrix/offset, axis order, y direction, origin, scale, bounds, geographic interpretation, invertibility, and provenance/configuration sufficient to reconstruct the transform. A CRS is deliberately not supplied.

## Decision evidence

| Question | Evidence | Tentative conclusion |
|---|---|---|
| Lossless boundary crossing: R1 vs R2 | Neither was bit-exact for grid vertices. R1 max errors: 5.68e-14 and 8.53e-14. R2: 2.84e-14 and 7.11e-14. | No strict lossless claim. Both are practically reversible at very small bounded error in these fixtures; R2 performed better on the measured FMG round trip. |
| Topology survival | All tested topology checks and -1 sentinel checks passed exactly for both slices. | Explicit coordinate transforms can leave topology intact when topology is kept separate from coordinates. |
| Sufficiency of an explicit transform object | Affine transforms, inversion, JSON reconstruction and provenance reconstruction all passed. | An explicit transform object is sufficient for this tested affine boundary. |
| Metadata needed beyond scale/origin/axis | Reconstruction used source/target spaces, affine coefficients, bounds, y direction, geographic interpretation, invertibility and provenance configuration. | Transform metadata should describe semantics and invertibility, not just numeric scale/origin. |
| Can SpatialGrid carry this? | It expressed the regular affine bounds, but not irregular geometry or continuous point inversion; Viveria also showed a tiny bounds mismatch. | SpatialGrid is useful for regular affine grid semantics, but is not sufficient as the general FMG spatial representation tested here. |
| Is fingerprint equality alone adequate? | tuple/list fingerprints matched while strict equality failed; NaN is accepted; numpy.float64 is accepted. | No. Fingerprint plus type-strict comparison is required for this experiment's fidelity checks. |
| Spatial operations without FMG-specific assumptions | Plain affine point arithmetic, distances, centroids, orientation and determinant-based area scaling worked on retained coordinate-bearing points. | Basic continuous-point operations can be representation-neutral; topology and irregular mesh operations require explicit spatial semantics. |
| Reason to fix a canonical system now | R1 and R2 both crossed the tested boundary with tiny bounded error; fixtures lack pack-cell geometry; Pithigy is anisotropic. | No evidence-based reason to choose a canonical coordinate system yet. |

## Unresolved

- Whether FMG map-space should eventually be retained as canonical, converted to another local space, or represented through multiple explicit views.
- Whether a general Worldloom spatial representation should support irregular meshes as first-class data.
- How full pack-cell and pack-vertex geometry should be handled at the real importer boundary; the current slices cannot answer this.
- How to treat anisotropic geographic affine mappings when preserving angles is important.
- Whether exact floating-point round trips are a requirement or whether bounded numerical error is sufficient for each spatial quantity.
- CRS/projection semantics.
- Canonical coordinate-system and world-file decisions.
- Whether Address should participate in spatial identity; this experiment did not use it for continuous coordinates.


## Follow-up — 2026-10-04

The follow-up used only examples/Thimaland Full 2026-10-02-14-17.json (783,840 bytes), not the larger 8 MB exports, for the primary measurement.

All 682 pack cells and 1,430 pack vertices were tested. The export contains cell p, area and h for every pack cell, and p for every pack vertex. pack.cells[].v indexes pack.vertices; every ring was valid, implicitly closed, non-degenerate and counter-clockwise.

The complete FMG -> Worldloom representation -> observed geographic affine space -> Worldloom -> FMG pipeline was tested for R1, the original R2, and R2-control (R2 with 1/256 power-of-two scale and 0.5 binary-exact offset). R2-control is a controlled R2 variant, not a third candidate.

Successful measurement run: GitHub Actions run 37185577861, runner commit bac83c1db2276f6c8ff49eb681e52dc395d9e600, Python 3.13.15. Raw output: experiments/fmg-spatial-boundary/results/followup-2026-10-04.json. The original raw result was not overwritten.

### Follow-up results

| Representation | Vertex mean abs | Vertex P99 abs | Vertex max abs | Vertex max relative | Vertex max ULP |
|---|---:|---:|---:|---:|---:|
| R1 | 2.7341e-15 | 2.8422e-14 | 2.8422e-14 | 8.6320e-16 | 6 |
| R2 | 3.3336e-15 | 2.8422e-14 | 4.2633e-14 | 2.0262e-15 | 13 |
| R2-control | 3.5395e-15 | 2.8422e-14 | 2.8422e-14 | 2.5506e-15 | 15 |

None was bit-exact. Stored cell-p round-trip maxima were 2.8422e-14, 4.2633e-14 and 2.8422e-14 for R1, R2 and R2-control respectively; maximum ULPs were 3, 5 and 5.

The naive x -> x*k -> x/k control had zero error for R1 and R2-control. R2's 1/240 and 1/135 scales alone produced up to 1.4211e-14 absolute noise and 1 ULP. The earlier apparent R2 advantage therefore does not survive the control.

All 682 polygon rings remained non-degenerate. The computed shoelace area does not equal stored pack.cells.area: computed/stored ratios had mean 1.02180, median 1.01868, P99 1.07189 and maximum 1.11839. Stored pack.cells.p also differs materially from both polygon centroid and vertex mean. Stored h is present on all cells, but its semantic/unit meaning was not established by this experiment.

Full topology passed: 3,984 directed adjacency references with no missing reverse, 1,992 shared-edge pairs with exactly two common vertices, no invalid burg/route/river cell references, and integer -1 sentinels preserved. 1,416 unique pack vertices encountered through cell rings had zero coordinate conflicts.

### Revised Question | Evidence | Tentative conclusion

| Question | Evidence | Tentative conclusion |
|---|---|---|
| Does the transform boundary hold on real cell polygons? | 682/682 real rings survived reconstruction and affine area/centroid checks; coordinate round-trip errors remained around 1e-14. | Yes as a practical numerical boundary for this fixture, but not bit-exactly lossless. |
| Does topology survive on a full-size mesh? | All 3,984 directed adjacency references were symmetric; all 1,992 shared edges had two common vertices; burg/route/river references were valid; -1 remained an integer sentinel. | Yes for the tested full Thimaland mesh. |
| Is R1 or R2 preferred? | R1 max vertex error 2.842e-14; R2 4.263e-14; R2-control 2.842e-14. | No robust system-level preference. The earlier R2 advantage is not supported; R1 is slightly better numerically on this fixture, but not by evidence warranting canonical authority. |
| What does stored area imply? | Present on all cells, but not equal to shoelace polygon area. | Preserve stored area as a distinct FMG field unless its semantics are separately established. |
| What does stored p imply? | Present on all cells and materially different from polygon centroid and vertex mean. | Preserve p separately from derived polygon geometry. |
| What does stored h imply? | Present on all 682 cells; not interpreted by this test. | Preserve as an independent FMG field; defer semantic/unit interpretation. |
| What changes earlier conclusions? | Real pack-cell geometry now tested successfully; R2's earlier numerical advantage disappears under full-mesh and scale-control evidence. | Stronger evidence for explicit/testable transforms; weaker evidence for R2 specifically. No canonical coordinate decision follows. |

### Provisional status of the follow-up findings

The follow-up findings are **retained as provisional for this experiment, with rationale**. They are evidence from the tested Thimaland fixture and measurement harness, not settled Worldloom architecture or implementation requirements. In particular:

- The successful full-mesh result establishes evidence for this fixture only; it does not establish that every FMG export, mesh size, or spatial representation will behave identically.
- The R2-control result removes the earlier experimental basis for preferring R2 on numerical round-trip error. R1 was slightly better on this fixture, but that difference is not evidence for making R1 canonical.
- The experiment demonstrates that explicit, reconstructible transforms are workable at this boundary. It does not establish a canonical coordinate system, CRS, world-file format, or first-class irregular-mesh representation.
- Stored `pack.cells.area`, `pack.cells.p`, and `pack.cells.h` are deliberately treated as source observations whose semantics remain unresolved. Their preservation is a provisional experiment finding, not a finalized schema decision.
- The harness failures listed below are retained as experiment execution history and are not treated as evidence against the FMG data or either representation.
- Optional Part C remains an explicitly recorded omission because the larger Viveria and Pithigy full exports were not included in this follow-up. No conclusion about those full geometries is drawn from their absence.

The appropriate next step is therefore to preserve these findings as evidence while leaving the unresolved architectural questions open. Any later decision to adopt a canonical spatial representation, irregular-mesh model, field semantics, or numerical-error requirement must be made separately from this experiment record.

### Failures and surprises

The temporary runner had real implementation failures before the accepted run: mixed burg-array handling, two newline-encoding mistakes, an incorrect pack-vertex collection reference, and a missing cell-point measurement binding. These were harness failures, not FMG-data failures, and were corrected before the successful run.

A source-data surprise was that pack.burgs is a mixed array: index 0 is integer placeholder 0 while indices 1–9 are burg objects carrying x/y and cell references. The follow-up handles this explicitly.

Optional Part C was skipped deliberately because the committed Viveria and Pithigy full exports are approximately 8.1 MB and 7.4 MB. It was not silently omitted.

### Unresolved

- Canonical FMG versus local versus multiple spatial views.
- A first-class representation for irregular meshes.
- Semantics/units of stored pack.cells.area.
- Semantics/units of stored pack.cells.h.
- Why stored pack.cells.p differs from polygon centroid and vertex mean.
- Anisotropic geographic transforms when angle preservation matters.
- Exact versus bounded floating-point error requirements.
- CRS/projection semantics.
- Canonical coordinate and world-file choices.
- Address participation in spatial identity.
- Whether full Viveria/Pithigy geometry materially changes the result.
