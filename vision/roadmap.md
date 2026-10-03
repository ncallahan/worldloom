---
type: vision
status: vision
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# roadmap

# Worldloom Long-Term Roadmap

## Purpose

This document captures the long-term direction so that implementation agents, including GitHub Copilot, can make local changes without losing sight of the larger project.

The roadmap is deliberately **directional rather than a rigid implementation schedule**. The architecture should be validated by progressively more realistic examples, and decisions may change when evidence warrants it.

The roadmap prioritises **risk-reducing demonstrations** over building a miniature version of the eventual system. The next experiment should be chosen because it resolves an important architectural or feasibility question.

## 1. Core objective

Build a modular platform capable of constructing, simulating, and exploring a persistent computational world by composing specialised systems.

The central problem is not to write one enormous world simulator. It is to make independently useful models and tools interoperable while preserving a coherent shared world, history, uncertainty, and provenance.

Worldloom should ultimately make it possible to obtain a useful broad world quickly and then progressively resolve more detail as the world is explored, edited, or simulated.

Conceptually:

    specialist systems
          ↓
       adapters
          ↓
    broad/provisional world
          ↓
    progressive resolution
          ↓
    canonical world state
          ↓
      orchestration
          ↓
    persistent world history

## 2. Domains to support

The eventual ecosystem may include:

- geography and GIS
- terrain and landforms
- hydrology and watersheds
- weather and climate
- ecology/environment
- population and demographics
- settlements and infrastructure
- transport
- agriculture and resources
- economy and trade
- politics and institutions
- language
- culture and social structure
- conflict and cooperation
- technology
- history and events
- visualisation and analysis

These are **candidate domains**, not requirements that all be implemented internally.

## 3. Integration-first philosophy

Worldloom should reuse established software wherever practical.

Potential integrations may include GIS, numerical/scientific libraries, climate/weather models, demographic models, optimisation systems, databases, visualisation tools, and external simulators.

The preferred pattern is:

    existing specialist system
              ↕
        Worldloom adapter
              ↕
    provisional or canonical state

The value Worldloom adds is interoperability, persistent state, scheduling, progressive resolution, provenance, and a common experimental framework.

## 4. Canonical world model

The core representation should eventually support:

- persistent entities with stable identity
- spatial fields and spatially located entities
- relationships
- constraints
- events and event consequences
- statistical/distributional and provisional information
- resolution of uncertain/provisional state into persistent facts
- provenance and dependency history
- versioned snapshots/checkpoints

The exact storage technology and representation of unresolved state should be selected only after the requirements are demonstrated by experiments.

## 5. Multi-scale simulation

The world contains processes with very different natural scales.

Examples include:

- weather: minutes
- rivers/hydrology: hours to days
- economy: days to months
- population: months to years
- politics: days to years
- culture: decades
- geography: centuries to millennia

The scheduler should therefore be event- and dependency-aware rather than imposing a single global timestep on every subsystem.

Progressive resolution adds another scale dimension: spatial or historical detail need not be generated everywhere at once.

## 6. Feasibility-driven prototype progression

The immediate prototype is now a deliberately narrow, useful FMG-based vertical slice. It is a risk-reducing demonstration rather than a miniature of the eventual system.

### First MVP: FMG import to campaign-planning vault

The selected first MVP is:

    FMG full JSON export
          ↓
    snapshot import
          ↓
    explicit source → internal coordinate transform
          ↓
    Worldloom canonical state
          ↓
    stable on-demand local detail
          ↓
    pinned provenance / “why?”
          ↓
    read-only Obsidian-compatible Markdown vault
          +
    raster export

The MVP is intended to be genuinely useful campaign-planning output while testing:

- progressive resolution;
- address-derived identity;
- keyed deterministic randomness;
- source-file/version provenance;
- persistence and regeneration;
- non-grid spatial representation;
- a concrete projection over canonical state.

The MVP does **not** demonstrate the eventual breadth of Worldloom.

### Selected implementation sequence

