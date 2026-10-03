---
type: architecture
status: normative
summary: Normative Obsidian/Atlas semantic-boundary statements retained verbatim from ARCHITECTURE §15.
related: ["[[architecture/index]]", "[[vision/obsidian-atlas-vtt]]"]
---

# Obsidian-compatible Markdown interface

Atlas-specific scene or asset formats should not become canonical Worldloom state merely because Atlas can consume them.

The core semantic boundary remains important: Worldloom owns the meaning and authority of the simulated world; Markdown is a human-facing representation of that state. A future mutation workflow may interpret edits to Markdown as requests to change canonical state, but the file itself does not automatically become an independent authority for world facts.
