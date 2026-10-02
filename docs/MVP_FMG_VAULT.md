# FMG Import / Vault MVP

## Status

This document records the selected first MVP development focus. It is a design/roadmap record, not a replacement for the normative architecture or specification.

Owner decisions are recorded as **DECIDED**. Temporary implementation choices are **PROVISIONAL**. Unresolved design questions remain **OPEN**. Observations from the FMG fixtures are labelled as observed rather than generalized beyond the inspected files.

## 1. MVP purpose

The first MVP target is:

> Import an Azgaar Fantasy Map Generator (FMG) full JSON export, represent it as Worldloom canonical state, add one stable level of on-demand detail below the imported resolution, and render a read-only Obsidian-compatible Markdown vault plus a raster export.

The purpose is to produce genuinely useful campaign-planning material while exercising:

- progressive resolution;
- address-derived stable identity;
- keyed/order-independent randomness;
- provenance and "why is this here?";
- non-grid spatial representation;
- persistent world save/load;
- GIS/raster export;
- a regenerable human-readable world projection.

This MVP is deliberately **not** expected to demonstrate the eventual breadth or fidelity of Worldloom.

## 2. Scope

### DECIDED: input

Only the FMG **full JSON** export is supported.

Out of scope for this MVP:

- FMG GeoJSON import;
- FMG .map files;
- minimal JSON;
- pack/grid JSON;
- responding to later FMG edits or re-exports.

GeoJSON may later be used as a proof of concept for reading data back from GIS tools, but that is future work rather than a commitment of this MVP.

### DECIDED: import lifecycle

The import is a one-time snapshot import.

The source file is pinned by provenance, including:

- source file hash;
- FMG version.

Imported FMG values are adopted as Worldloom canonical state by the import process, while their eventual uncertainty/fuzziness semantics remain open.

### DECIDED: coordinate pipeline

The intended pipeline is:

    FMG source coordinates
        -> explicit source-to-internal transform
        -> Worldloom internal coordinate space
        -> explicit internal-to-target transform
        -> export coordinates

The two transformations are intended to be explicit, replaceable objects.

**PROVISIONAL:** the internal coordinate space is currently the FMG map coordinate space through an explicit identity transform. The final canonical internal coordinate system remains open.

Lat/long is an export projection, not a decision that FMG's coordinate metadata is already a suitable canonical geodetic CRS.

### DECIDED: raster export

The MVP includes a raster export with:

- a sensible default resolution;
- a configurable scale factor.

The existing GeoTIFF export remains supported. GeoJSON is likely to become the primary GIS export later, but that is a later change of direction rather than current work.

### DECIDED: persistence

The MVP uses a versioned JSON world file.

The intended package layout is approximately:

    world/
      world.json
      source/
        <FMG full export>
      vault/
        <generated Markdown>

The world file is authoritative. The vault is a regenerable projection.

**OPEN:** SQLite may become necessary internally later.

**PROVISIONAL:** save everything needed by the current implementation, with a schema version, until experiments establish whether canonical-only, observation-inclusive, recomputed, or mixed persistence is preferable.

### DECIDED: vault

The first vault renderer is read-only.

The vault is a projection of Worldloom state, not a second canonical database. Editing/mutation workflows are later work.

The exact note schema, metadata vocabulary, folder layout, and identifier presentation must be established separately; agents should surface those choices rather than silently fixing them.

### DECIDED: on-demand detail

The first detail level is one level below the imported FMG resolution. Candidate examples include:

- burg districts;
- notable people;
- factions;
- rumours.

The detail must be stable through address-derived identity and keyed randomness, and must retain enough provenance to answer "why is this here?"

The trigger mechanism is not yet final. A CLI command or batch run are candidate mechanisms.

## 3. MVP pipeline

    FMG full JSON
         |
         v
    pinned one-time import
         |
         v
    source -> internal coordinate transform
         |
         v
    Worldloom canonical state
         |
         +----> raster export
         |
         +----> on-demand detail
                    |
                    v
              stable identity
              keyed randomness
              provenance / "why?"
                    |
                    v
              persisted detail
         |
         v
    read-only Markdown vault

The same canonical world file must be sufficient to regenerate the vault.

## 4. Observed FMG full-JSON format

The following observations come from direct parsing of three repository fixtures with FMG version 1.153.1.

### 4.1 Top-level structure

All three inspected files have these top-level keys:

- info
- settings
- mapCoordinates
- pack
- grid
- nameBases

The full export therefore contains substantially more than a single cell table.

### 4.2 File metadata

| Fixture | Map dimensions | Seed | FMG map ID | Export timestamp | UTF-8 size |
|---|---:|---|---:|---|---:|
| Thimaland | 240 × 135 | 306393520 | 1790914616100 | 2026-10-02T04:17:05.348Z | 783,763 characters |
| Pithigy | 400 × 230 | 790095095 | 1790904880207 | 2026-10-02T01:35:07.166Z | 7,423,207 characters |
| Viveria | 240 × 135 | 577637767 | 1790904565163 | 2026-10-02T01:31:42.419Z | 8,054,921 characters |

