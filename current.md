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

1. Finish the current address-derived identity work in draft PR #19, including address-derived entity IDs and the engine-level order-independence experiment.
2. Next selected step: run the non-grid spatial experiment on the real FMG fixture, covering cell adjacency, burg points, river/route geometry, state polygons, and explicit coordinate-transform objects.

## Later

- Producer ownership: after the current identity work, implement the policy enum and exclusive-producer validation; defer the runtime guard, REFINES, and overlay store until the second-release canon-edit workflow.
- Implement minimal world save/load using versioned JSON.
- Implement the one-time FMG full-JSON importer with source-file-hash and FMG-version provenance.
- Implement the read-only Obsidian-compatible Markdown vault with a minimal schema; consult the owner before fixing schema choices.
- Implement one level of persisted on-demand burg detail using address-derived identity and keyed randomness.
- Add pinned-input provenance and “why?” explanations to generated notes.
- Second release: canon edits, overlays, the runtime guard, and continuity checking.
- Keep the existing GeoTIFF export working while the later GeoJSON-primary direction is evaluated.
- Explore GIS-to-Worldloom re-import later, potentially using FMG GeoJSON as a proof of concept.
- Expand provenance and dependency history.
- Add versioned snapshots/checkpoints.
- Add event-triggered scheduling after the fixed-interval scheduler has been exercised.
- Test composition with increasingly realistic specialist systems.
- Add architectural, integration, reproducibility, performance, and domain-model validation as appropriate.
- Longer-term validation target: a Roshar/Stormlight campaign constrained by book canon, testing authored-canon layering, observer knowledge, and continuity checking. Store extracted facts with citations rather than passages, keep imported canon data out of public repositories, and check licence terms before sharing.

## Questions / Decisions Needed

- What is the canonical internal coordinate system?
- How should imported location uncertainty from the map projection be represented and behave?
- Should imported population values be treated as centres of distributions, and how should those distributions behave?
- What belongs in the world file: canonical state only, observations too, or a mixture with recomputation?
- How should JSON encode tuple keys, tuple locations, and sets so save/load is lossless? Address strings are a candidate key representation, but no choice is made here.
- Should SQLite replace or supplement JSON internally?
- What exact minimal schema should the read-only Obsidian vault use?
- What exact CLI/batch mechanism should trigger on-demand detail?
- How should FMG source IDs map to Worldloom identifiers?
- How should the observed FMG river-cell -1 sentinel be handled?
- Which FMG collections should become canonical Worldloom state in the MVP versus retained source material or later imports?
- How should source identity and versioning support reproducible imported datasets?
- How should observation version history and provenance tracing be represented?
- What invalidation semantics apply when a broad observation changes?
- How should already-resolved facts be reconciled after an explicit world change?
- How should per-module seeds and execution configuration support deterministic regeneration?
- Should derived outputs be stored, recomputed, or handled as a combination?
- What should the canonical interface for external specialist systems look like?
- Which state is authoritative, and which values should always be recomputable?
- What minimum snapshot semantics are required for branching and reproducibility?
