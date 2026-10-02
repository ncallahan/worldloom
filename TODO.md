# Worldloom TODO

This is the active working queue for Worldloom.

Unlike the long-term roadmap, this document records work that has been consciously selected for near-term implementation or design. Completed work should be removed from this file; the Git history is the record of what was done.

## Now

1. Finish the current identity work, including address-derived entity IDs and the order-independence experiment.
2. Next, run the selected non-grid spatial experiment against the real FMG fixtures, including cells/adjacency, burg points, river/route polylines, state polygons, and explicit coordinate-transform objects.

## Later

3. Producer ownership: add only the policy enum and exclusive-producer validation. Defer runtime guards, `REFINES`, and overlay storage until the canon-edit workflow is built.
4. Add minimal versioned JSON world save/load.
5. Build the FMG full-JSON importer with pinned source-hash and FMG-version provenance.
6. Build the read-only Obsidian-compatible Markdown vault renderer around a minimal schema after owner review of schema choices.
7. Add one stable, persisted level of on-demand burg/local detail using address-derived identity and keyed randomness.
8. Add "why is this here?" provenance to generated notes.
9. Add configurable-scale raster export while keeping the existing GeoTIFF export working.
10. After the first release, investigate canon edits, overlays, runtime producer guards, `REFINES`, and continuity checking.
11. Later investigate GeoJSON as the primary GIS exchange format and GIS → Worldloom re-import.
12. Continue broader architectural, integration, reproducibility, performance, and domain-model validation as appropriate.

## Questions / Decisions Needed

- What is the canonical Worldloom internal coordinate system?
- Should the MVP's explicit identity transform from FMG map space remain the internal transform?
- How should source projection uncertainty be represented and eventually affect behaviour?
- Should imported population values remain exact, become distributions, or support both?
- What should the authoritative world file contain: canonical state only, observations too, or a mixture?
- Which derived values should be recomputed, stored, or handled as a combination?
- Is SQLite eventually necessary internally?
- What is the minimal stable Markdown vault schema, including frontmatter/properties and folder structure?
- How should Worldloom identity map to generated filenames and links?
- What is the final trigger/batching mechanism for on-demand detail?
- How should FMG numeric IDs relate to Worldloom identities without becoming the canonical identity scheme?
- How should tuple keys, tuple locations, and sets be encoded in versioned JSON with lossless round trips?
- How should source identity/versioning permit reproduction independently of the original file path?
- When should GeoJSON become the primary GIS export, and what should its round-trip semantics be?
