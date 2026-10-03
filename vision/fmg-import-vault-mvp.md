---
type: vision
status: vision
summary: FMG import, progressive detail, and read-only Obsidian vault MVP direction.
related: ["[[vision/interfaces]]", "[[vision/roadmap]]"]
---

# FMG Import and Markdown Vault MVP

## Status

Selected first MVP target. This is an implementation/design plan, not a replacement for the normative architecture or specification.

## Purpose

Import an Azgaar Fantasy Map Generator (FMG) **full JSON export**, represent it as Worldloom canonical state, resolve one stable level of additional local detail on demand, and render a read-only Obsidian-compatible Markdown vault plus a raster export.

The purpose is genuinely useful campaign-planning output while exercising progressive resolution, provenance, address-derived identity, and keyed deterministic randomness. It is not expected to demonstrate the eventual breadth of Worldloom.

## Scope and owner decisions

### Input

Only FMG **full JSON exports** are supported.

Out of scope: FMG GeoJSON, `.map` files, minimal/pack/grid-only JSON, and responding to later FMG edits or re-exports. GeoJSON may later be a proof of concept for reading data back from GIS tools.

Import is a one-time snapshot operation. Provenance records the source-file hash and FMG version.

### Coordinates

The intended pipeline is:

    FMG source -> source-to-internal transform -> Worldloom internal
        -> internal-to-target transform -> export

Both transforms are explicit, replaceable objects. The canonical internal coordinate system is **OPEN**. For the MVP, internal space equals FMG map space through an explicit identity transform. Lat/long is an export projection.

### Canonical adoption and uncertainty

Imported FMG data is adopted as canonical state by import, while its values are considered potentially fuzzy for later modelling.

**PROVISIONAL:** import exact values and optionally attach an uncertainty descriptor, with no behaviour attached to that descriptor. The vault displays values as imported. The owner still needs to decide how uncertainty affects later simulation.

### Progressive detail

One level below FMG resolution may include burg districts, notable people, factions, or rumours. Generation is on demand through a CLI command or batch run; the exact trigger mechanism is **OPEN**.

Generated identities must remain stable through address-derived identity and keyed randomness. Generated facts must retain provenance sufficient to answer “why is this here?”.

### Persistence

The MVP uses a versioned JSON world file. Suggested layout:

    world.json
    source/<FMG export>
    vault/<generated Markdown>

The world file is authoritative; the vault is a regenerable read-only projection.

**OPEN:** whether JSON remains the internal persistence mechanism or is eventually supplemented/replaced by SQLite.

**OPEN:** what belongs in the saved world file. **PROVISIONAL:** save everything initially, with a schema version, so later experiments can change the policy without losing information.

### Export

Keep the existing GeoTIFF export working. Raster export uses a sensible default resolution with a configurable scale factor.

A later direction is for **GeoJSON to become the primary GIS export**, potentially replacing GeoTIFF as the main GIS target. That is not current implementation work.

## Observed FMG fixture

Repository fixture:

    examples/Thimaland Full 2026-10-02-14-17.json

Observed directly:

- FMG version: `1.153.1`
- export timestamp: `2026-10-02T04:17:05.348Z`
- map name: `Thimaland`
- dimensions: 240 x 135
- seed: `306393520`
- map ID: `1790914616100`
- top-level keys: `info`, `settings`, `mapCoordinates`, `pack`, `grid`, `nameBases`
- `mapCoordinates`: latT 102.6, latN 44.3, latS -58.3, lonT 182.4, lonW -91.2, lonE 91.2
- `pack` includes cells, vertices, features, biomes, cultures, burgs, states, provinces, religions, rivers, goods, markers, markets, deals, routes, zones, measurers, and journeys
- counts include 682 pack cells, 1,430 pack vertices, 10 burgs, 1 state, 2 cultures, 3 religions, 1 province, 49 rivers, 9 routes, 5 features, 14 markers, and 13 biomes
- pack cells contain numeric IDs plus adjacency/geometry references and population, culture, burg, state, religion, and province fields
- burgs contain coordinates, cell/state/culture references, names, population, type/group, economic fields, and heraldic data
- rivers contain source/mouth IDs, discharge, length, width information, cell paths, basin, name, and type
- routes contain a group, feature reference, and point sequences that can include a cell ID
- the separate `grid` representation has 1,008 cells and 2,082 vertices, so a full export contains more than one spatial graph/resolution representation
- `features`, `burgs`, and `provinces` have leading numeric `0` entries in this fixture; these are observed FMG data and must not be silently discarded until importer semantics are defined
- the first state is a `Neutrals` record with index 0, so zero-valued records can have semantic significance
- `settings` includes user-facing units/configuration and generation/application configuration

