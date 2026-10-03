---
type: vision
status: vision
summary: FMG import, progressive detail, and read-only Obsidian vault MVP direction.
related: ["[[vision/interfaces]]", "[[vision/roadmap]]"]
---

# FMG import → progressive detail → Obsidian vault MVP

## Status

This is a development design note, not a normative architecture or specification change. It records the project-owner's selected MVP focus and keeps provisional choices and open questions visible.

The MVP is a risk-reducing demonstration intended to produce genuinely useful campaign-planning material while exercising progressive resolution, provenance, and address-derived identity. It is not expected to demonstrate the eventual breadth or fidelity of Worldloom.

## Purpose and scope

The first MVP target is:

1. import an Azgaar Fantasy Map Generator (FMG) full JSON export;
2. represent it as Worldloom canonical state;
3. add one stable level of on-demand detail below FMG resolution;
4. render a read-only, Obsidian-compatible Markdown vault;
5. produce a raster export;
6. retain provenance sufficient to explain imported and generated facts.

In scope: FMG full JSON only, one-time snapshot import, source-file hash and FMG version provenance, canonical adoption of imported values, explicit replaceable coordinate transforms, versioned JSON persistence, read-only vault generation, configurable raster scale, and one stable level of on-demand detail.

Out of scope: FMG GeoJSON import, .map/minimal/pack/grid JSON import, responding to later FMG edits or re-exports, Markdown mutation, a final coordinate system, a final uncertainty model, a final world-file representation, SQLite as a settled choice, and making GeoJSON the current primary GIS export.

FMG GeoJSON may later be a proof of concept for reading GIS data back into Worldloom, but that is future work.

## Owner decisions

### Import lifecycle

The importer accepts FMG full JSON only. Import is a one-time snapshot. Later FMG edits and re-exports are deferred until one-time import is solid.

Imported FMG data is adopted as canonical state by import. Its values are nevertheless treated as fuzzy for purposes of a future uncertainty model. Provenance records the source-file hash and FMG version.

### Coordinates

The intended pipeline is:

    FMG import space
        ↓
    internal coordinate space
        ↓
    target coordinate space
        ↓
    export

Both transformations are explicit, replaceable objects. Latitude/longitude is an export projection.

**PROVISIONAL:** until the internal-space question is resolved, internal space equals FMG map space through an explicit identity transform.

### GIS and raster

GeoJSON is likely to become the primary GIS export later, replacing GeoTIFF as the main target. This is a later change of direction, not current work. Existing GeoTIFF export remains working.

Raster export uses a sensible default resolution with a configurable scale factor.

### Persistence

The MVP uses a versioned JSON world file. SQLite may become necessary later, but is open.

Suggested layout:

    world.json
    source/
      <FMG export copy>
    vault/
      <generated vault>

The world file is authoritative; the vault is regenerable.

### Vault

The first vault is read-only. Editing/mutation is a later workflow.

### On-demand detail

The first deeper resolution level is one level below FMG resolution, for example burg districts, notable people, factions, or rumours. Detail should be stable through address-derived identity and keyed randomness and should carry provenance explaining why it exists. The exact CLI/batch trigger remains open.

## Pipeline

    FMG full JSON
          |
          v
    source hash + FMG version
          |
          v
    canonical Worldloom state
          |
          +-------------------+
          |                   |
          v                   v
    on-demand resolution   raster projection
          |
          v
    persisted detail
          |
          v
    read-only Markdown vault

The vault is generated from authoritative state and must be regenerable without becoming a second source of truth.

## Observed FMG format

The two repository fixtures are real FMG full exports on main:

| Fixture | Bytes | FMG version | Seed | Dimensions |
|---|---:|---|---|---:|
| Pithigy | 7,423,584 | 1.153.1 | 790095095 | 400 × 230 |
| Viveria | 8,055,496 | 1.153.1 | 577637767 | 240 × 135 |

Their Git blob object IDs are respectively 881728954d7eef0166f0909410d179ffdc88313f and 21bab6e2af522dea6393dacda79b79f24bf5a9ce. CI uses these IDs as exact fixture-integrity hashes; they are Git SHA-1 object IDs, not SHA-256 digests.

Both have top-level keys:

    info
    settings
    mapCoordinates
    pack
    grid
    nameBases

The main imported collections are under pack:

    cells, vertices, features, biomes, cultures, burgs, states,
    provinces, religions, rivers, goods, markers, markets, deals,
    routes, zones, measurers, journeys

The grid object contains cells, vertices, spacing, cellsY, cellsX, points, boundary, seed, and features.

### Counts observed

| Collection | Pithigy | Viveria |
|---|---:|---:|
| cells | 4,474 | 4,855 |
| vertices | 9,154 | 9,918 |
| features | 21 | 15 |
| biomes | 13 | 13 |
| cultures | 4 | 4 |
| burgs | 507 | 714 |
| states | 4 | 7 |
| provinces | 118 | 72 |
| religions | 9 | 8 |
| rivers | 156 | 53 |
| goods | 71 | 71 |
| markers | 49 | 59 |
| markets | 16 | 15 |
| deals | 7,627 | 10,277 |
| routes | 427 | 570 |
| zones | 11 | 8 |
| measurers | 1 | 1 |
| journeys | 1 | 1 |

These counts are observations of these fixtures, not a general FMG contract.

### Settings, coordinates and units

Pithigy records distance unit mi, distance scale 1, height unit ft, temperature °C, graph 400 × 230 with 10,000 points, and map-coordinate bounds latitude 24.8–51.8 and longitude -23.5–23.5.

Viveria records distance unit mi, distance scale 2, height unit ft, temperature °C, graph 240 × 135 with 10,000 points, and map-coordinate bounds latitude 1.8–28.8 and longitude -24–24.

