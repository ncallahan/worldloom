---
type: process
status: process
summary: Migration log and source-to-destination traceability.
related: ["[[process/wiki-conventions]]"]
---

# Migration log

## Phase 2 owner decisions

### ARCHITECTURE §14

1. “Worldloom is intended to support multiple clients over the same canonical world rather than separate world representations.” → vision/future-interface-boundary.md
2. “Long-term clients may include: a generated world-guide/wiki; interactive GIS; natural-language query and controlled world editing; historical timeline exploration; character/observer perspectives; GM/referee tools; author research tools; consistency and continuity inspection; scenario/counterfactual exploration; visual observation; eventually, a 3D client.” → vision/future-interface-boundary.md
3. “These are future interface directions, not current implementation requirements.” → vision/future-interface-boundary.md
4. “The architectural consequence is that the core should remain capable of exposing a coherent world at a specified simulation time and scope, tracing provenance, distinguishing canonical reality from derived projections and observer knowledge, and making mutations or branch simulations explicit.” → vision/future-interface-boundary.md
5. “A user-facing interface should be treated as a projection or control surface over Worldloom state.” → architecture/future-interface-boundary.md
6. “It should not become an alternative authority for world facts.” → architecture/future-interface-boundary.md
7. “The eventual 3D environment is intentionally secondary to the primary storytelling goals: maintaining a consistent world for TTRPGs and fiction, and making that world inspectable and usable by authors and game masters.” → vision/future-interface-boundary.md

### ARCHITECTURE §15

1. “The first concrete user-facing interface for Worldloom is an Obsidian-compatible Markdown world vault.” → vision/obsidian-atlas-vtt.md
2. “This is an architectural boundary, not merely an export format: the vault is the first human-facing projection of the simulated world and should be useful directly in Obsidian.” → vision/obsidian-atlas-vtt.md
3. “The Markdown representation should remain human-readable and navigable while carrying enough structured metadata and links for Worldloom to maintain a meaningful connection between notes and world entities, places, events, and relationships.” → vision/obsidian-atlas-vtt.md
4. “The detailed note schema, metadata vocabulary, folder conventions, and mutation semantics remain to be designed separately.” → vision/obsidian-atlas-vtt.md
5. “Atlas-VTT is a compatibility target rather than a Worldloom core dependency.” → vision/obsidian-atlas-vtt.md
6. “Where Atlas-VTT conventions provide useful interoperability without distorting Worldloom semantics, Worldloom should support them through the Markdown/interface boundary.” → vision/obsidian-atlas-vtt.md
7. “Atlas-specific scene or asset formats should not become canonical Worldloom state merely because Atlas can consume them.” → architecture/obsidian-markdown-interface.md
8. “The core semantic boundary remains important: Worldloom owns the meaning and authority of the simulated world; Markdown is a human-facing representation of that state.” → architecture/obsidian-markdown-interface.md
9. “A future mutation workflow may interpret edits to Markdown as requests to change canonical state, but the file itself does not automatically become an independent authority for world facts.” → architecture/obsidian-markdown-interface.md
10. “This establishes a concrete first interface while preserving the broader architectural principle that other clients, including GIS, natural-language interfaces, timelines, observer views, and future visual clients, consume the same underlying world rather than maintaining competing world models.” → vision/obsidian-atlas-vtt.md

The intended relationship code block in §15 is descriptive material and is retained in vision/obsidian-atlas-vtt.md.

## Other owner decisions

- ARCHITECTURE §11 remains verbatim at architecture/prototype-path.md with status: process.
- CAMPAIGN §10 and §11 remain unadopted proposals in vision/gm-campaign-continuity.md.
- entity-id-digest-length, entity-alias-uniqueness, address-unicode-normalisation, and identifier-address-model are consolidated into questions/identifier-address-model.md, with one section per original question.
- The question-note count changes from 39 planned notes to 36 after this consolidation.
- Frontmatter wikilinks in migrated pages are quoted.


## Phase 4 final retirement

The legacy documentation migration is now complete and the retired source documents were removed from the repository: `docs/ARCHITECTURE.md`, `docs/SPECIFICATION.md`, `docs/DEVELOPMENT.md`, `docs/EXPERIMENTS.md`, `docs/GLOSSARY.md`, `docs/INTERFACES.md`, `docs/REFERENCE_BACKLOG.md`, `docs/ROADMAP.md`, `docs/COPILOT_CONTEXT.md`, `docs/CAMPAIGN DIRECTION.md`, and root `TODO.md`. The temporary `devwiki/migration-map.md` was also retired.

Verified before retirement: Phase 3 coverage, verbatim-content, link, frontmatter, and size/context checks; the heading-level coverage check found no unmapped legacy headings; the repository source/test/workflow path scan found no legacy documentation references; `AGENTS.md` remains within the 60-line limit; and `.github/copilot-instructions.md` is a one-line pointer to `AGENTS.md`. The final CI run on this Phase 4 head is still pending at the time of this entry.

Not verified here: the exact local commands `python -m pytest -q tests/unit` and `python -m pytest -q tests/experiments` were not run locally; verification is via the corresponding GitHub Actions jobs.