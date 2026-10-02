# FMG Vault MVP

## Status

**Selected development focus.** This document records the project-owner decisions for the first useful Worldloom MVP. It is a design/roadmap document, not a replacement for the normative architecture or specification.

The MVP is deliberately a risk-reducing demonstration rather than a miniature of the eventual Worldloom system. Its purpose is to make Worldloom genuinely useful for campaign planning while exercising progressive resolution, provenance, and address-derived identity against a real external world representation.

## MVP purpose

The first MVP target is:

> Import an Azgaar Fantasy Map Generator (FMG) full JSON export, represent it as Worldloom canonical state, add one level of stable on-demand detail, and render a read-only Obsidian-compatible Markdown vault plus a raster export.

The intended output is useful campaign-planning material. The MVP is **not** expected to demonstrate the eventual aims of Worldloom.

## Scope

### In scope

- FMG **full JSON export** as the only supported FMG input.
- One-time snapshot import.
- Adoption of imported FMG values as canonical state.
- Source-file hash and FMG version in provenance.
- Explicit coordinate transformations:
  `source FMG map space -> Worldloom internal space -> target/export space`.
- An explicit identity transform for the current provisional internal-space choice.
- A non-grid spatial representation experiment using a real FMG fixture.
- Versioned JSON world save/load for the MVP.
- Read-only Obsidian-compatible Markdown vault generation.
- One stable level of on-demand detail below FMG resolution, such as burg districts, notable people, factions, and rumours.
- Provenance explaining why an on-demand fact exists.
- Configurable raster export with a sensible default resolution and scale factor.
- Existing GeoTIFF export remains supported during this MVP.
- Fixture integrity checking in CI.

### Explicitly out of scope

- FMG GeoJSON import.
- FMG `.map`, minimal, pack, or grid JSON imports as supported input formats.
- Continuous synchronisation with later FMG edits or re-exports.
- A Markdown edit/mutation workflow.
- Runtime producer guards, `REFINES`, or overlay storage from the producer-ownership work.
- Choosing the final canonical internal coordinate system.
- Choosing the final uncertainty/fuzziness semantics.
- Choosing whether JSON or SQLite is the eventual internal persistence mechanism.
- Making GeoJSON the current GIS export target.
- Any claim that this MVP is the eventual complete progressive world-generation architecture.

FMG GeoJSON may later be useful as a proof of concept for reading data back from GIS tools, but it is not part of this MVP.

## Owner decisions

### Input and import semantics

Only FMG full JSON exports are supported for the MVP. Import is a one-time snapshot operation. Later changes to an FMG source file are not reconciled with the imported world.

The imported values are adopted as canonical by the import. They are nevertheless considered **fuzzy** for future modelling purposes; the representation and behaviour of that fuzziness are deferred.

The imported source file is pinned by provenance, including its content hash and FMG version.

### Coordinates

The intended pipeline is:

```
FMG source map space
        |
        v
source -> internal transform
        |
        v
Worldloom internal coordinate space
        |
        v
internal -> target transform
        |
        v
export coordinate space
```

Both transformations are intended to be explicit, replaceable objects. Latitude/longitude is an export projection, not a decision about the canonical internal coordinate system.

The internal coordinate system remains **open**. For the MVP, it is provisionally the FMG map space reached through an explicit identity source transform.

### Raster output

Raster export uses a sensible default resolution and a configurable scale factor.

The existing GeoTIFF exporter remains working while the longer-term GIS direction is reconsidered. GeoJSON is likely to become the primary GIS export later, but that is a later change of direction rather than current implementation work.

### Persistence

The MVP uses a versioned JSON world file.

A suggested generated-world layout is:

```
world.json
source/
  <FMG export copy>
vault/
  <generated Markdown vault>
```

The world file is authoritative. The vault is regenerable.

SQLite may become necessary later, but that is an open question rather than a current implementation decision.

### Vault

The first vault is read-only. It is a projection of canonical Worldloom state, not a second canonical database.

The exact note schema, frontmatter/property vocabulary, folder layout, and identifier-to-filename mapping require owner review before they are fixed.

### On-demand detail

The first detail level is below FMG's broad representation. Candidate examples include burg districts, notable people, factions, and rumours.

Detail must be stable across repeated resolution, save/load, and equivalent re-import. Address-derived identity and keyed randomness are the intended mechanisms for this stability.

The trigger mechanism is not yet final; a CLI command or batch run are current candidates.

