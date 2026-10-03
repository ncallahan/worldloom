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

1. Finish the current address-derived identity and keyed-randomness work, including the remaining address-derived entity-ID and order-independence steps.
2. Implement the narrowly scoped producer-ownership step: policy enum and exclusive-producer validation only.
3. Run the planned non-grid spatial experiment on a real FMG fixture, including explicit coordinate-transform objects.

## Later

- Implement minimal versioned JSON world save/load.
- Implement the one-time FMG full-JSON importer with source-hash and FMG-version provenance.
- Implement the read-only Obsidian-compatible Markdown vault renderer after the note schema is explicitly designed.
- Implement one stable level of on-demand burg-level detail and persist it.
- Add pinned-input provenance and “why?” explanations to generated notes.
- Keep the existing GeoTIFF export working and add the MVP raster export with configurable scale.
- Investigate GeoJSON as the later primary GIS export and later GIS re-import proof of concept.
- Second release: canon edits, overlays, runtime producer guard, `REFINES`, and continuity checking.
- Longer-term: event semantics, provenance/dependency expansion, snapshots/checkpoints, event-triggered scheduling, specialist-system composition, and broader validation.
- Later directional validation target: a canon-constrained Roshar/Stormlight campaign, subject to copyright/licensing constraints.

## Questions / Decisions Needed

- What is the canonical internal coordinate system?
- How should FMG positional uncertainty and population distributions be represented and eventually affect simulation?
- What exactly belongs in the world file: canonical state only, observations too, or a recomputation/storage combination?
- How should tuple keys, tuple locations, and sets be encoded for JSON round trips?
- Should SQLite eventually supplement or replace JSON internally?
- What is the minimum Markdown note schema and metadata vocabulary?
- How exactly is on-demand detail triggered?
- Which FMG fields are stable enough across FMG versions to become importer contracts?
- How should external source identity and versioning be represented for reproducible imports?
- What invalidation/reconciliation semantics apply when a broad observation changes after local detail has been resolved?
