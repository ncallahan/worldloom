---
type: question
status: open
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# obsidian markdown interface

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