1. Finish identity work, including the remaining address-derived entity-ID and order-independence work.
2. Producer ownership: implement only the policy enum and exclusive-producer validation. Defer runtime guards, `REFINES`, and overlay storage until the canon-edit workflow.
3. Run the non-grid spatial experiment on a real FMG fixture: cells and adjacency, burg points, river/route polylines, state polygons, and explicit coordinate-transform objects.
4. Implement minimal versioned JSON world save/load.
5. Implement the one-time FMG full-JSON importer with source-hash and FMG-version provenance.
6. Implement the read-only Obsidian-compatible Markdown vault renderer. The note schema and metadata vocabulary are an explicit design step, not an assumed contract.
7. Implement one level of stable on-demand burg-level detail and persist it.
8. Add pinned-input provenance and “why?” explanations to notes.
9. Treat canon-edit workflow, overlays, runtime producer guards, and continuity checking as the second release.

The sequence is intentionally arranged so that spatial representation and persistence are exercised before the importer and renderer become large implementations.

### Longer-term validation

After the MVP, validation should broaden toward increasingly realistic composition, editing, provenance, and continuity scenarios.

A later directional validation target is a Roshar/Stormlight campaign constrained by book canon. This is not current implementation work. It is intended to test authored-canon layering, observer knowledge, and continuity checking after those capabilities exist.

Copyright-sensitive source material should be represented as extracted facts with citations rather than copied passages, and imported canon data should not be placed in a public repository without checking applicable licence/permission terms.

## 7. GIS and external-tool interoperability

GIS remains an important integration and inspection target.

The MVP keeps the existing GeoTIFF export working and uses raster export as a concrete output. The longer-term direction is now likely to make **GeoJSON the primary GIS export**, with GeoTIFF retained where raster output is useful. This is a future direction, not a current format replacement.

FMG GeoJSON import is not part of the MVP. A later GeoJSON reader may serve as a proof of concept for reading data back from GIS tools.

Worldloom should exchange canonical spatial data with established GIS tooling such as QGIS rather than recreating a GIS engine. The exact GIS stack and data formats should be decided during implementation based on the smallest useful integration.

## 8. Progressive generation experiments

The project should explicitly test the central progressive-world hypothesis.

The first concrete experiments are:

1. represent non-grid FMG spatial structures without prematurely fixing a universal spatial model;
2. verify source/internal/target coordinate transform round trips;
3. establish minimal world save/load semantics, including JSON encoding of tuple keys, tuple locations, and sets;
4. verify that on-demand details remain stable across save/load and repeated import of the same pinned FMG input;
5. retain enough provenance to explain why generated details exist.

Later experiments should investigate:

- whether a useful broad projection can be generated cheaply;
- whether selected regions/entities can be resolved without resolving unrelated regions/entities;
- how dependencies between unresolved and resolved information should be represented;
- how explicit world edits affect provisional and already-resolved information;
- how much global coherence must be guaranteed by the broad projection.

These experiments should remain evidence, not silent architectural commitments.

## 9. Experiments and validation

Each significant modelling experiment should record:

- question/purpose
- implementation/version
- configuration
- random seed(s)
- software/environment versions
- execution parameters
- measurements
- outputs
- interpretation

Raw results should remain distinguishable from interpretation.

The project should gradually add architectural validation, integration tests, reproducibility tests, performance tests, and domain-model tests as the system grows.

## 11. Success criterion

The long-term success of Worldloom is not measured by how much domain functionality exists inside its own source tree.

It is measured by whether a collection of independently developed specialist models and tools can be composed into a coherent, persistent, inspectable world simulation without each system needing bespoke knowledge of every other system, while allowing the world to become more detailed as it is explored.

## 13. First concrete interface: Obsidian-compatible Markdown

The first user-facing Worldloom interface is deliberately scoped as an **Obsidian-compatible Markdown world vault**.

The first implementation is read-only. The vault is a regenerable projection over the authoritative Worldloom world file, not a second canonical database. Mutation of canonical state from Markdown is deferred to the second release.

The MVP should provide campaign-planning material while remaining ordinary Markdown that a user can inspect in Obsidian and compatible clients such as Atlas-VTT. The initial renderer should expose the entities and relationships supported by the imported FMG snapshot and the first level of generated detail, without pretending that the eventual note schema is settled.

The exact note schema, metadata vocabulary, folder structure, identifier conventions, and Markdown mutation semantics remain open design questions. In particular, identifier decisions must remain separate from validation decisions.

The preferred dependency direction remains:

    Worldloom
        |
        v
    Obsidian-compatible Markdown
        |
        +---- Obsidian
        +---- Atlas-VTT
        +---- future clients

GIS, natural-language, timeline, observer, GM, author, continuity, scenario, and visual interfaces remain later clients of the same world state.
