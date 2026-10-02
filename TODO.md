# Worldloom TODO

This is the active working queue for Worldloom.

Unlike the long-term roadmap, this document records work that has been consciously selected for near-term implementation or design. Completed work should be removed from this file; the Git history is the record of what was done.

## Now

1. Finish the address-derived identity work in the current identity experiment, including the engine-level order-independence experiment.
2. Start the selected FMG MVP path with the real-fixture non-grid spatial experiment, including explicit source/internal/target coordinate-transform objects.

## Later

- Add minimal versioned world save/load and establish a JSON round-trip encoding for tuple keys, tuple locations, and sets.
- Build the FMG full-JSON importer with source-file hash and FMG-version provenance.
- Render a read-only Obsidian-compatible Markdown vault using an owner-reviewed minimal note schema.
- Add one stable on-demand detail layer below FMG resolution and persist it.
- Add pinned-input provenance and "why is this here?" notes.
- Keep the existing GeoTIFF export working while investigating GeoJSON as the likely future primary GIS export.
- Investigate GIS re-import later as a proof of concept rather than as part of the first import path.
- Second release: canonical edits, overlays, runtime guard, and continuity checking.
- Expand event semantics and event consequences.
- Expand provenance and dependency history.
- Add versioned snapshots/checkpoints.
- Add event-triggered scheduling after the fixed-interval scheduler has been exercised.
- Test composition with increasingly realistic specialist systems.
- Add architectural, integration, reproducibility, performance, and domain-model validation as appropriate.
- Longer-term directional validation: authored-canon layering and continuity using a constrained Stormlight/Roshar campaign, subject to copyright and licence review.

## Questions / Decisions Needed

- What should the canonical internal coordinate system be?
- What uncertainty semantics should imported FMG locations and populations have?
- Should the world file store canonical state only, observations too, derived outputs too, or a recomputable mixture?
- How should tuple keys, tuple locations, sets, and other non-JSON-native values be encoded for lossless round trips?
- Should address strings be used as JSON keys, or should another explicit encoding be used?
- Should SQLite eventually replace JSON as the internal persistence mechanism?
- What minimal vault note schema, metadata vocabulary, folder structure, and link conventions should the owner select?
- What should trigger on-demand detail generation: explicit CLI request, batch resolution, or another mechanism?
- How should source-file identity and FMG version be represented in provenance beyond the pinned hash?
- How should the source/internal/target coordinate-transform contract interact with future GIS CRS policy?
