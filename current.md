---
type: process
status: process
summary: Active working queue migrated from the repository TODO.
related: ["[[index]]", "[[process/development-workflow]]"]
---

# Current work

This is the active working queue for Worldloom.

Unlike the long-term roadmap, this document records work that has been consciously selected for near-term implementation or design. Completed work should be removed from this file; the Git history is the record of what was done.

## Now

1. Finish the identity work, including address-derived entity IDs and the order-independence experiment.
2. Prepare the non-grid spatial experiment on the real FMG fixtures:
   - cell adjacency;
   - burg point locations;
   - river and route polylines;
   - state polygons;
   - explicit source/internal/target coordinate-transform objects.

## Next

- Implement the minimal producer-ownership policy enum and exclusive-producer validation only.
- Implement minimal versioned JSON world save/load.
- Implement the one-time FMG full-JSON importer with source-file hash and FMG-version provenance.
- Design and implement the first read-only Obsidian-compatible Markdown vault, after surfacing the note-schema choices for owner review.
- Implement stable on-demand burg-level detail and persistence.
- Add pinned-input provenance and "why?" explanations.

## Later

- Defer the producer-ownership runtime guard, REFINES semantics, and overlay store until the second release canon-edit workflow.
- Keep GeoTIFF export working while evaluating GeoJSON as the likely future primary GIS export.
- Add canon edits and controlled Markdown mutation.
- Add overlays and runtime ownership enforcement.
- Add continuity checking.
- Expand event semantics and event consequences.
- Expand provenance and dependency history.
- Add versioned snapshots/checkpoints beyond the MVP world file.
- Add event-triggered scheduling after the fixed-interval scheduler has been exercised.
- Test composition with increasingly realistic specialist systems.
- Add architectural, integration, reproducibility, performance, and domain-model validation as appropriate.
- Consider SQLite as an internal persistence implementation if experimentation shows that JSON is no longer sufficient.
- Consider FMG GeoJSON re-import as a GIS interoperability proof of concept.

## Questions / Decisions Needed

- What is the canonical Worldloom internal coordinate system?
- What exactly does "fuzzy" mean for imported FMG locations and populations?
- Should the MVP world file save canonical state only, observations too, or another combination?
- Which values should be recomputed after load, and which should be persisted?
- Should SQLite eventually replace JSON internally?
- What is the minimal vault schema, metadata vocabulary, and folder/file convention?
- What exact mechanism triggers on-demand detail: CLI command, batch run, or another mechanism?
- How should FMG compact numeric fields map to semantic Worldloom entities and fields?
- What exact semantics apply to the FMG pack/grid distinction?
- How should the FMG -1 river-cell sentinel be represented?
- What JSON encoding should represent tuple keys, tuple values, and sets while preserving round trips?
- Which FMG version range should the eventual importer support?
- How should external source identity and versioning be represented so imported datasets can be reproduced independently of their original file path?
- How should observation version history, invalidation, and provenance tracing be represented?
- How should already-resolved facts be reconciled after an explicit world change?
- How should per-module seeds and execution configuration support deterministic regeneration?
- Which state is authoritative, and which values should always be recomputable?
- What minimum snapshot semantics are required for branching and reproducibility?
