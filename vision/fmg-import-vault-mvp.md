---
type: vision
status: vision
summary: FMG import, progressive detail, and read-only Obsidian vault MVP direction.
related: ["[[vision/interfaces]]", "[[vision/roadmap]]"]
---

# FMG Import → Worldloom → Obsidian MVP

## Status

This document records the selected first MVP direction and observations from the committed FMG full-JSON fixtures.

Owner decisions are distinguished from provisional implementation choices and open questions. This document does not amend the normative architecture or specification.

## 1. MVP target

The first MVP is a risk-reducing, genuinely useful campaign-planning vertical slice:

    FMG full JSON
        ↓
    one-time snapshot import
        ↓
    Worldloom canonical state
        ↓
    first level of stable on-demand detail
        ↓
    provenance / "why is this here?"
        ↓
    read-only Obsidian-compatible Markdown vault
        ↓
    raster export

The MVP is not intended to demonstrate the eventual breadth of Worldloom. Its purpose is to exercise progressive resolution, provenance, address-derived identity, persistence, and a concrete human-facing projection on a real external world representation.

## 2. Owner decisions

### Input

- Supported input is an Azgaar Fantasy Map Generator (FMG) full JSON export.
- FMG GeoJSON import is out of scope for the MVP.
- .map, minimal JSON, pack JSON, and grid JSON are unsupported inputs.
- GeoJSON may later be used as a proof of concept for reading data back from GIS tools; that is future work, not an MVP commitment.

### Import semantics

- Import is a one-time snapshot operation for the MVP.
- Responding to later FMG edits or re-exports is deferred until one-time import is solid.
- Imported FMG data is adopted as Worldloom canonical state by import.
- FMG values are expected to become fuzzy/uncertain in the Worldloom model, but exact semantics are deferred.
- Provenance records the source file hash and FMG version.

### Coordinates

The intended transformation pattern is:

    FMG source space
        ↓
    source → internal transform
        ↓
    Worldloom internal space
        ↓
    internal → target transform
        ↓
    export target space

Both transformations should be explicit, replaceable objects.

Whether the Worldloom internal coordinate system should eventually be the FMG map space or a distinct Worldloom space is open. The interim implementation should use an explicit identity transform so the boundary exists without prematurely choosing the final internal space.

Lat/long is an export projection, not the assumed canonical internal representation.

### GIS and raster output

- GeoJSON is likely to become the primary GIS export later, replacing GeoTIFF as the main GIS target.
- That is a later direction change, not current work.
- Existing GeoTIFF export should remain working.
- Raster export should use a sensible default resolution with a configurable scale factor.

### Persistence

- The MVP world file is versioned JSON.
- SQLite may become necessary later, but this is open.
- Suggested MVP layout:
  - authoritative versioned Worldloom world JSON;
  - a copy of the FMG source export, identified by hash;
  - generated read-only vault.
- The world file is authoritative.
- The vault is regenerable.

### Vault

- The first vault is read-only.
- Markdown mutation/canon-edit workflow is deferred to the second release.
- The note schema, metadata vocabulary, folder layout, and other detailed vault conventions must be designed separately; they are not selected by this document.

### Progressive detail

The first resolved detail level is one level below FMG resolution, with examples such as burg districts, notable people, factions, and rumours.

Detail must be stable through address-derived identity and keyed randomness. It should carry enough provenance to answer why the detail exists and what inputs produced it.

The trigger mechanism is not final; a CLI command or batch run are candidate mechanisms.

## 3. Observed FMG fixture format

All three committed fixtures identify themselves as FMG version 1.153.1 and use the same top-level structure:

    info
    settings
    mapCoordinates
    pack
    grid
    nameBases

The fixtures were inspected independently and sequentially: Thimaland was used to form initial hypotheses; Pithigy was then processed independently; Viveria was processed after Pithigy had been released from the inspection scope.

### Fixture sizes and identity

| Fixture | Map | JSON UTF-8 bytes | FMG version | Seed | Width × height | Pack cells | Grid cells |
|---|---|---:|---|---|---:|---:|---:|
| Thimaland | Thimaland | 783,840 | 1.153.1 | 306393520 | 240 × 135 | 682 | 1,008 |
| Pithigy | Pithigy | 7,423,584 | 1.153.1 | 790095095 | 400 × 230 | 4,474 | 10,032 |
| Viveria | Viveria | 8,055,496 | 1.153.1 | 577637767 | 240 × 135 | 4,855 | 9,975 |

