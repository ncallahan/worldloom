---
type: process
status: process
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# Agent Rules

## AI-assisted development

AI agents may implement requested changes, but they are not architectural authorities. They must not invent requirements, silently broaden scope, hide failed experiments, or claim unexecuted tests as evidence. The repository architecture, specification, and tests remain the authoritative boundaries for implementation.

# Copilot Context: Worldloom Big Picture

Use this document as a compact orientation when working on Worldloom. It is intended to prevent short-term implementation work from accidentally narrowing the long-term design.

## Working rule for agents

Before making structural changes:

1. Read `devwiki/architecture/index.md` and the relevant architecture pages.
2. Read `devwiki/vision/roadmap.md`.
3. Read `devwiki/vision/interfaces.md` when the change could affect world representation, queries, projections, or future clients.
4. Check `devwiki/current.md` for the active task.
5. Prefer the smallest experiment or implementation that resolves the current question.
6. Surface architectural choices that affect the general shape of data or interfaces before committing to them.
7. Keep validation/identifier-scheme questions separate when they are not part of the current task.
8. Do not turn future interface aspirations into present implementation requirements without an explicit task.
9. Work on feature branches and leave merging for human review unless explicitly instructed otherwise.

The purpose of this context is continuity: local implementation should advance the current task while preserving the possibility of the larger system described above.

## Architectural principles

## Development discipline

- Make the smallest change that satisfies the requirement.
- Prefer explicit interfaces over implicit coupling.
- Update documentation when architecture or contracts change.
- Avoid premature generalisation.
- Do not silently change the project's long-term direction to make a local implementation easier.
- If a requirement conflicts with the architecture, surface the conflict rather than inventing a workaround.
- Work on feature branches. Do not merge a pull request unless explicitly asked to do so.
- Before modifying a general data contract, explain the architectural options and trade-offs first.
- Keep validation and identifier-scheme decisions explicitly separate unless the current task requires them.