The character counts above are from the parsed JSON strings exposed by the GitHub connector; exact on-disk byte counts should be checked by the eventual fixture-integrity job.

### 4.3 Settings and map metadata

The fixtures expose settings including:

- distance unit and scale;
- area unit;
- height unit and exponent;
- temperature scale;
- population rate;
- urbanisation and urban density;
- a nested options structure containing map, geography, climate, culture, lore, units, style, burg, label, military, transport, coastline, generation, application, trade, and 3D settings.

The inspected files use:

- distance unit: mi;
- area unit: square;
- height unit: ft;
- temperature scale: °C;
- population rate: 1000;
- urbanisation: 1;
- urban density: 10.

Distance scale varies between fixtures:

- Pithigy: 1;
- Viveria: 2;
- Thimaland: 3.

### 4.4 Coordinate metadata

The mapCoordinates object contains latT, latN, latS, lonT, lonW, and lonE.

Observed values include:

- Pithigy: latN 51.8, latS 24.8, lonW -23.5, lonE 23.5;
- Viveria: latN 28.8, latS 1.8, lonW -24, lonE 24;
- Thimaland: latN 44.3, latS -58.3, lonW -91.2, lonE 91.2.

Notably, Thimaland has latT = 102.6. This is a concrete reason not to treat FMG's coordinate metadata as an already-validated conventional geographic CRS. The MVP should preserve the source metadata and make coordinate transformation explicit rather than silently treating these values as canonical latitude/longitude.

### 4.5 pack and grid are different spatial structures

The full exports contain both an irregular pack representation and a separate grid representation.

Observed counts:

| Fixture | pack.cells | pack.vertices | grid.cells | grid.vertices |
|---|---:|---:|---:|---:|
| Thimaland | 682 | 1,430 | 1,008 | 2,082 |
| Pithigy | 4,474 | 9,154 | 10,032 | 20,270 |
| Viveria | 4,855 | 9,918 | 9,975 | 20,158 |

The pack.cells records are irregular cells with:

- i: cell ID;
- v: vertex references;
- c: neighbouring cell references;
- p: point/centre coordinate;
- g: corresponding grid-cell reference;
- h: height;
- area;
- f: feature;
- t: terrain/type value;
- haven, harbor, fl, r, conf;
- biome, s, pop, culture, burg, state, religion, province;
- routes in the larger fixtures.

The grid.cells records are a separate regular-grid structure with keys including:

- i;
- v;
- c;
- b;
- f;
- t;
- h;
- temp;
- prec.

This distinction is important for the non-grid spatial experiment: the MVP should not collapse the FMG pack representation into a rectangular raster merely because a raster export is also required.

### 4.6 Adjacency and IDs

Scripts run against all three inspected fixtures found:

- pack cell IDs are unique and contiguous from 0 to N-1;
- every pack-cell vertex reference is within the pack vertex array;
- every pack-cell adjacency reference is within the pack-cell array;
- every pack cell has at least 3 neighbours in these fixtures;
- observed maximum adjacency is 9 for Thimaland, 12 for Pithigy, and 10 for Viveria.

These are observations about the inspected exports, not a universal FMG contract.

### 4.7 Entity collections

The pack object contains these array collections in all three fixtures:

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

Collection sizes vary substantially. For example:

| Collection | Thimaland | Pithigy | Viveria |
|---|---:|---:|---:|
| cultures | 2 | 4 | 4 |
| burgs | 10 | 507 | 714 |
| states | 1 | 4 | 7 |
| provinces | 1 | 118 | 72 |
| religions | 3 | 9 | 8 |
| rivers | 49 | 156 | 53 |
| routes | 9 | 427 | 570 |
| deals | 130 | 7,627 | 10,277 |

There are placeholder/sentinel patterns that require care. In the inspected files:

- the first burg entry is 0;
- the first province entry is 0;
- state index 0 is Neutrals;
- culture index 0 is Wildlands;
- religion index 0 is No religion;
- river IDs begin at 1 in the inspected samples;
- route IDs begin at 0.

The numeric value 0 therefore cannot be interpreted uniformly as a normal entity record or as an absence marker across all FMG collections.

### 4.8 Rivers, routes and geometry

Rivers are represented as records containing, among other fields:

- source cell;
- mouth cell;
- discharge;
- length;
- width;
- width factor;
- source width;
- parent;
- a list of cell IDs;
- basin;
- name;
- type.

Routes contain a group, feature, and a list of coordinate triples. This provides a direct basis for the planned non-grid experiment involving burg points and river/route polylines.

States and provinces also contain cell references and other political metadata. Features contain cell and vertex references and geometric/area information.

### 4.9 Name bases and generated content