The byte counts are the UTF-8 byte lengths of the committed JSON content.

### Top-level metadata

info contains at least:

- version
- description
- exportedAt
- mapName
- width
- height
- seed
- mapId

settings contains map units and a nested options object containing generation, map, climate, culture, state, burg, application, and rendering configuration.

mapCoordinates contains latT, latN, latS, lonT, lonW, and lonE.

A significant caution is that these values are not safely interchangeable with ordinary WGS84 latitude/longitude. For example, Thimaland has latT = 102.6 and lonT = 182.4. They therefore must not be treated as a canonical geographic CRS merely because the fields are named lat* and lon*.

### pack

Across the fixtures, pack contains:

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

The first-level records have useful direct cross-references. Examples include cell adjacency and vertex lists, burg-to-cell references, river cell sequences, route point sequences, state cell/burg/province lists, and province/state/burg references.

### grid

The three fixtures contain grid.cells, grid.vertices, grid.spacing, grid.cellsY, grid.cellsX, grid.points, grid.boundary, grid.seed, and grid.features.

The important observation is that pack cells and grid cells are not interchangeable representations. In all three fixtures both arrays use sequential i values beginning at zero, but corresponding positions have different geometry and adjacency. For example, the first pack.cells and grid.cells entries have the same i = 0 while their vertex and neighbour arrays differ.

The pack and grid therefore need separate representation in an importer; matching numeric cell IDs alone is not sufficient evidence that two records represent the same spatial object.

Pack-cell adjacency references stay within the pack-cell range in all three fixtures. Grid-cell adjacency references stay within the grid-cell range. Pack river and route cell references generally use pack-cell IDs.

Pithigy contains three river records with a -1 member at the end of their cells arrays. This is a real fixture value and must not be silently rejected as though every river cell reference were guaranteed to be a valid pack-cell ID. Its exact semantic meaning remains an importer question.

### Placeholder and zero semantics

Several FMG arrays use a leading 0 placeholder:

- features
- burgs
- provinces

This is not universal. Other arrays have a genuine record at index/ID zero. For example:

- cultures[0] is Wildlands;
- religions[0] is No religion;
- states[0] is Neutrals;
- cells[0] and vertices[0] are ordinary records;
- rivers[0], goods[0], markers[0], deals[0], and routes[0] are ordinary records.

The importer must therefore not apply one global "ID zero is placeholder" rule.

### Cells

pack.cells records consistently expose:

    i, v, c, p, g, h, area, f, t,
    haven, harbor, fl, r, conf, biome, s, pop,
    culture, burg, state, religion, province

and can additionally contain routes.

p is a two-number coordinate in FMG map space. Across the fixtures these coordinates are within the map's numeric width/height region, while mapCoordinates provides separate geographic metadata.

Cells also contain compact numeric references and values rather than verbose nested objects. Import therefore requires an explicit interpretation layer rather than treating the JSON structure as already-normalised Worldloom entities.

### Settlements, political entities, rivers and routes

Burg records include at least:

- cell and x/y location;
- i;
- state and culture references;
- name;
- feature;
- capital/port flags;
- population;
- type/group;
- coat of arms;
- settlement features such as citadel, walls, temple and plaza;
- market;
- treasury/product;
- production/deal information.

State records include identity/name, tax and treasury values, neighbours/diplomacy, urban/rural values, burg lists, area, cells, and provinces.

Province records include state/center/burg references and a name/form/full name, plus pole and presentation data.

River records include source, mouth, discharge, length, width, width factors, parent/basin, cell sequence, name, and type.

Route records contain a group, optional name, feature, and a list of coordinate triples whose third value is a cell ID.

Features contain polygon/cell/vertex information and geographic classification such as ocean, island, continent, or isle.

Markers contain map coordinates, cell references, types, names, notes, and optional display offsets.

## 4. Provisional implementation choices

These are deliberately reversible and are not owner-level architectural decisions.

