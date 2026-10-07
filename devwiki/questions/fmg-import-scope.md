---
type: question
status: open
summary: "Open and decided questions governing the first FMG importer scope and representation."
related: ["[[experiments/fmg-export-scale-and-structure]]", "[[devwiki/references/fmg-full-json-observed]]", "[[current]]"]
---

# FMG importer scope and representation questions

## Decided: input boundary

The importer input is the FMG full JSON export, not a reduced or alternative FMG export format.

## Decided: import lifecycle

The first importer is a one-time snapshot import. Ongoing synchronization with FMG is outside this experiment.

## Decided: interim coordinate space

Native FMG map coordinates are the interim internal coordinate space. Latitude/longitude is an export projection rather than the canonical imported coordinate space.

## Decided: first-importer scope

The MVP imports the FMG mesh (pack cells and vertices), features and biomes as lookups, cultures, religions, states with neighbors and diplomacy, provinces, burgs, rivers, routes, and markers. It excludes goods, markets, deals, journeys, measurers, military, campaigns, zones, nameBases, coats of arms, and burg production data. Excluded data is not carried into the MVP world state; it remains in the user's original export, which the retained source hash identifies. Military and campaigns may return later as history-event inputs.

This scope is deliberately narrower than the observed full schema: the experiment established that the excluded structures exist, but the MVP does not need them to establish the first import contract.

## Decided: int/float handling

Imported numeric values are preserved exactly as parsed. WorldState.fingerprint keeps its current int-versus-float distinction, but importer logic must not depend on that distinction. The distinction will be revisited when an actual re-import diff exists.

The three canonical exports contain no integral-valued floats: the bounded numeric-serialization check found zero parsed floats for which value.is_integer() was true in each file. This is evidence consistent with JavaScript JSON.stringify normalisation, which serialises integral numeric values without a decimal point; it is evidence, not proof of the originating serializer. No contradiction to this decision was found.

## Decided: -1 sentinels

-1 sentinel values are skipped during entity/reference resolution and recorded as diagnostics in import provenance. The diagnostic mechanism should be a general list capable of recording any tolerated anomaly, rather than a river-specific special case.

This matches the observed FMG river and adjacency sentinel convention without assigning -1 an entity meaning.

## Decided: representation

The MVP uses a hybrid representation. Entities use a Worldloom translation layer with derived Worldloom IDs; the source FMG ID is retained as an attribute, and FMG placeholder records are dropped. The mesh retains FMG index spaces verbatim, with pack and grid spaces explicitly tagged separately. Grid data is retained only for climate values reached through pack.cells[].g. The source export itself is not retained by Worldloom. The SHA-256 of the exact source bytes and basic source metadata (file name, FMG version, map ID, seed) are retained as provenance, so a candidate file can be verified as the one that was imported. Keeping the original export is the user's responsibility.

This preserves the useful stability of FMG's mesh indexing while preventing external FMG entity identifiers from becoming Worldloom's canonical entity identity.

## Decided: fixture policy

The three canonical full exports remain committed in examples/ with -diff and linguist-generated attributes and are read only through experiments/fmg_scale/inspect_fmg.py for bounded inspection. Generated slice fixtures remain committed alongside their .remap.json sidecars.

This keeps the canonical experimental inputs reproducible while preventing routine diffs from being dominated by minified generated JSON.

## Decided: grid climate representation

Grid climate is retained as fmg.grid.climate, keyed by grid cell index, and only for grid cells reached through pack.cells[].g. The many-to-one pack-to-grid mapping is carried by the verbatim g values in fmg.pack.cells and is not duplicated. This keying is provisional and does not preclude later graph-oriented representations.

## Open: internal canonical coordinate space

What coordinate space should become Worldloom's eventual canonical internal spatial representation? Native FMG coordinates remain the interim import space only.

## Open: fuzzy representation of imported values

How should imported values whose source semantics or precision are uncertain be represented without prematurely fixing a universal fuzzy-value model?

## Open: world-file contents

What should the saved Worldloom world file contain, including the retained source-export hash and metadata and imported state versus reproducible provenance? (Embedding a copy of the source export is not part of the MVP.)

## Open: grid.vertices[].c semantics

What do the observed grid.vertices[].c values mean, and should they ever enter the importer contract? They are not needed for the MVP representation above and remain deliberately unresolved.

## Decided: lone surrogates in source strings

Lone UTF-16 surrogate code points found in parsed FMG source strings are tolerated at the FMG importer boundary. Each affected string is sanitised by replacing each lone surrogate with U+FFFD and recorded as a `lone-surrogate` import anomaly. Proper surrogate pairs representing valid astral characters are preserved unchanged.

This is an importer-boundary tolerance only. It does not establish a Worldloom-wide rule that lone surrogates are valid core strings.

## Open: core acceptance of lone surrogates

Should Worldloom core hashing and persistence eventually define an explicit acceptance, rejection, or normalisation policy for lone surrogate code points? The FMG importer does not answer this question.
