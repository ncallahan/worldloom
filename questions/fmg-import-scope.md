---
type: question
status: open
summary: "Open and decided questions governing the first FMG importer scope and representation."
related: ["[[experiments/fmg-export-scale-and-structure]]", "[[references/fmg-full-json-observed]]", "[[current]]"]
---

# FMG importer scope and representation questions

## Decided: input boundary

The importer input is the FMG full JSON export, not a reduced or alternative FMG export format.

## Decided: import lifecycle

The first importer is a one-time snapshot import. Ongoing synchronization with FMG is outside this experiment.

## Decided: interim coordinate space

Native FMG map coordinates are the interim internal coordinate space. Latitude/longitude is an export projection rather than the canonical imported coordinate space.

## Decided: first-importer scope

The MVP imports the FMG mesh (pack cells and vertices), features and biomes as lookups, cultures, religions, states with neighbors and diplomacy, provinces, burgs, rivers, routes, and markers. It excludes goods, markets, deals, journeys, measurers, military, campaigns, zones, nameBases, coats of arms, and burg production data. Excluded data remains recoverable through the retained source-export hash and provenance rather than becoming part of the MVP world state. Military and campaigns may return later as history-event inputs.

This scope is deliberately narrower than the observed full schema: the experiment established that the excluded structures exist, but the MVP does not need them to establish the first import contract.

## Decided: int/float handling

Imported numeric values are preserved exactly as parsed. WorldState.fingerprint keeps its current int-versus-float distinction, but importer logic must not depend on that distinction. The distinction will be revisited when an actual re-import diff exists.

The three canonical exports contain no integral-valued floats: the bounded numeric-serialization check found zero parsed floats for which value.is_integer() was true in each file. This is evidence consistent with JavaScript JSON.stringify normalisation, which serialises integral numeric values without a decimal point; it is evidence, not proof of the originating serializer. No contradiction to this decision was found.

## Decided: -1 sentinels

-1 sentinel values are skipped during entity/reference resolution and recorded as diagnostics in import provenance. The diagnostic mechanism should be a general list capable of recording any tolerated anomaly, rather than a river-specific special case.

This matches the observed FMG river and adjacency sentinel convention without assigning -1 an entity meaning.

## Decided: representation

The MVP uses a hybrid representation. Entities use a Worldloom translation layer with derived Worldloom IDs; the source FMG ID is retained as an attribute, and FMG placeholder records are dropped. The mesh retains FMG index spaces verbatim, with pack and grid spaces explicitly tagged separately. Grid data is retained only for climate values reached through pack.cells[].g. A copy of the source export and its hash is retained with the world.

This preserves the useful stability of FMG's mesh indexing while preventing external FMG entity identifiers from becoming Worldloom's canonical entity identity.

## Decided: fixture policy

The three canonical full exports remain committed in examples/ with -diff and linguist-generated attributes and are read only through experiments/fmg_scale/inspect_fmg.py for bounded inspection. Generated slice fixtures remain committed alongside their .remap.json sidecars.

This keeps the canonical experimental inputs reproducible while preventing routine diffs from being dominated by minified generated JSON.

## Open: internal canonical coordinate space

What coordinate space should become Worldloom's eventual canonical internal spatial representation? Native FMG coordinates remain the interim import space only.

## Open: fuzzy representation of imported values

How should imported values whose source semantics or precision are uncertain be represented without prematurely fixing a universal fuzzy-value model?

## Open: world-file contents

What should the saved Worldloom world file contain, including the retained source export/hash and imported state versus reproducible provenance?

## Open: grid.vertices[].c semantics

What do the observed grid.vertices[].c values mean, and should they ever enter the importer contract? They are not needed for the MVP representation above and remain deliberately unresolved.