### Imported uncertainty

Until the uncertainty model is selected:

- import exact FMG values;
- optionally attach an uncertainty descriptor;
- do not attach behaviour to that descriptor;
- render the imported value as given in the vault.

### World-file contents

Until experiments determine the appropriate persistence boundary:

- save everything currently needed for faithful MVP restoration;
- include a schema version;
- allow the persisted representation to change when the canonical/derived persistence question is resolved.

### JSON encoding

Current Worldloom state includes structures such as tuple keys, tuple locations, and sets that JSON cannot represent directly.

The save format must therefore define an encoding and round-trip behaviour. Address strings are one possible encoding for keys, but this document deliberately does not select that scheme.

## 5. Open questions

The following remain unresolved:

1. What is the canonical Worldloom internal coordinate system?
2. What exactly does "fuzzy" mean for imported FMG locations and populations?
3. Which canonical state, observations, provenance, and derived material should be saved?
4. Which values should be recomputed after load?
5. Should SQLite eventually replace JSON internally?
6. What is the MVP vault schema?
7. What exact mechanism triggers on-demand detail?
8. How should FMG compact numeric fields map to semantic Worldloom entities and fields?
9. What are the exact semantics of the FMG pack/grid distinction and -1 river-cell sentinel?
10. What JSON encoding should represent Worldloom tuple keys, tuple values, and sets while preserving round trips?
11. Which FMG version range should an eventual importer support beyond the fixtures used here?

## 6. Fixture integrity and repository disposition

The three fixtures are real FMG full JSON exports committed under examples/ and are useful as importer fixtures.

The FMG project states that its Generator source is MIT-licensed and that maps created with it are the creator's work; it also cautions that bundled assets may have separate licences. Worldloom should therefore retain these user-created fixtures in examples/ while avoiding assumptions that every bundled FMG asset has the same licence.

Reference hashes for CI integrity checking are:

    examples/Thimaland Full 2026-10-02-14-17.json
      SHA-256 dc23265844c7dc9ea4ebb6fe58a2e90d805f8d7daf233e181100662b5020281a

    examples/Pithigy Full 2026-10-02-11-35.json
      SHA-256 d0d4b192f9806e1e07c9ad7e01bd0fedc3eee5b3c4b7ece747efea56c5f2fef5

    examples/Viveria Full 2026-10-02-11-31.json
      SHA-256 9f3ac12a3df1d91939f3abd8e1eea094e2de333a4394be7d4ba98ccf54c97eb8

CI should fail if any of these fixture files is missing or differs from its expected hash.

## 7. Fixture inspection conclusions

### Confirmed across all three fixtures

- FMG version is 1.153.1.
- The same top-level full-export structure is present.
- pack and grid are both present and are distinct representations.
- Pack cells and grid cells have the same sequential i numbering but different geometry.
- Cells, vertices, rivers, routes, burgs, states, provinces, cultures, religions, markers, features and other systems use cross-references by numeric IDs.
- Placeholder-zero behaviour is array-specific rather than global.
- FMG map-space coordinates and mapCoordinates are distinct concepts.
- Full exports can be substantially larger than the small Thimaland fixture: the larger fixtures are about 7.4 MB and 8.1 MB of UTF-8 JSON.

### Fixture/version-dependent or requiring caution

- Pithigy contains -1 river-cell references.
- Density and population/state/culture coverage varies substantially between fixtures.
- Some arrays can be empty or contain only their placeholder entry.

### Not established

- A final Worldloom interpretation for every FMG field.
- A final geographic CRS or projection.
- Exact semantic equivalence between pack and grid geometry.
- Exact semantics of all sentinel values.
- A final uncertainty model.
- A final vault schema.
- A final persistence schema.

## 8. Sources

- Azgaar Fantasy Map Generator repository and licence: https://github.com/Azgaar/Fantasy-Map-Generator
- FMG policy/licensing guidance: https://github.com/Azgaar/Fantasy-Map-Generator/wiki/Policy
- FMG release history, including 1.153.1: https://github.com/Azgaar/Fantasy-Map-Generator/releases

These external references are contextual; the fixture observations above are observations of the committed Worldloom files, not claims inferred from external documentation.
