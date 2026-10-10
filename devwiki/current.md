---
type: process
status: process
summary: Active working queue for Worldloom.
related: ["[[index]]", "[[devwiki/process/development-workflow]]", "[[devwiki/questions/identifier-address-model]]", "[[devwiki/questions/fmg-import-scope]]"]
---

# Current work

This document records work selected for near-term implementation or design. Completed work is removed from the active queue; durable decisions and outcomes belong in their relevant documentation.

## Now

The Markdown-vault exporter refactor, frozen-reference retirement, FMG anomaly severity and surfacing, tolerant Markdown projection, and its hardening follow-up are complete. Extra entity metadata and malformed FMG values are prepared before fingerprinting; provenance attributes are handled independently; surrogate checks use ASCII fast paths. Projection anomalies are classified and surfaced without changing importer behavior or report shapes. Valid imported worlds retain byte-identical generated vault files.

## Next work

1. **Importer cleanup (build_entities).** Simplify entity construction while preserving current import behavior and report shapes.
2. **Step 7.** Return to the planned on-demand local-detail design after the exporter work.

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
