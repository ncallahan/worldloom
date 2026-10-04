---
type: vision
status: vision
summary: Current FMG import MVP direction, incorporating completed schema and scale measurements.
related: ["[[devwiki/vision/roadmap]]", "[[devwiki/vision/interfaces]]", "[[devwiki/experiments/fmg-export-scale-and-structure]]", "[[devwiki/questions/fmg-import-scope]]"]
---

# FMG Import MVP

## Status

This is a current implementation direction, not normative architecture.

The first concrete Worldloom MVP is to import a real Azgaar Fantasy Map Generator (FMG) full JSON snapshot into Worldloom, preserve the useful source structure and provenance, and establish a foundation for progressive local resolution and human-readable projections.

The MVP is deliberately narrower than the full FMG schema and narrower than Worldloom's eventual simulation goals.

## Purpose

The FMG import MVP is a risk-reducing demonstration of the Worldloom core:

- external specialist output can be adopted into Worldloom without making the external system's identifiers canonical;
- source provenance can be retained;
- multiple spatial/index spaces can be represented without prematurely imposing a universal spatial model;
- imported state can be persisted and queried;
- later detail can be resolved deterministically and independently of generation order;
- human-facing projections can remain derived from authoritative Worldloom state.

It is not an attempt to reproduce FMG internally or to build the eventual full simulation in one step.

## Current progress

The three canonical FMG exports have now been measured directly by the FMG scale-and-structure experiment. The experiment confirms that the 10,000-point examples are useful default-scale integration inputs, but are still relatively small worlds and should not be treated as a performance ceiling.

The measurements establish, among other things:

- FMG full exports contain distinct irregular pack and regular grid structures;
- pack/grid mappings are not one-to-one;
- FMG collections do not share a universal ID/index convention;
- optional keys and heterogeneous numeric shapes occur within a single FMG version;
- richer exports exercise states, provinces, diplomacy, military/campaign fields, economic structures and transport data absent from the small control;
- the existing WorldState measurements are comfortably below the original working resource prediction for these fixtures;
- repeated loading produced matching fingerprints for the tested WorldState sections.

The complete measurements, raw results, and observed schema digest are recorded in [[devwiki/experiments/fmg-export-scale-and-structure]] and [[devwiki/references/fmg-full-json-observed]]. Those documents are experimental/reference material, not importer architecture.

## Current importer boundary

The first importer is explicitly limited to:

1. FMG full JSON exports;
2. one-time snapshot import;
3. source-file hash and FMG-version provenance;
4. the FMG mesh (pack cells and vertices);
5. features and biomes as lookups;
6. cultures and religions;
7. states, including neighbors and diplomacy;
8. provinces;
9. burgs;
10. rivers;
11. routes;
12. markers.

The first importer does not adopt goods, markets, deals, journeys, measurers, military, campaigns, zones, nameBases, coats of arms, or burg production data into MVP world state. Some of these may become later event or simulation inputs.

This boundary is recorded as an owner decision in [[devwiki/questions/fmg-import-scope]]. It is deliberately narrower than the observed FMG schema.

## Representation and provenance

The MVP uses a hybrid representation.

Worldloom entities receive Worldloom-derived identifiers. The source FMG identifier is retained as an attribute where applicable; FMG placeholder records are not promoted to entities.

The FMG mesh retains its source index spaces explicitly. Pack and grid indices must not be collapsed into one identifier space. Grid data is retained for climate values reached through the relevant pack-cell mapping rather than treating the two meshes as interchangeable.

The source export and its hash remain part of import provenance so excluded source structures remain recoverable without making them part of the MVP canonical world state.

Observed anomalies such as FMG `-1` sentinels are not assigned entity meaning. They are skipped during entity/reference resolution and recorded in general import diagnostics.

## Coordinates

Native FMG map coordinates are the interim internal coordinate space for the importer. This is an implementation choice for the MVP, not the final Worldloom canonical coordinate system.

The import/export pipeline remains conceptually:

    FMG source space
          |
          v
    Worldloom internal space
          |
          v
    target/export space

Coordinate transformations should remain explicit objects so that the eventual canonical spatial representation can change without redefining the importer boundary.

Latitude/longitude is a projection/export representation, not the canonical imported coordinate space.

## Numeric values

Imported numeric values are preserved as parsed. Importer logic must not rely on WorldState's current distinction between integer and float values.

The three measured canonical exports contained no parsed floats whose value was integral. This is evidence about the tested files, not a universal FMG serialization guarantee.

## Persistence

Minimal versioned Worldloom save/load remains the next implementation-level persistence step.

The save format must preserve the semantic identity of current state, including structures that ordinary JSON cannot directly represent such as tuple keys, tuple locations, and sets.

The experiment establishes the need for this round-trip work but does not settle the final storage technology. JSON is the immediate persistence experiment; SQLite remains open.

## Progressive resolution

Progressive local detail remains a core reason for the MVP, but it is downstream of the spatial and persistence work that now precedes the importer. The remaining identity/address questions and the deferred producer-ownership validation do not block this MVP sequence.

The intended first demonstration is one stable local level of detail below the imported FMG representation. Generated identities should use the already-developed address-derived identity/keyed-randomness mechanisms where their owner decisions establish that as appropriate.

The exact detail schema and trigger mechanism remain implementation questions. Generated detail must remain derived from authoritative world state and retain enough provenance to explain why it exists.

## Human-facing projection

The first human-facing projection remains a read-only, Obsidian-compatible Markdown vault.

The vault is a projection of Worldloom state, not a competing source of truth. Its minimum note schema and metadata vocabulary should be designed deliberately during implementation rather than inferred from this vision document.

Existing raster export remains useful for inspection. GIS interoperability should continue to prefer established formats and specialist tools rather than recreating GIS functionality inside Worldloom.

## Development sequence

The current sequence is:

1. run the non-grid spatial experiment on a real FMG slice with explicit coordinate-transform objects;
2. implement minimal versioned world save/load;
3. implement the first FMG snapshot importer within the boundary recorded in [[devwiki/questions/fmg-import-scope]];
6. design and implement the minimum read-only Markdown projection;
7. demonstrate one stable level of on-demand local detail;
8. add the provenance and explanatory "why?" path needed by that demonstration.

Later work includes canon edits, overlays, runtime producer guards, continuity checking, richer event semantics, snapshots/checkpoints, FMG re-import/update semantics, and broader specialist-system composition.

## Deliberately open

This MVP does not settle:

- Worldloom's eventual canonical spatial coordinate system;
- a universal uncertainty/fuzzy-value representation;
- the complete world-file contents or long-term storage technology;
- the meaning of unresolved FMG grid vertex references not required by the MVP;
- a universal FMG identifier mapping beyond the explicit MVP translation layer;
- the eventual GIS primary format;
- FMG re-import/update semantics;
- the final Markdown vault schema.

Evidence from the experiments should precede promoting any of these into normative architecture.
