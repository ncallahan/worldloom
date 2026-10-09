---
type: reference
status: reference
summary: Built implementation reference for the scoped Azgaar Fantasy Map Generator snapshot importer.
related: ["[[devwiki/questions/fmg-import-scope]]", "[[devwiki/vision/fmg-import-vault-mvp]]", "[[devwiki/vision/roadmap]]"]
---

# FMG snapshot importer

This page documents the scoped FMG snapshot importer as implemented. It describes the current implementation; it does not make the implementation normative Worldloom architecture.

## Input and provenance

The importer accepts one FMG full-JSON snapshot at a time. The source export itself is not retained. `fmg.source` retains source filename, SHA-256, byte size, selected FMG metadata, and map coordinates; provenance records retain the source filename and hash plus the importer configuration.

The importer has a current limitation when a second FMG map is imported into an already-populated `WorldState`: the import aborts with an entity-ID collision because the provisional entity-ID format has no world/map scope part.

## FMG-to-Worldloom mapping

### Entities

The following FMG `pack` collections become Worldloom entities:

- `states`
- `provinces`
- `burgs`
- `cultures`
- `religions`
- `rivers`
- `routes`
- `markers`

Each entity retains FMG collection, explicit FMG `i`, and source position in its FMG metadata. The current entity ID is derived from:

    derive_entity_id(kind, "source:fmg", "collection:{collection}", "fmg-id:{fmgi}")

This identity-part format is **provisional**. It is an implementation detail of the current importer and does not settle the eventual Worldloom identity/address model.

`provinces` and `burgs` may begin with a bare integer placeholder at position 0; that placeholder is dropped and is not an entity. Invalid records are reported as anomalies and skipped. Duplicate explicit `i` values abort the import before any WorldState writes.

### Fields and lookups

The importer stores the FMG mesh/index structures without enriching pack cells:

- `fmg.pack.cells`: source `pack.cells`, including raw FMG `f` and `biome` values and raw `g`.
- `fmg.pack.vertices`: source `pack.vertices`.
- `fmg.features`: lookup keyed by explicit `pack.features[].i`; the bare integer feature placeholder at position 0 is dropped.
- `fmg.biomes`: lookup keyed by explicit `pack.biomes[].i`.
- `fmg.grid.climate`: reachable grid cells keyed by grid-cell position, retaining only `temp` and `prec`; reachability comes only from usable `pack.cells[].g`.

The current canonical-export tests observe that every `pack.cells[].f` value is present in `fmg.features` and every `pack.cells[].biome` value is present in `fmg.biomes`. These are recorded observations of the tested exports, not importer contracts.

### Dropped keys and data

The entity adapter deliberately drops these FMG keys from entity attributes:

- `states`: `coa`, `military`, `campaigns`
- `provinces`: `coa`
- `burgs`: `coa`, `production`

The FMG feature placeholder is dropped as described above. Entity reference fields are translated into Worldloom `refs` where the importer has an explicit reference specification; unresolved or invalid references are omitted and recorded as anomalies.

## References: resolved versus raw

The entity adapter currently resolves these references:

- states: `neighbors` -> `states`; `provinces` -> `provinces`
- provinces: `state` -> `states`; `center` -> raw mesh reference in `pack.cells`
- burgs: `cell` -> raw mesh reference in `pack.cells`; `state` -> `states`
- rivers: `cells` -> raw mesh references in `pack.cells`
- markers: `cell` -> raw mesh reference in `pack.cells`
- routes: `points[i][2]` -> raw mesh reference in `pack.cells`, recorded as `refs["cells"]` (list); the full `points` value remains raw in attributes

Mesh references remain explicit `{space, index}` values rather than becoming entities. In contrast, `fmg.pack.cells[].f`, `fmg.pack.cells[].biome`, and `fmg.pack.cells[].g` remain raw FMG values; the importer does not rewrite them to lookup keys or duplicate mappings.