These are fixture observations, not a claim that every FMG export has the same shape.

## JSON representation catch

Current Worldloom state contains structures JSON cannot represent directly, including tuple-keyed mappings, tuple locations, and sets.

The save format therefore needs explicit encoding and round-trip tests.

**OPEN:** whether address strings, structured objects, arrays, or another representation should encode these values. Do not decide this here.

## Fixture disposition

The committed FMG export should remain available as a reference fixture for importer and spatial experiments and must not be modified.

Before redistributing additional generated maps, check the applicable FMG/tool licence and any map-specific sharing constraints.

A CI integrity check should compare the committed fixture bytes against recorded SHA-256 values and fail if either fixture changes.

## Delivery sequence

1. Finish address-derived identity and keyed-randomness work.
2. Producer ownership: policy enum and exclusive-producer validation only. Defer runtime guard, `REFINES`, and overlay storage until the canon-edit workflow.
3. Non-grid spatial experiment on a real FMG fixture, including coordinate-transform objects.
4. Minimal world save/load.
5. FMG importer producing canonical entities with source-hash provenance.
6. Read-only Markdown vault renderer; note schema and metadata vocabulary require an explicit design step.
7. Stable on-demand burg-level detail and persistence.
8. Pinned-input provenance and “why?” in notes.
9. Second release: canon edits, overlays, runtime guard, and continuity checking.

## Open questions

- Canonical internal coordinate system.
- FMG positional uncertainty and population distributions, and how they eventually affect simulation.
- What exactly belongs in the saved world file; recompute versus persist.
- Whether SQLite supplements/replaces JSON.
- Encoding tuple keys, tuple locations, and sets for JSON round trips.
- Minimum Markdown note schema and metadata vocabulary.
- On-demand detail trigger.
- Which FMG fields are stable across versions enough to become importer contracts.

## Normative edits proposed for owner review

No normative files are changed by this work.

Potential future normative edits, after experiments:

1. Snapshot-import semantics and source identity/version recording.
2. Coordinate-transform contract and round-trip expectations.
3. Persistence semantics for canonical versus derived state.
4. Stability and provenance requirements for progressive-resolution details.

These are proposals only; implementation evidence should precede adopting them.


## Cross-fixture observations

The two larger reference fixtures were processed independently after Thimaland; neither larger fixture was held in memory at the same time as the other.

### Pithigy

- FMG version: `1.153.1`; map: Pithigy; dimensions: 400 x 230; seed: `790095095`; map ID: `1790904880207`.
- File size observed through the GitHub blob: 7,423,207 characters.
- `mapCoordinates`: latT 27, latN 51.8, latS 24.8, lonT 47, lonW -23.5, lonE 23.5.
- Pack counts: 4,474 cells; 9,154 vertices; 21 features; 13 biomes; 4 cultures; 507 burgs; 4 states; 118 provinces; 9 religions; 156 rivers; 49 markers; 16 markets; 7,627 deals; 427 routes; 11 zones; 1 measurer; 1 journey.
- Grid counts: 10,032 cells and 20,270 vertices.
- The cell, river, route, feature, province, and leading-zero patterns observed in Thimaland also occur here, so they are not unique to that small fixture.

### Viveria

- FMG version: `1.153.1`; map: Viveria; dimensions: 240 x 135; seed: `577637767`; map ID: `1790904565163`.
- File size observed through the GitHub blob: 8,054,921 characters.
- `mapCoordinates`: latT 27, latN 28.8, latS 1.8, lonT 48, lonW -24, lonE 24.
- Pack counts: 4,855 cells; 9,918 vertices; 15 features; 13 biomes; 4 cultures; 714 burgs; 7 states; 72 provinces; 8 religions; 53 rivers; 59 markers; 15 markets; 10,277 deals; 570 routes; 8 zones; 1 measurer; 1 journey.
- Grid counts: 9,975 cells and 20,158 vertices.
- The same broad full-export structure and leading-zero placeholder/semantic-entry pattern occur here, while concrete counts, geometry, names, political structure, and other values vary substantially by map.

### Fixture conclusions

Across all three inspected fixtures, the stable-looking structural features include the six top-level sections, the `pack` and `grid` spatial representations, indexed records with zero entries in several arrays, cell IDs and references, burg point records, river cell paths, route point sequences, and map-coordinate metadata. The concrete counts and generated content are clearly map-dependent. FMG version 1.153.1 is common to all three current fixtures, so these observations do not yet establish cross-version compatibility.

Recorded SHA-256 values are maintained in `.github/fmg-fixture-sha256.txt` and checked by CI. These are byte-level fixture hashes; the earlier Git blob SHA-1 values are not used as fixture integrity hashes.
