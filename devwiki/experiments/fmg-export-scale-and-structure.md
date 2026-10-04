---
type: experiment
status: experiment
summary: "Measurement-only FMG full-JSON scale, structure, schema, and WorldState compatibility experiment."
related: ["[[devwiki/process/experiments]]", "[[devwiki/references/fmg-full-json-observed]]", "[[devwiki/questions/fmg-import-scope]]", "[[devwiki/current]]"]
---

## FMG export scale and structure experiment

### Question

What data shape, reference/index behaviour, and resource scaling does a real Azgaar Fantasy Map Generator (FMG) full-JSON export present to Worldloom, and what structures must an importer preserve?

This is a measurement-only experiment. It does not change `src/worldloom`, implement an importer, or select a final internal FMG representation.

### Scope and inputs

The experiment uses three canonical FMG full-JSON exports:

- Thimaland: 1,000 requested graph points, used as the small control.
- Viveria: 10,000 requested graph points.
- Pithigy: 10,000 requested graph points.

The 10,000-point exports use the FMG-recommended/default graph-point setting, but these are still relatively small worlds with comparatively low simulation settings. They should not be treated as upper bounds or as maximally populated examples of a 10,000-point FMG world. A richer authored FMG world may contain substantially more content at the same graph-point count.

Canonical FMG exports remain committed in `examples/` under the fixture policy recorded in [[devwiki/questions/fmg-import-scope]]. Raw numerical results belong under `experiments/fmg_scale/results/`; interpretation belongs here.

### Hypotheses and falsification criteria

These hypotheses are stated before the final three-file measurement run. Some exploratory measurements of the two currently available files occurred before this documentation update; those preliminary observations are retained as provisional and are not presented as the completed experiment.

**H1 — Size and structure (inconclusive from three points).** Export size is approximately 0.7 KB per requested graph point beyond a roughly 110 KB constant, and the grid section is approximately 40% of the file. Falsify if the three-file measurements materially contradict that scale or if the grid share is not of that order. Measure serialised bytes for `info`, `settings`, `pack.*`, `grid.*`, and `nameBases`, then fit/export the requested-point relationship.

**H2 — Index/ID.** Collections differ in whether array position is an identifier. Report dict-vs-nondict entries, `id == index` behaviour, placeholder entries and positions, and removed/null entries. Specifically check the expected placeholder at index 0 for burgs/features/provinces, the offset behaviour of rivers/markets, and populated states/provinces/diplomacy/military. Falsify any universal indexed-collection assumption.

**H3 — Reference integrity.** Count dangling/out-of-range references for cell→burg/state/province/culture/religion, burg→cell/state, state→neighbors, river cells, route points, marker/zone cells, `cells.c`, `cells.v`, and `vertices.c`. Determine which index space `vertices.c` uses rather than assuming it references pack cells.

**H4 — Pack/grid mapping.** Determine whether `pack.cells[].g` is injective, how it relates pack and grid cell counts, which attributes exist only on grid (including candidates such as `prec`), and what fraction of grid cells have no pack cell. Falsify any assumption that pack cells and grid cells have a one-to-one correspondence.

**H5 — Shape variance.** Census key presence and value types per collection, including optional keys such as cell routes, and identify fields whose value type changes between entries. Falsify a homogeneous-schema assumption where the exports demonstrate otherwise.

**H6 — Structure variation within one FMG version.** Compare `info.version` and the presence of goods, markets, deals, journeys, and measurers across all three files. Measure deals and markets relative to burg count; Viveria has 14.41 deals per burg. Falsify any assumption that these structures can be ignored because they are absent from the small control.

**H7 — Coordinates.** Confirm the `mapCoordinates` longitude/latitude mapping against `info.width` and `info.height` in all three files, report coordinate ranges and units, and report the pack-cell fraction of the requested graph.

**H8 — Existing-code scaling.** With the real files loaded through `json.load`, measure load time/peak memory; `WorldState.set_field` of pack cells, vertices, and grid cells using fingerprint plus deepcopy; snapshot/restore; and a plain `json.dumps` round trip. The working prediction is linear scaling, below about 10 s and 2 GB for the largest tested file. A superlinear step or resource ceiling falsifies that prediction.

**H9 — Determinism.** Load each file twice and compare the resulting `WorldState.fingerprint` values section-by-section; record each file's SHA-256. Falsify if repeated loading produces different fingerprints for the same canonical input.

### Repository fixture hygiene

This experiment also compares five ways of handling FMG fixtures:

1. **Commit only Thimaland.** Small and convenient, but does not exercise the structures found only in richer worlds.
2. **Seeded regeneration.** Avoids storing large exports, but reproducibility is conditional on retaining the same FMG version and settings; generator changes can alter output.
3. **Derived trimmed fixture.** Small and targeted, but risks exercising a representation that differs from a real full export and conflicts with the full-JSON-only input boundary if treated as a production fixture.
4. **Git LFS.** Keeps the canonical full export in the repository while moving large binary/object storage out of ordinary Git history. It adds an LFS dependency and does not make large-file review equivalent to ordinary text review.
5. **External download with a pytest marker.** Keeps the repository small and permits canonical full exports to remain outside Git, but requires a stable external source and an explicit test-data acquisition step.

