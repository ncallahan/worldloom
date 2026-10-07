---
type: process
status: process
summary: Active working queue migrated from the repository TODO.
related: ["[[index]]", "[[devwiki/process/development-workflow]]", "[[devwiki/questions/identifier-address-model]]", "[[devwiki/questions/fmg-import-scope]]"]
---

# Current work

This is the active working queue for Worldloom.

Unlike the long-term roadmap, this document records work that has been consciously selected for near-term implementation or design. Completed work should be removed from this file; the Git history is the record of what was done.

## Now

1. **Minimum read-only Obsidian-compatible Markdown projection.** The first read-only Markdown projection is implemented. Next: demonstrate one stable level of on-demand local detail and its provenance (step 7 of the roadmap sequence in [[devwiki/vision/roadmap]]).

## Later

- **Deferred: exclusive-producer validation.** The narrow validation step was deliberately skipped in favour of the spatial experiment; revisit it after the MVP path is further established. Do not add runtime guards, REFINES, or overlay-store semantics without separate authorisation.

- Inspect the generated GeoTIFF in an external GIS application and use the result to inform the next interface/internal-model experiment.
- Use the raster and spatial-field experiments to inform the eventual spatial-data contract without prematurely fixing it.
- Prefer an adapter and standard data exchange over implementing equivalent specialist functionality inside Worldloom.
- Expand event semantics and event consequences.
- Expand provenance and dependency history.
- Add versioned snapshots/checkpoints.
- Add event-triggered scheduling after the fixed-interval scheduler has been exercised.
- Test composition with increasingly realistic specialist systems.
- Add architectural, integration, reproducibility, performance, and domain-model validation as appropriate.