## Pipeline

The intended MVP path is:

1. Read a pinned FMG full JSON export.
2. Validate the supported source/version assumptions without silently broadening input scope.
3. Record source identity, file hash, and FMG version as provenance.
4. Transform FMG map coordinates into the provisional Worldloom internal space.
5. Import the supported FMG structures into canonical Worldloom entities/fields/relationships.
6. Save the canonical world in the versioned JSON world format.
7. Resolve selected local detail on demand using address-derived identity and keyed randomness.
8. Persist resolved detail and its provenance.
9. Render a read-only Obsidian-compatible Markdown vault.
10. Export a raster representation at the configured scale.
11. Permit the vault and raster outputs to be regenerated from the authoritative world file.

## Observed FMG fixture format

The repository contains two real FMG full JSON exports:

- `examples/Pithigy Full 2026-10-02-11-35.json`
- `examples/Viveria Full 2026-10-02-11-31.json`

They were inspected directly from their Git blobs. Both report FMG version **1.153.1**.

| Fixture | File size | FMG seed | Map dimensions | mapId |
| --- | ---: | --- | --- | ---: |
| Pithigy | 7,423,207 characters | 790095095 | 400 × 230 | 1790904880207 |
| Viveria | 8,054,921 characters | 577637767 | 240 × 135 | 1790904565163 |

The sizes above are character counts of the UTF-8 JSON content returned by GitHub's blob interface; they are recorded as fixture observations rather than filesystem byte measurements.

### Top-level structure

Both fixtures have the same top-level keys:

- `info`
- `settings`
- `mapCoordinates`
- `pack`
- `grid`
- `nameBases`

The `info` object contains FMG version, export timestamp, map name, map dimensions, seed, and map ID.

The `settings` object contains units, generation/application settings, map name, and style preset. The fixtures use miles for distance, square area units, feet for height, and degrees Celsius for temperature.

The `pack` object contains the major world structures, including:

- cells
- vertices
- features
- biomes
- cultures
- burgs
- states
- provinces
- religions
- rivers
- goods
- markers
- markets
- deals
- routes
- zones
- measurers
- journeys

The `grid` object separately contains grid cells and vertices, spacing, X/Y cell counts, points, boundary data, seed, and features.

### Cells and adjacency

Pack cells are objects with fields including:

- `i` — cell index
- `v` — vertex indices
- `c` — neighbouring cell indices
- `p` — an X/Y coordinate pair
- `g`, `h`, `area`, `f`, `t` and other terrain/climate attributes
- `biome`, `burg`, `state`, `culture`, `religion`, and `province` references

The fixtures therefore provide a concrete non-grid/irregular cell graph suitable for the planned spatial experiment. The `c` arrays are explicit adjacency references rather than a Worldloom-designed universal grid contract.

Pithigy contains 4,474 pack cells and 9,154 pack vertices. Viveria contains 4,855 pack cells and 9,918 pack vertices.

The separate FMG grid is much larger: Pithigy has 10,032 grid cells and 20,270 grid vertices; Viveria has 9,975 grid cells and 20,158 grid vertices. This distinction is important: the MVP must not accidentally assume that the pack-cell representation and FMG grid are the same spatial layer.

### Burgs and other entities

Both files use index-zero placeholders in several arrays. For example, Pithigy has 507 burg entries but 506 are objects, with index 0 represented by `0`; Viveria has 714 entries with 713 burg objects. Provinces and features show the same placeholder pattern.

Burg objects include a cell reference, X/Y coordinates, numeric ID, state/culture references, name, population, type/group, settlement features, market, treasury/product information, and production/deal references.

States contain names, numeric IDs, neighbouring-state lists, diplomacy entries, urban/rural population values, burg counts, area, cell counts, and province references.

Rivers contain source/mouth cells, discharge, length/width data, parent/basin IDs, an ordered cell list, name, and type.

Routes contain group/name/feature information and point sequences. Route points observed in the fixtures are triples of X, Y, and cell index.

Markers contain coordinates, cell references, type, name, and note text.

Zones and journeys are also present. The fixtures therefore contain authored/generated narrative-adjacent material as well as purely geometric and statistical data.

### Coordinate observations

FMG map-space coordinates appear throughout pack entities and route/river-related structures as numeric X/Y values, while the map dimensions are reported in the `info` object. The fixtures do **not** provide an explicit textual declaration that labels those X/Y values with a universal physical unit or an origin convention suitable for adoption as Worldloom's canonical coordinate system.