The nameBases structure is large and contains language/culture name-generation data, including lists of names and generation parameters. It should not be assumed to be canonical Worldloom culture/language state merely because it occurs in the same export.

Likewise, FMG exports contain generated descriptions, notes, markers, military information, market/deal data, and other authored/generated material. The importer needs an explicit mapping policy rather than blindly treating every FMG property as a Worldloom entity.

## 5. Fixture observations and repository disposition

The three inspected files are useful fixtures because they span:

- a small map with sparse entities (Thimaland);
- a substantially larger pack graph (Pithigy);
- a different 240 × 135 map with many burgs/routes/deals (Viveria).

They should remain immutable reference inputs for the import work.

FMG's official project documentation states that the generator is MIT-licensed and that maps created with it are the creator's property. It also notes that bundled assets can carry separate licences. The fixture files should therefore be acceptable as project test/reference inputs as far as the FMG-generated-map licensing statement goes, but the repository should retain the source-file provenance and should not assume that every embedded asset has the same licence.

**Recommendation:** keep the three user-supplied FMG JSON exports under examples/ as immutable reference fixtures for development and CI. Do not modify them in-place. If a future public distribution raises a licence question about embedded assets, review the exact FMG version and bundled-asset licences before redistribution.

## 6. Provisional decisions and open questions

### PROVISIONAL: imported uncertainty

Imported values are initially preserved exactly.

An optional uncertainty descriptor may be attached to a location or population value, but the descriptor has no behavioural effect in this MVP. The vault shows the imported value as given.

This is deliberately not a final uncertainty model.

### OPEN: canonical internal coordinate system

The MVP does not decide whether FMG map space becomes the long-term Worldloom internal coordinate system. The current identity transform is only a replaceable provisional bridge.

### OPEN: persistence semantics

Experiments must establish whether the world file should persist:

- canonical state only;
- observations as well;
- derived outputs as well;
- or a mixture with deterministic recomputation.

**PROVISIONAL:** save everything needed by the current implementation, with an explicit schema version, so this choice can change without losing information.

### OPEN: JSON representation of current state

The current Python state contains structures that JSON cannot represent directly, including:

- tuple keys such as (x, y);
- tuple-valued locations;
- sets.

The save format therefore needs an explicit encoding and round-trip test.

Address strings are a possible key representation, but this document does **not** select that solution.

### OPEN: SQLite

SQLite may become necessary for larger worlds or efficient partial access. No SQLite architecture is selected for this MVP.

### OPEN: vault schema

The note schema, frontmatter/metadata vocabulary, folder structure, links, and handling of generated versus canonical information require owner review before becoming an interface contract.

### OPEN: detail trigger

CLI-triggered and batch detail generation are both plausible. The first implementation should use the smallest mechanism that allows the stability experiment to run; this does not settle the eventual interaction model.

## 7. Sequencing

1. Finish identity work: remaining address-derived entity ID work and the engine-level order-independence experiment.
2. Producer ownership: implement only the policy enum and exclusive-producer validation. Defer runtime guard, REFINES, and overlay storage until the canonical-edit workflow is built in the second release.
3. Run the non-grid spatial experiment against a real FMG fixture, including cells/adjacency, burg points, river/route polylines, state polygons, and explicit coordinate-transform objects.
4. Add minimal versioned world save/load and settle a first round-trip encoding.
5. Build the FMG full-JSON importer with source-hash provenance.
6. Build the read-only vault renderer using an owner-reviewed minimal schema.
7. Add one stable on-demand burg/detail layer and persist it.
8. Add pinned-input provenance and "why is this here?" notes.
9. Second release: canonical edits, overlays, runtime guard, and continuity checking.

## 8. Longer-term validation target

A later directional validation target is a Stormlight/Roshar campaign constrained by published book canon. This is not current implementation work.

If used, the validation should test:

- authored-canon layering;
- observer knowledge;
- continuity checking;
- conflict between generated and authored constraints.

Copyright-sensitive material should be represented as extracted facts with citations rather than copied passages, and imported canon data should not be placed in a public repository without checking the relevant licence terms.

## 9. Proposed normative edits for owner review

No changes to docs/ARCHITECTURE.md or docs/SPECIFICATION.md are made by this work.

Potential future normative edits, subject to owner approval:

1. **Snapshot import semantics:** explicitly define the relationship between a pinned external source snapshot and the resulting canonical state, including source identity/version provenance.
2. **Coordinate transform contract:** define a replaceable source/internal/target transform abstraction once the spatial experiments demonstrate the required operations.
3. **Progressive-detail identity:** make stable address-derived identity and deterministic keyed randomness an explicit requirement for resolution where stability across runs is required.
4. **Persistence contract:** define what a world file guarantees about canonical state, observations, derived data, schema versioning, and regeneration.
5. **Projection/vault semantics:** if the read-only vault proves useful, explicitly define it as a regenerable projection rather than a second canonical representation.

These are proposals, not decisions.