A `-1` sentinel in a reference field is recorded as an anomaly and does not become a reference.

## Import report

The importer stores its observation under `fmg.import.report`. The report contains:

- `source`: sanitized source metadata.
- `mesh`: pack-cell and pack-vertex counts.
- `diagnostics`: mesh diagnostics.
- `entities`: `entity_counts`, `dropped_keys`, and `anomalies`.
- `features`: feature lookup retention, dropped-placeholder count, and feature anomalies.
- `biomes`: biome lookup retention and biome anomalies.
- `climate`: retained grid-cell count, usable `g` count, retained `temp`/`prec` counts, and climate anomalies.
- `lookup_observations`: read-only observations about whether pack-cell `f` and `biome` values occur in their lookup keys.

The `entities`, `features`, `biomes`, and `climate` anomaly reports use `counts`, `examples`, and `total`. `counts` is keyed first by anomaly kind and then by source path. `examples` contains a bounded sorted sample (up to 20), and `total` is the total anomaly count for that report. The `diagnostics` block has a different mesh-diagnostic shape: `missing_sections`, `invalid_structure`, `invalid_structure_count`, `sentinels_minus_one`, `out_of_range`, and `out_of_range_examples`.

Anomalies can therefore be found at, for example:

- `fmg.import.report.entities.anomalies`
- `fmg.import.report.features.anomalies`
- `fmg.import.report.biomes.anomalies`
- `fmg.import.report.climate.anomalies`
- `fmg.import.report.diagnostics`, for mesh anomalies and tolerated structural issues

The importer currently records kinds including `invalid-type`, `sentinel`, `out-of-range`, `missing-section`, `missing-field`, `id-position-mismatch`, and `lone-surrogate`, depending on the affected collection or stage.

The mesh `diagnostics` block records its own tolerated mesh issues, including missing sections, invalid structure, `-1` sentinels, and out-of-range mesh references.

## Anomaly severity and surfacing

Anomalies are classified and surfaced by a shared reader on the Worldloom side. The importer continues to write the report shapes described above; unifying those shapes is deferred. The reader understands both the nested `anomalies.counts` shape and the mesh `diagnostics` shape without changing the report.

Anomalies are deliberately tolerant: **they never fail a run**. Invalid or incomplete values continue to be skipped or partially retained according to the importer rules above, with the issue reported for review.

| Severity | Kinds |
| --- | --- |
| `info` | `sentinel`, `placeholder-reference` |
| `warning` | `lone-surrogate`, `invalid-type`, `out-of-range`, `unresolved-reference`, `invalid-structure`, `missing-section`, `missing-field`, `id-position-mismatch` |
| `error` | Reserved; no known anomaly kind maps to this severity today |

Unknown anomaly kinds default to `warning`, so a newly introduced kind is surfaced rather than silently treated as informational. `lone-surrogate` is deliberately a warning because these anomalies are prevalent in real FMG exports. The error tier remains reserved and its count is currently zero.

The existing report is surfaced in four places:

- The CLI read-stage line reports `anomalies=E errors, W warnings, I info`; when no import report exists it reports `anomalies=none`. Unrecognised report blocks are listed as `unrecognised_report_blocks=...`.
- `_worldloom/import.md` shows a severity summary.
- `_worldloom/anomalies.md` is generated whenever the report is a mapping and shows severity, kind, normalised path pattern, and up to five concrete paths for each pattern. A zero-anomaly report says “No anomalies recorded”.
- `index.md` starts with an anomaly banner only when warning or error counts are nonzero. Informational-only reports do not add the banner.

The shared reader is a presentation and interpretation layer; it does not rewrite importer output or change the rule that anomalies never fail a run.

## Lone-surrogate sanitization

At the FMG importer boundary, lone UTF-16 surrogate code points are sanitized in entity attributes, feature and biome lookup records, source metadata, provenance values, and anomaly values. The verbatim `fmg.pack.cells` and `fmg.pack.vertices` fields are not sanitized; they retain the source structures as imported.