GitHub currently warns when regular Git files exceed 50 MiB and blocks files larger than 100 MiB; Git LFS is the mechanism GitHub documents for files beyond the regular repository limit. Release assets are another option for distributing large files. The final recommendation should use the measured export sizes and the project's reproducibility requirements rather than assuming that every FMG export needs LFS. 


### Results

The completed measurements establish the following for the three canonical exports:

| Export | Requested points | File bytes | Pack cells | Grid cells | Grid share | Pack/requested |
|---|---:|---:|---:|---:|---:|---:|
| Thimaland | 1,000 | 783,840 | 682 | 1,008 | 41.1% | 68.2% |
| Viveria | 10,000 | 8,055,496 | 4,855 | 9,975 | 42.2% | 48.6% |
| Pithigy | 10,000 | 7,423,584 | 4,474 | 10,032 | 46.3% | 44.7% |

All three exports report FMG version 1.153.1. The two 10,000-point files differ by 631,912 bytes (7.84% of Viveria), so graph-point count alone does not determine export size.

**H1 — Inconclusive from the three-point fit.** The three points give a least-squares slope of 772.9 bytes/requested point and an intercept of 11.0 KB, rather than the proposed approximately 700 bytes/point beyond approximately 110 KB. The grid share is in the expected broad range but rises from 41.1% to 46.3%. The two same-point-count exports also show substantial content-dependent variance. The result does not justify a universal bytes-per-point capacity estimate.

**H2 — Confirmed.** cells and vertices are position-indexed in all three measured files (i == array index). features, burgs, and provinces use a bare integer placeholder at index 0 in the examples. River IDs are offset/sparse rather than array-position identifiers; markets likewise use explicit IDs rather than i == index. The larger files exercise populated states, provinces, diplomacy, campaigns, and military structures that the Thimaland control does not. Pithigy has 4 states, 117 provinces, 506 burgs, 3 states with campaigns, and 3 with military records.

**H3 — Confirmed with corrected vertex index spaces and sentinel distinction.** The measured references are in range for the requested cell/state/province/culture/religion/burg/state/neighbour/province/marker/zone/route relationships. `pack.cells[].v` indexes `pack.vertices`. `pack.vertices[].v` is valid in `grid.vertices` space (with `-1` sentinels) rather than `pack.vertices` space. `pack.vertices[].c` is valid in `grid.cells` space; values exceed pack-cell count in all three files. Pithigy has three `-1` river-cell values. These sentinels are recorded separately from ordinary OOB references.

**H4 — Confirmed non-bijective mapping.** pack.cells[].g is not injective: duplicate grid indices occur in all three files. Maximum multiplicity is 5 in Thimaland and Viveria and 4 in Pithigy. Grid cells without a pack-cell mapping are 485/1,008 (48.1%), 5,980/9,975 (60.0%), and 6,634/10,032 (66.1%) respectively. Pithigy's grid cells also carry temp and prec, while pack cells do not use those grid-only fields. An importer must preserve the two index spaces rather than collapsing them.

**H5 — Confirmed heterogeneous shape/type.** Optional keys and mixed scalar types occur in the larger exports. Pithigy has routes on 1,995/4,474 pack cells and demonstrates integer/float variation in fields including population, burg coordinates, treasury, product, state taxes, river measurements, and deal values. Feature records also have optional flux, temp, evaporation, inlets, and outlet fields. A strict homogeneous-record schema would reject observed FMG data.

**H6 — Confirmed structure variation within one FMG version.** All three files are version 1.153.1 and contain 71 goods. Deals and markets are present at materially different scales: Thimaland 130/1, Viveria 10,277/15, and Pithigy 7,627/16. Deals per burg are approximately 14.44, 14.41, and 15.07 respectively, while markets per burg are approximately 0.111, 0.0210, and 0.0316. Journeys and measurers are also present in the three canonical exports. The small control therefore does not exercise the full economic/transport structure.

**H7 — Confirmed for the native coordinate model.** The exports provide FMG-native map coordinates through mapCoordinates, alongside the declared info.width/height; the pack-cell p values are in the native map x/y space. Pithigy's declared map is 400×230 with p.x in [0.29, 320.81] and p.y in [17.55, 211.53]. The working coordinate mapping remains the linear map-space-to-lon/lat transformation implied by the declared west/east/north/south bounds. The measurements support retaining native FMG coordinates at import rather than inventing a new coordinate system in this experiment.

