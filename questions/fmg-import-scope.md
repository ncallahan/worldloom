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

## Open: first-importer scope

Should the first importer explicitly exclude goods, markets, deals, military, diplomacy, journeys, and measurers? The experiment demonstrates that these structures exist in the canonical full exports, so exclusion should be an explicit scope choice rather than an assumption based on the small control.

## Open: fingerprint numeric normalisation

Should numerically equal integer and float values be treated as identical by WorldState.fingerprint, or should their JSON scalar types remain significant? The current implementation distinguishes values such as 1 and 1.0.

## Open: -1 river sentinels

Recommended, not decided: skip -1 during entity resolution and record a diagnostic rather than treating -1 as an entity identifier. The observed files contain -1 in river-cell lists, and vertex adjacency also uses sentinel values.

## Open: FMG arrays versus translation layer

Should the importer preserve FMG arrays and their native index spaces directly, or translate them into Worldloom-owned identifiers and relationships? The experiment establishes the existence of multiple interacting index spaces but does not select either representation.
