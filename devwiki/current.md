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

1. **Markdown-vault cleanup — U0: retire the frozen reference exporter and tidy R3 leftovers.** In Draft PR #64.

## Next work

R1, R1b, R2, R3a, and R3b are merged (PRs #59–#63). U0 is the current cleanup task in PR #64.

After U0, continue in this order:

1. **Report-shape unification.** Change `render_import_note` input handling.
2. **Importer cleanup.** Follow report-shape unification.
3. **Step 7.** Return to the planned on-demand local-detail design after the exporter work.

The existing FMG reference-field measurement remains separate: measurement only; no implementation or schema decision is implied.

## Questions / Decisions Needed

- How should explicit authorial amendments to canonical state be represented, including provenance and precedence, and how should dependent derived values become stale? See [[devwiki/questions/canon-amendment]].

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
