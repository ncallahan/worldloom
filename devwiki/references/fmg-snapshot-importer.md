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

The importer deliberately does not accept a second FMG map into an already-populated `WorldState`: the current provisional entity IDs do not include a world/map scope, so importing two maps into one `WorldState` can collide.

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

Mesh references remain explicit `{space, index}` values rather than becoming entities. In contrast, `fmg.pack.cells[].f`, `fmg.pack.cells[].biome`, and `fmg.pack.cells[].g` remain raw FMG values; the importer does not rewrite them to lookup keys or duplicate mappings.

A `-1` sentinel in a reference field is recorded as an anomaly and does not become a reference.

## Import report

The importer stores its observation under `fmg.import.report`. The report contains:

- `source`: sanitized source metadata.
- `mesh`: pack-cell and pack-vertex counts.
- `diagnostics`: mesh diagnostics.
- `entities`: entity retention, dropped-key information, resolved-reference observations, and entity anomalies.
- `features`: feature lookup retention, dropped-placeholder count, and feature anomalies.
- `biomes`: biome lookup retention and biome anomalies.
- `climate`: retained grid-cell count, usable `g` count, retained `temp`/`prec` counts, and climate anomalies.
- `lookup_observations`: read-only observations about whether pack-cell `f` and `biome` values occur in their lookup keys.

Every anomaly report uses `counts`, `examples`, and `total`. `counts` is keyed first by anomaly kind and then by source path. `examples` contains a bounded sorted sample (up to 20), and `total` is the total anomaly count for that report.

Anomalies can therefore be found at, for example:

- `fmg.import.report.entities.anomalies`
- `fmg.import.report.features.anomalies`
- `fmg.import.report.biomes.anomalies`
- `fmg.import.report.climate.anomalies`

The importer currently records kinds including `invalid-type`, `sentinel`, `out-of-range`, `missing-section`, `missing-field`, `id-position-mismatch`, and `lone-surrogate`, depending on the affected collection or stage.

## Abort versus anomaly

The importer distinguishes malformed data that can be skipped from conditions that make the import unsafe to continue.

Anomalies are tolerated and reported for invalid record types, invalid IDs, invalid or sentinel references, out-of-range mesh/grid references, missing optional sections or climate fields, grid ID/position mismatches, and lone-surrogate strings. The affected value or record is skipped or partially retained according to the collection-specific rule.

The import aborts before WorldState writes for duplicate explicit entity or lookup IDs, derived entity-ID collisions, existing entity-ID collisions in the destination world, a non-list FMG collection where a list is required, and provenance-construction failure. The importer also rejects the explicitly deferred `scope` argument rather than silently choosing an identity scope.

## Known limitations

- Two FMG maps cannot currently be imported into one `WorldState` because the provisional entity identity format has no world/map scope.
- The original FMG export is not retained; only source hash and metadata are retained.
- The importer is a one-time snapshot import, not an FMG re-import/update mechanism.
- The identity/address model remains provisional.
- The importer does not yet implement the deferred FMG collections and fields recorded in the import-scope question.
- The current climate representation is keyed by grid position and is deliberately limited to grid cells reached from `pack.cells[].g`; it does not establish a final graph-oriented spatial representation.