Cell and vertex coordinates are numeric [x, y] pairs in FMG map space. The file does not explicitly declare the coordinate-origin convention or attach a unit label to these x/y values. Their ranges correspond to the map dimensions, but origin/orientation must therefore remain an implementation fact to verify rather than a Worldloom convention. The explicit distance-unit settings do not prove that raw map-space x/y are directly in miles.

### Cells and adjacency

pack.cells records have i, vertex IDs v, neighbouring cell IDs c, point p, terrain/area fields, and references including biome, population, burg, state, religion and province.

In both fixtures, cell i matches array position. All inspected c adjacency references are valid, and every observed adjacency pair is reciprocal: 26,604/26,604 pairs for Pithigy and 28,980/28,980 for Viveria.

### Burgs and states

Burgs contain cell, state, culture and feature references plus x/y position, name, population and settlement attributes. Both fixtures have a zero placeholder at burg array position 0; populated records inspected thereafter use i matching array position.

State records use i matching array position. Burg state references are within the state array range; state 0 is used by some burgs and corresponds to the Neutrals record in these fixtures.

States contain aggregate burg and cell counts and a province list, but no state-owned cell-ID list analogous to cell.state, and no explicit state polygon geometry was observed. State regions can therefore be reconstructed from cell state references plus state aggregates in these fixtures; the experiment should not assume an FMG state polygon record exists.

### Rivers and routes

River records contain i, source, mouth, discharge, length, width fields, parent, an ordered cells list, basin, name and type. They do not contain an explicit coordinate polyline field in these fixtures.

Routes contain i, group, feature and an ordered points list. Observed route points are [x, y, cell] triples.

A significant fixture/version catch is that Pithigy has three river cell-list entries with -1 (rivers 151, 197 and 291); Viveria has none. -1 is not a valid cell ID and should be treated as a sentinel/data-quality case, not silently as a normal cell reference.

### Other requested collections

The fixtures include features, biomes, cultures, religions and provinces under pack. Features and provinces have a zero placeholder at array position 0. Cultures, religions, states, cells and vertices have populated records starting at index 0.

Markers contain x/y, a cell reference, i, type/icon/name and optional notes.

### ID semantics

There is no universal ID rule.

- cells and vertices use i values matching array indices;
- states, cultures, religions, markers, routes, deals and zones also use inspected i values matching array indices;
- burgs and provinces use a zero placeholder at array position 0, then inspected i values match array positions;
- rivers, goods and markets use record IDs that are not simply array positions. Rivers are sparse/one-based in the inspected fixtures; goods and markets use contiguous one-based IDs.

The importer therefore needs to distinguish array position, record ID and foreign-key reference. Source IDs must not automatically become Worldloom identity.

## Provisional decisions

**PROVISIONAL — imported uncertainty:** import exact FMG values and optionally attach an uncertainty descriptor with no behaviour attached. The vault displays values as given. The owner still needs to decide how map-projection location uncertainty and population distributions behave.

**PROVISIONAL — world-file contents:** save everything currently represented by the MVP world state, with a schema version, while experiments determine whether long-term persistence should store canonical state only, observations too, or a recomputable mixture.

**OPEN — JSON encoding:** JSON cannot directly represent tuple keys or sets. Current state includes (x, y) tuple keys, tuple locations and sets. The save format needs a defined encoding plus round-trip tests. Address strings are a candidate key representation, not a decision.

**OPEN — SQLite:** no decision is made about replacing JSON with SQLite internally.

## Open questions

1. What is the canonical internal coordinate system?
2. How should imported location uncertainty behave?
3. Should imported population values represent centres of distributions, and how should those distributions behave?
4. What belongs in the world file?
5. How should JSON encode tuple keys, tuple locations and sets?
6. Should SQLite replace or supplement JSON?
7. What minimal Obsidian vault schema should be selected?
8. What CLI/batch mechanism should trigger on-demand detail?
9. How should FMG IDs map to Worldloom identifiers?
10. How should the observed FMG river -1 sentinel be handled?
11. Which FMG collections become canonical state in the MVP?
12. When and how should GeoJSON become the primary GIS export?
13. How should GIS-to-Worldloom re-import be approached later?
14. How should FMG re-import/update semantics work after one-time import is solid?

## Development sequence

1. Finish the current identity work: address-derived entity IDs and the order-independence experiment.
2. Producer ownership: policy enum and exclusive-producer validation only now; defer runtime guard, REFINES and overlay store until the second-release canon-edit workflow.
3. Non-grid spatial experiment on the real FMG map, including cells/adjacency, burg points, river/route geometry, state polygons and coordinate-transform objects.
4. Minimal world save/load.
5. FMG importer producing canonical entities with source-hash provenance.
6. Read-only vault renderer with a minimal schema; consult the owner before settling schema choices.
7. Persisted on-demand burg detail.
8. Pinned-input provenance and “why?” in notes.
9. Second release: canon edits, overlays, runtime guard and continuity checking.

## Directional later work

GeoJSON as primary GIS export, GIS-to-Worldloom re-import, FMG re-import/update, and a longer-term Roshar/Stormlight campaign constrained by book canon are directional only.

For any Stormlight/Roshar validation, store extracted facts with citations rather than passages, keep imported canon data out of public repositories, and check licence terms before sharing.

## Fixture repository recommendation

**Recommendation, not a decision:** keep the two real FMG full-JSON fixtures under examples/ because they are useful reproducible MVP integration inputs. Their sizes are about 7.4 MB and 8.1 MB. FMG itself is MIT-licensed, and its policy states that maps created with the Generator are the user's work; CI should pin the fixture contents so later work cannot silently modify these repository copies. If repository growth or hosting limits become a concern, moving or compressing them should be a separate owner decision.
