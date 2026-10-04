---
type: vision
status: vision
summary: Descriptive Obsidian/Atlas interface direction retained verbatim from ARCHITECTURE §15.
related: ["[[devwiki/architecture/obsidian-markdown-interface]]", "[[devwiki/vision/interfaces]]"]
---

# Obsidian-compatible Markdown as the first interface



The first concrete user-facing interface for Worldloom is an **Obsidian-compatible Markdown world vault**. This is an architectural boundary, not merely an export format: the vault is the first human-facing projection of the simulated world and should be useful directly in Obsidian.

The Markdown representation should remain human-readable and navigable while carrying enough structured metadata and links for Worldloom to maintain a meaningful connection between notes and world entities, places, events, and relationships. The detailed note schema, metadata vocabulary, folder conventions, and mutation semantics remain to be designed separately.

The intended relationship is:

    canonical Worldloom state
              |
              v
    Obsidian-compatible Markdown vault
              |
       +------+------+
       |             |
    Obsidian      Atlas-VTT

Atlas-VTT is a compatibility target rather than a Worldloom core dependency. Where Atlas-VTT conventions provide useful interoperability without distorting Worldloom semantics, Worldloom should support them through the Markdown/interface boundary. Atlas-specific scene or asset formats should not become canonical Worldloom state merely because Atlas can consume them.

The core semantic boundary remains important: Worldloom owns the meaning and authority of the simulated world; Markdown is a human-facing representation of that state. A future mutation workflow may interpret edits to Markdown as requests to change canonical state, but the file itself does not automatically become an independent authority for world facts.

This establishes a concrete first interface while preserving the broader architectural principle that other clients, including GIS, natural-language interfaces, timelines, observer views, and future visual clients, consume the same underlying world rather than maintaining competing world models.

## 6. First concrete interface: Obsidian-compatible Markdown

The first interface selected for implementation is an **Obsidian-compatible Markdown world vault**.

This turns the previously abstract world-guide/wiki direction into a concrete, low-coupling target. A Worldloom vault should be usable as an ordinary Obsidian vault: notes should remain readable and navigable as Markdown, while structured metadata and links provide machine-readable connections back to the simulated world.

The intended architecture is:

    Worldloom canonical state
             |
             v
    Markdown world vault
             |
       +-----+-----+
       |           |
    Obsidian    Atlas-VTT

### What this means

The vault is the **first human-facing projection of Worldloom**, not a second canonical database. Worldloom remains authoritative for simulated reality. Markdown files represent that reality and may eventually provide controlled inputs back into Worldloom through an explicit mutation workflow.

The first interface should be capable of representing at least:

- places and regions;
- settlements and infrastructure;
- people and populations;
- political entities and institutions;
- cultures and languages;
- religions and organisations;
- natural features;
- economic activity and trade;
- historical events;
- relationships and dependencies;
- current conditions.

The representation should preserve the distinction between simulated reality and information about that reality. In particular, a note may eventually contain or link to canonical facts, derived descriptions, unresolved/uncertain information, provenance, and in-world beliefs or rumours. These must not become semantically interchangeable merely because they appear in the same Markdown file.

### Atlas-VTT compatibility

Atlas-VTT is a compatibility target for this interface, not a Worldloom dependency. Its Obsidian-native workflow and ability to associate Markdown notes with map locations make it a natural first consumer of Worldloom's world vault.

Compatibility should be pursued where it follows naturally from the Markdown contract. Worldloom should not make Atlas-specific scene formats, asset stores, or implementation details part of canonical world state merely to obtain compatibility.

### Open design questions

This decision does **not** yet fix:

- the folder/file layout;
- the exact frontmatter/property vocabulary;
- the identifier scheme;
- how entity identity maps to filenames and links;
- how generated content is marked;
- how provenance is represented in notes;
- how uncertainty and unresolved information are represented;
- how an edited Markdown note becomes an explicit canonical mutation;
- which Atlas-VTT extensions, if any, should receive first-class support.

Those are separate design questions. The immediate architectural commitment is to make ordinary Obsidian-compatible Markdown the first concrete interface and to preserve Atlas-VTT compatibility where it does not compromise Worldloom's independent semantics.