**H8 — Completed on all three canonical files.** Repeated real-file measurements recorded load time/peak tracemalloc, `set_field` for pack cells, pack vertices, pack burgs, and grid cells, snapshot, and restore. Load times were 0.076/0.073 s for Thimaland, 0.733/0.744 s for Pithigy, and 0.861/0.829 s for Viveria. Snapshot/restore were 0.080/0.082 s, 0.775/0.825 s, and 0.845/1.158 s respectively. The largest measured set_field was Viveria pack burgs at 0.387 s; the largest snapshot/restore peak tracemalloc was about 31.2 MB. All three are well below the original 10 s / 2 GB working prediction. Raw measurements are committed under experiments/fmg_scale/results/fmg_scale_h8_h9_2026-10-03.json.

**H9 — Confirmed for the tested WorldState sections.** Each canonical file was loaded twice and `WorldState.fingerprint` matched for `pack.cells`, `pack.vertices`, `pack.burgs`, and `grid.cells`. The same four fingerprints matched between load 1 and load 2 for each file. File SHA-256 values and per-section fingerprints are retained in the raw result. The current fingerprint preserves int/float distinctions; whether that should remain the long-term normalisation rule is an owner decision, not an experiment conclusion.

No tested section raised `TypeError` during fingerprinting. The current normalisation distinguishes integer and float scalar types; the final measurement counted 79,564 numeric scalar values in Thimaland (67,824 int / 11,740 float), 781,196 in Viveria (651,241 / 129,955), and 736,592 in Pithigy (617,798 / 118,794).

A bounded serialization check found zero integral-valued floats in all three canonical exports: Thimaland 11,740 floats / 0 integral-valued, Viveria 129,955 / 0, and Pithigy 118,794 / 0. This is consistent with JavaScript JSON.stringify serializing integral numeric values without a decimal point, but it does not prove the originating serializer.


### Observed schema digest and slice fixtures

The regenerable schema digest is devwiki/references/fmg-full-json-observed.md. It records the observed top-level and pack collection shapes across all three canonical exports, including ID/index rules, placeholders, key/type presence, reference index spaces, and bounded examples. It is a reference artifact, not normative importer architecture.

The digest corrected an earlier assumption: pack.vertices[].v is grid-vertex adjacency (with -1 sentinels), while pack.vertices[].c is grid-cell adjacency. grid.vertices[].c was deliberately left semantically open because the simple grid-cell bound does not hold in these exports.

The slice generator is experiments/fmg_scale/make_slice.py. It remaps pack cells/vertices, grid references, burgs, provinces, and route/river/marker references; preserves burg/province placeholder-at-zero and one-based IDs; retains a state with neighbors and diplomacy; and writes the remapping to a `.remap.json` sidecar. High-volume or owner-excluded structures are represented as empty collections rather than copied wholesale. The committed Viveria and Pithigy hop-3 slices contain 39 and 52 pack cells and are 77,912 B and 99,002 B respectively when pretty-printed. Both are below 100 KB, deterministic across repeated generation, and pass the bounded reference-integrity checks; the Pithigy slice retains a reachable river -1 sentinel.

### Owner decisions

Decided and genuinely open importer-scope questions are consolidated separately in [[devwiki/questions/fmg-import-scope]]. This experiment records the evidence and does not promote those owner decisions into architecture.

### Fixture-hygiene interpretation

The measured regular-Git sizes are 0.75 MiB (Thimaland), 7.68 MiB (Viveria), and 7.08 MiB (Pithigy), all well below GitHub's 50 MiB warning and 100 MiB hard block for ordinary Git files. GitHub recommends keeping ordinary repository objects small, but these particular fixtures do not require Git LFS merely to remain within the file-size limit. GitHub also documents that generated files can be marked with linguist-generated in .gitattributes so they are hidden by default in diffs; that attribute is useful if generated FMG exports are intentionally committed, but it is not required for correctness and does not solve the repository-history cost of repeated large-file changes.

For this project, the experiment leaves the fixture choice as an owner decision. The practical options remain: commit only Thimaland; regenerate seeded exports under a pinned FMG version/settings; commit a derived trimmed fixture for targeted tests; use Git LFS; or keep canonical exports external and acquire them under an explicit test-data step. The measured 7–8 MiB size of the 10,000-point examples makes ordinary Git technically possible, but the full-JSON-only boundary and the risk of frequent large diffs favour treating the larger exports as experiment inputs rather than routine test fixtures.

### Decision-relevant structures

The larger exports exercise structures absent or effectively empty in Thimaland: multiple states; populated provinces; diplomacy; campaigns; military unit records; hundreds of burgs; substantial deals and markets; route data; and, in the inspected exports, journeys and measurers. They also demonstrate that vertices.c and pack.cells[].g belong to the grid index space rather than providing a simple pack-cell mapping.

Nothing measured here contradicts the current owner decisions that the MVP input is the FMG full JSON export, that import is a one-time snapshot, and that the interim coordinate space may remain FMG map space. The experiment reinforces that an importer cannot safely assume a pack-only representation: the full export contains multiple interacting collections and both pack/grid index spaces. Which of those structures the first importer preserves is an explicit owner decision.

### Decision boundary

The experiment records observed FMG behaviour and resource measurements only. Importer representation and scope decisions remain in [[devwiki/questions/fmg-import-scope]].