Each lone surrogate is replaced with U+FFFD (`\\ufffd`) and records a `lone-surrogate` anomaly where the sanitized value is being processed with anomaly collection. Anomaly values themselves are sanitized without recursively creating another anomaly. Proper surrogate pairs are preserved unchanged.

Sanitized strings can therefore differ from the source text. If sanitization changes two dictionary keys to the same key, the importer aborts with a key-collision error rather than silently choosing one.

The scope decision is recorded in [[devwiki/questions/fmg-import-scope#Decided: lone surrogates in source strings]], with the unresolved core question in [[devwiki/questions/fmg-import-scope#Open: core acceptance of lone surrogates]].
## Abort versus anomaly

The importer distinguishes malformed data that can be skipped from conditions that make the import unsafe to continue.

Anomalies are tolerated and reported for invalid record types, invalid IDs, invalid or sentinel references, out-of-range mesh/grid references, missing optional sections or climate fields, grid ID/position mismatches, and lone-surrogate strings. The affected value or record is skipped or partially retained according to the collection-specific rule.

The import aborts before WorldState writes for duplicate explicit entity or lookup IDs, derived entity-ID collisions, existing entity-ID collisions in the destination world, a non-list FMG collection where a list is required, and provenance-construction failure. The importer also rejects the explicitly deferred `scope` argument rather than silently choosing an identity scope.

## Known limitations

- Two FMG maps cannot currently be imported into one `WorldState` because the provisional entity identity format has no world/map scope.
- The original FMG export is not retained; only source hash and metadata are retained.
- The importer is a one-time snapshot import, not an FMG re-import/update mechanism.
- The identity/address model remains provisional.
- The importer does not yet implement the excluded FMG collections: `goods`, `markets`, `deals`, `journeys`, `measurers`, `military`, `campaigns`, `zones`, `nameBases`, `coats of arms`, and `burg production data`.
- The current climate representation is keyed by grid position and is deliberately limited to grid cells reached from `pack.cells[].g`; it does not establish a final graph-oriented spatial representation.

## Command-line conversion

The provisional CLI conversion path exposes the current format wiring through `worldloom convert`:

    worldloom convert -f fmg -t markdown-vault INPUT -o OUTPUT
    worldloom convert -f fmg -t world-json INPUT -o OUTPUT
    worldloom convert -f world-json -t markdown-vault INPUT -o OUTPUT
    worldloom convert --list-formats

The currently listed formats are:

| Format | Role | Description |
| --- | --- | --- |
| `fmg` | source | Azgaar FMG full JSON snapshot |
| `world-json` | source, target | provisional unversioned Worldloom world save |
| `markdown-vault` | target | Obsidian-compatible Markdown projection |

Every conversion passes through a fresh Worldloom world. A `markdown-vault` target is a projection rather than a lossless equivalent of its source. `world-json` is provisional and unversioned.

With one input, `-o/--output` names the destination itself. With several inputs, it names an output directory and each result uses the input filename stem; Worldloom sanitizes characters outside `[A-Za-z0-9._-]` and collapses replacement runs. Each input is converted independently and is never merged with another input.

The CLI can also convert an FMG snapshot to `world-json`, then use that saved world as the source for a later `world-json` to `markdown-vault` conversion. `--overwrite-edited` applies only to Markdown vault output. `--force` applies only to existing `world-json` output files.

The command reports read and write timings, entity counts, FMG import anomaly totals when present, output byte counts, and peak memory where the host provides it. These measurements are informational and are not written into the world or vault. FMG source metadata reports its version; versions other than the currently tested `1.153.1` receive a notice but are not rejected.

The conversion-format table is provisional CLI wiring. It is not a plugin architecture or a settled adapter registry.

For several inputs, validation is performed before output work begins; an expected failure during conversion stops at the first failing input rather than continuing with later inputs.