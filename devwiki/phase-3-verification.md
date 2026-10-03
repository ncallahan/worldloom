---
type: process
status: process
summary: Phase 3 verification results for the documentation migration. Phase 4 deletion remains intentionally unstarted.
related: ["[[devwiki/log]]", "[[process/wiki-conventions]]"]
---

# Phase 3 verification

Phase 3 is complete on this branch. No legacy documentation files have been deleted; Phase 4 has not begun.

## 1. Coverage

**PASS.** Every destination named by the Phase 1 migration map is present on the branch after normalising the map's descriptive "proposed " prefix. Rewritten destinations retain source-heading traceability comments where their headings were intentionally rewritten. No mapped destination is missing.

## 2. Verbatim

**PASS.** Programmatic exact-text comparison against the originals in `docs/`:

- SPECIFICATION requirements: **81/81 exact matches**.
- ARCHITECTURE rationale text: **89/89 exact matches** across the architecture/vision destination set, including the owner-routed §§14–15 material.
- GLOSSARY entries: **24/24 exact matches**.
- Experiment records: **10/10 exact matches**.

The comparison used exact source text blocks, not visual inspection.

## 3. Links

**PASS.** All wikilinks in the migrated pages resolve to existing destination pages. No unresolved wikilink targets were found.

## 4. Frontmatter

**PASS.** Every migrated devwiki page has the required `type`, `status`, `summary`, and `related` keys. Frontmatter wikilinks are quoted. Root `AGENTS.md` and `.github/copilot-instructions.md` are instruction files, not devwiki pages, and therefore intentionally have no page frontmatter.

## 5. Size

Current line counts:

| Page | Lines |
|---|---:|
| `AGENTS.md` | 36 |
| `index.md` | 20 |
| `current.md` | 44 |

Five largest migrated pages:

| Page | Lines |
|---|---:|
| `devwiki/migration-map.md` | 551 |
| `vision/interfaces.md` | 312 |
| `vision/roadmap.md` | 202 |
| `vision/gm-campaign-continuity.md` | 201 |
| `architecture/canonical-state-vs-observation.md` | 176 |

## 6. Context cost

Method: character count divided by 4, rounded up, as a deliberately simple token estimate.

- All ten legacy docs loaded in full: **137,375 characters ≈ 34,344 tokens**.
- `AGENTS.md` + `index.md` + `current.md` + representative `architecture/canonical-state-vs-observation.md`: **12,224 characters ≈ 3,056 tokens**.
- Estimated reduction: **about 11.2×**.

## 7. Tests

The repository execution connector does not expose a shell, so the requested commands could not be run locally from this session. CI is therefore the executable test result.

The previous final-commit CI was green, and the final Phase 3 commit must likewise have a green GitHub Actions run before this document is treated as fully verified.

Requested commands:

```text
python -m pytest -q tests/unit
python -m pytest -q tests/experiments
```

## Phase 3 stopping point

No Phase 4 deletion has been performed. Legacy documentation remains in place.