The `mapCoordinates` object separately contains latitude/longitude bounds. For Pithigy these are approximately:

- latitude target 27
- north 51.8
- south 24.8
- longitude target 47
- west -23.5
- east 23.5

For Viveria they are approximately:

- latitude target 27
- north 28.8
- south 1.8
- longitude target 48
- west -24
- east 24

These observations support treating geographic latitude/longitude as an explicit export transformation rather than assuming it is the internal map coordinate system.

### Version- and fixture-sensitive complications

The inspection found several facts that should be treated as source-format observations, not Worldloom assumptions:

1. Full exports contain both a pack-cell spatial graph and a separate grid representation.
2. Several indexed arrays contain a zero placeholder followed by object entries.
3. IDs are numeric indices and relationships are frequently encoded as those indices.
4. Some structures contain nested references, such as production entries pointing to goods/deals and route/journey points referring to cells.
5. The source contains both world data and UI/generation configuration in one JSON document.
6. The files contain sizeable derived/trade data such as markets and deals that may not all be required for the first canonical Worldloom representation.
7. The fixtures use different map dimensions, graph sizes, generation templates, and geographic bounds while sharing FMG version 1.153.1.

These are reasons to keep the importer explicitly scoped rather than treating this file as a generic JSON-to-Worldloom mapping.

## Provisional uncertainty treatment

Imported values are currently copied exactly.

A provisional uncertainty descriptor may optionally be attached to imported values, but it has **no behaviour** in the MVP. The vault displays imported values as given.

The purpose is to leave room for the owner to decide later how map-projection uncertainty and population distributions should work without making the importer silently reinterpret source data.

## Provisional world-file semantics

For the MVP, save/load should preserve all state required by the current prototype rather than prematurely deciding which portions are canonical versus recomputable.

The world file therefore temporarily saves **everything needed to reconstruct the current in-memory state**, with an explicit schema version. Whether observations and other derived data should instead be recomputed or cached remains open.

## JSON encoding question

The current Worldloom state contains Python values that JSON cannot represent directly, including tuple keys, tuple locations, and sets. Settlement-suitability data is one known example involving tuple keys.

The save format must therefore define an encoding and prove round-trip fidelity. Address strings are a possible future key representation, but this document deliberately does not choose that approach.

## Fixture disposition and integrity

The two real FMG exports are suitable as repository fixtures. FMG's official documentation states that the generator is MIT-licensed and that maps created with it are owned by their creators; bundled assets can have separate licences. https://github.com/Azgaar/Fantasy-Map-Generator/wiki/Policy

For Worldloom, the recommended location is the existing `examples/` directory because the files are real reference inputs rather than generated build artifacts. They should remain unchanged and should not be used as mutable test output.

Current Git blob SHA-1 identifiers are:

- Pithigy: `881728954d7eef0166f0909410d179ffdc88313f`
- Viveria: `21bab6e2af522dea6393dacda79b79f24bf5a9ce`

These are Git object identifiers, not SHA-256 digests. The CI integrity check should compare the checked-out fixture contents against fixed expected content hashes and fail on missing or modified fixtures. The exact hash algorithm should remain an implementation detail of the CI check unless the owner wants a repository-wide hash convention.

## Open questions

The following remain deliberately unresolved:

- What is the canonical Worldloom internal coordinate system?
- Should the current FMG-map-space identity transform remain the MVP's internal representation?
- How should fuzziness from source projection be represented and eventually used?
- Should imported populations be point values, distributions, or both?
- Which state belongs in the authoritative world file versus recomputed observations?
- Should observations be stored, recomputed, or handled as a combination?
- Is SQLite eventually needed internally?
- What is the minimal stable Markdown vault schema?
- What is the final detail-resolution trigger and batching mechanism?
- How should FMG's numeric source IDs relate to Worldloom identity without making FMG IDs the canonical identity scheme?
- How should tuple keys, tuples, and sets be encoded in versioned JSON while preserving round-trip semantics?
- How should source/version identity be represented so an imported world can be reproduced independently of its original file path?
- When should GeoJSON become the primary GIS export, and what should its round-trip semantics be?

## Deferred second release

The second release can add:

- canonical editing;
- overlay storage;
- runtime producer guards;
- `REFINES` semantics;
- continuity checking after canon changes;
- re-import/update workflows where justified by the first release's evidence.

These are not required to make the first vault MVP useful.
