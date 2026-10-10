---
type: question
status: open
summary: Decisions for the first read-only Obsidian-compatible Markdown projection.
related: ["[[index]]"]
---

# obsidian markdown interface

## Decided: folder/file layout and filenames

The first Markdown interface is a deterministic projection of WorldState. Each entity receives one note at `<kind>/<Title> (<hex>).md`, where kind is the entity-ID prefix and hex is its 12-hex digest. Titles come from the non-empty string `attributes["name"]`, otherwise `Unnamed <kind>`. Titles are NFC-normalised, sanitised, whitespace-collapsed, bounded to 80 characters, and made safe for Windows device names.

The standard entity-ID form is `kind:12hex`, but projection accepts nonstandard string IDs too. Nonstandard IDs receive a deterministic safe projection ID; references to those IDs are rewritten within the projection. Filenames derive from projection IDs, not canonical identity decisions. The vault is therefore regenerate-only for now: hand-added links into generated notes may break if the identity scheme changes.

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

## Decided: anomaly surfacing

The shared reader classifies `sentinel` and `placeholder-reference` as informational; known anomaly kinds are warnings otherwise, including `lone-surrogate`, which is deliberately a warning because it is prevalent in real exports. The error tier is reserved and currently has no mapped kinds. Unknown kinds default to warnings. Anomalies are surfaced loudly but never fail a run, and the importer continues to write its existing report shapes.

The import record shows a severity summary. When an import report is available, `_worldloom/anomalies.md` provides per-kind and per-pattern counts plus up to five concrete paths for each pattern. The root `index.md` has a banner only when warnings or errors are present; informational-only reports do not add one. The CLI read-stage line reports counts by severity and identifies unrecognised report blocks.

Per-entity import notes remain an open follow-up. The existing exact per-path counts already make that possible without changing the importer report shapes.

## Decided: overwrite safety and determinism

A non-empty directory without a Worldloom marker is never overwritten. With a marker, existing generated files are checked against their recorded hashes; edited files abort the export unless `overwrite_edited=True`. Missing generated files are recreated. Unlisted files are preserved and never overwritten. Generated content is staged before changing the target so a pre-commit write failure leaves the target unchanged.

Exports are deterministic for the same WorldState. The marker fingerprint covers `entities`, `fields`, and `observations`.

## Decided: no interpretation of imported values

The projector reads entities, references, provenance, and observations generically. Imported attribute values are emitted as raw key/value data under the source keys. FMG-specific interpretation is limited to using the `name` attribute for note titles and the explicitly requested FMG metadata vocabulary.

## Decided: link display disambiguation

Wikilink display text is disambiguated generically within each entity kind when multiple entities share a title. A unique title keeps the title as its display. For duplicate titles, Worldloom uses the title of the first single-valued entity reference whose field name comes first alphabetically; list-valued references and mesh references are ignored. If the resulting qualifier is missing or still collides, the entity's 12-hex ID digest is appended. Final display text escapes `|`, `[`, and `]`, and lists are sorted deterministically by title, display, and entity ID.

This rule is generic rather than FMG-specific. In particular, burgs receive their state name as the qualifier because the importer stores a state reference but no province reference; deriving a province from the burg's cell would be an interpretation of FMG fields rather than a generic imported relationship.

## Decided: text fields and group-by indexes

Long or multi-line string attributes are presentation-only text fields: they are summarized under Imported facts and emitted in a fenced Text fields section using their raw value. The fence is chosen to contain the value safely; the raw value is not interpreted as Markdown.

For each entity kind, the attribute names `type` and `group` are treated as categorical purely by name when at least one entity has a string value. Group-by indexes contain one section per distinct raw string value, plus a final `(none)` section for entities without a string value. Values are not interpreted or renamed. The indexes are deterministic projections and are linked from both the per-kind index and the root index.

This decision is presentation-only. It does not define canonical semantics for `type` or `group`, and it does not adopt per-kind templates.

## Open design questions

This decision does **not** yet fix:

- how an edited Markdown note becomes an explicit canonical mutation;
- how uncertainty and unresolved information are represented;
- which Atlas-VTT extensions, if any, should receive first-class support;
- whether per-kind templates should exist;
- per-kind disambiguators (for example, province for burgs).


## Decided: tolerant Markdown projection

**Principle:** Worldloom accepts imperfect input at its boundaries, processes what it can, preserves what it cannot interpret, and records every deviation as a visible classified anomaly. Output stays deterministic, valid and safe. It aborts only to protect data or the filesystem.

The projection prepares a separate view and does not mutate canonical `WorldState`. Valid, JSON-safe worlds retain byte-identical generated files. Lone surrogates are replaced by U+FFFD; references are sanitized and remapped to projected IDs where needed. Nonstandard string IDs are projected to a safe kind plus a deterministic 12-hex digest. Non-string entity IDs, IDs that collide after sanitization, and projected-path collisions abort.

JSON-safe values are preserved as-is, including tuples and integer-keyed mappings that already serialize. Sets/frozensets become sorted lists, bytes become `bytes:<hex>`, and `Address` values become canonical strings. Unsupported objects and non-finite floats become stable type/number placeholders. Key collisions after sanitization or conversion retain both entries using the smallest available ` (duplicate N)` suffix. Each conversion or fallback is recorded with a positional source path.

Projection anomaly kinds: `info` — `coerced-value`; `warning` — `lone-surrogate`, `nonstandard-id`, `nonserialisable-value`, `key-collision`, `nonstandard-entity-shape`, and `fingerprint-fallback`. Unknown kinds default to warning.

Projection anomalies merge into the existing report reader surface under `projection`. The import note and anomaly note show counts and paths; the root index banner appears for warning/error counts; the CLI write-stage line reports a positive projection-anomaly total. Importer behavior and report shapes do not change. Other than the cases above, the exporter aborts only for projected path collisions and managed-vault/filesystem safety refusals. Raw fingerprint failure falls back to the prepared view and is itself reported.
