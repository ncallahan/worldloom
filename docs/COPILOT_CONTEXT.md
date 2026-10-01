# Copilot Context: Worldloom Big Picture

Use this document as a compact orientation when working on Worldloom. It is intended to prevent short-term implementation work from accidentally narrowing the long-term design.

## Mission

Worldloom is a modular framework for constructing, simulating, and exploring a persistent computational world for storytelling, especially TTRPGs and fiction.

The primary goal is **not** to build a game. The simulation is the source of truth; interfaces are clients/projections over that world.

The long-term user experience may include:

- a generated world-guide/wiki;
- interactive GIS maps;
- a natural-language world query/edit interface;
- historical timelines;
- character/observer perspectives;
- GM/referee tools;
- author research tools;
- consistency/continuity inspection;
- scenario/counterfactual exploration;
- visual "god's-eye" observation;
- eventually, perhaps, a 3D CRPG-like client.

The 3D client is an aspirational possibility, not a current requirement.

## Architectural consequence

Do not build the core around any one interface.

Prefer a canonical world representation with:

- persistent entities and identity;
- fields;
- events/history;
- relationships and constraints;
- uncertainty/statistical/provisional information;
- provenance;
- spatial and temporal semantics;
- reproducible snapshots/checkpoints.

Derived observations, projections, visualisations, and observer knowledge must remain distinguishable from canonical world state.

A future wiki, GIS, chatbot, GM interface, or 3D client should be able to query the same world rather than maintaining a second competing representation.

## Progressive world generation

A central Worldloom idea is:

> Generate broadly; resolve deeply where needed.

A world may first have a useful broad statistical/coarse representation. Exploration, editing, simulation, or module dependencies can request local resolution. Once a result is explicitly resolved into canonical state, it becomes part of the world's history and should not be silently regenerated.

The exact representation of provisional information remains an experiment-driven open question.

## Integration philosophy

Worldloom is the loom, not every thread.

Prefer established specialist systems behind adapters rather than reimplementing GIS, terrain, hydrology, agent-based modelling, language processing, etc. inside Worldloom when an appropriate external system exists.

The repository's research/reference backlog contains systems such as GPlates, GRASS GIS, WhiteboxTools, Landlab, Mesa, GAMA, Neighborly, Canwu, WorldForge, WorldGen/Worldsmith, and others. These are references to investigate, not committed dependencies.

## Storytelling perspective

The eventual system should support both:

- what is actually true in the simulated world; and
- what a particular person, society, traveller, GM, or author could know about it.

An LLM may provide a natural interface to the world, but it should be grounded in canonical state, provenance, and explicit world operations rather than becoming an independent source of canon.

## Working rule for agents

Before making structural changes:

1. Read `docs/ARCHITECTURE.md`.
2. Read `docs/SPECIFICATION.md`.
3. Read `docs/ROADMAP.md`.
4. Read `docs/INTERFACES.md` when the change could affect world representation, queries, projections, or future clients.
5. Check `TODO.md` for the active task.
6. Prefer the smallest experiment or implementation that resolves the current question.
7. Surface architectural choices that affect the general shape of data or interfaces before committing to them.
8. Keep validation/identifier-scheme questions separate when they are not part of the current task.
9. Do not turn future interface aspirations into present implementation requirements without an explicit task.
10. Work on feature branches and leave merging for human review unless explicitly instructed otherwise.

The purpose of this context is continuity: local implementation should advance the current task while preserving the possibility of the larger system described above.

## First concrete user interface

Worldloom's first concrete user-facing interface is an **Obsidian-compatible Markdown world vault**.

Treat this as an architectural boundary, not as permission to make Obsidian the simulation engine. Worldloom remains the source of truth; Markdown is the first human-facing projection of that state. Keep the representation human-readable and navigable in ordinary Obsidian while allowing structured metadata and links to carry Worldloom semantics.

Atlas-VTT is a compatibility target because it is Obsidian-native and can associate Markdown notes with map locations. Do not make Atlas-VTT a core dependency or make Atlas-specific scene or asset formats canonical Worldloom state. Prefer compatibility through the Markdown boundary.

Do not prematurely decide the Markdown folder layout, metadata vocabulary, identifier scheme, validation scheme, provenance syntax, uncertainty representation, or Markdown-to-canonical mutation semantics. Those are design questions to be surfaced and resolved separately.
