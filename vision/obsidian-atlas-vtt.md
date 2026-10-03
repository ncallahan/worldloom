---
type: vision
status: vision
summary: Descriptive Obsidian/Atlas interface direction retained verbatim from ARCHITECTURE §15.
related: ["[[architecture/obsidian-markdown-interface]]", "[[vision/interfaces]]"]
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
