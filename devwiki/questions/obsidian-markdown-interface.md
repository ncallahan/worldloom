---
type: question
status: open
summary: Decisions for the first read-only Obsidian-compatible Markdown projection.
related: ["[[index]]"]
---

# obsidian markdown interface

## Decided: folder/file layout and filenames

The first Markdown interface is a deterministic projection of WorldState. Each entity receives one note at `<kind>/<Title> (<hex>).md`, where kind is the entity-ID prefix and hex is its 12-hex digest. Titles come from the non-empty string `attributes["name"]`, otherwise `Unnamed <kind>`. Titles are NFC-normalised, sanitised, whitespace-collapsed, bounded to 80 characters, and made safe for Windows device names.

Projection requires entity IDs of the form `kind:12hex`, with kind matching the projection's safe identifier grammar. Filenames derive from the current provisional entity IDs. The vault is therefore regenerate-only for now: hand-added links into generated notes may break if the identity scheme changes.

Per-kind indexes live under `indexes/`; `index.md` links those indexes. `_worldloom/import.md` records projection/import information.

## Decided: frontmatter vocabulary

Generated entity notes use this vocabulary, in this order when present:

- `worldloom_generated`
- `worldloom_id`
- `worldloom_kind`
- `worldloom_projection_version`
- `aliases`
- `fmg_collection`
- `fmg_id`
- `fmg_position`
- `fmg_x`
- `fmg_y`
- `provenance_producer`
- `provenance_inputs`
- `importer_version`

Absent source/provenance values are omitted. Native FMG x/y values are labelled explicitly rather than exported as generic coordinates.

## Decided: generated-content marking

Every generated entity note is marked with `worldloom_generated: true`. The vault root also contains `.worldloom-vault.json`, which records the generator, projection version, WorldState fingerprint, and SHA-256 hashes of generated files.

## Decided: provenance in notes

Each entity note has a Provenance section containing producer, inputs, configuration, and a link to the generated import record. The import record includes source metadata, entity counts, anomaly totals, and duplicate-title counts when those observations exist.

## Decided: overwrite safety and determinism

A non-empty directory without a Worldloom marker is never overwritten. With a marker, existing generated files are checked against their recorded hashes; edited files abort the export unless `overwrite_edited=True`. Missing generated files are recreated. Unlisted files are preserved and never overwritten. Generated content is staged before changing the target so a pre-commit write failure leaves the target unchanged.

Exports are deterministic for the same WorldState. The marker fingerprint covers `entities`, `fields`, and `observations`.

## Decided: no interpretation of imported values

The projector reads entities, references, provenance, and observations generically. Imported attribute values are emitted as raw key/value data under the source keys. FMG-specific interpretation is limited to using the `name` attribute for note titles and the explicitly requested FMG metadata vocabulary.

## Decided: link display disambiguation

Wikilink display text is disambiguated generically within each entity kind when multiple entities share a title. A unique title keeps the title as its display. For duplicate titles, Worldloom uses the title of the first single-valued entity reference whose field name comes first alphabetically; list-valued references and mesh references are ignored. If the resulting qualifier is missing or still collides, the entity's 12-hex ID digest is appended. Final display text escapes `|`, `[`, and `]`, and lists are sorted deterministically by title, display, and entity ID.

This rule is generic rather than FMG-specific. In particular, burgs receive their state name as the qualifier because the importer stores a state reference but no province reference; deriving a province from the burg's cell would be an interpretation of FMG fields rather than a generic imported relationship.

## Open design questions

This decision does **not** yet fix:

- how an edited Markdown note becomes an explicit canonical mutation;
- how uncertainty and unresolved information are represented;
- which Atlas-VTT extensions, if any, should receive first-class support;
- whether per-kind templates should exist;
- per-kind disambiguators (for example, province for burgs).
