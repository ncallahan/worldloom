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

The eventual ecosystem may include models or adapters for:

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

The immediate prototype should prove that modules can interact meaningfully, not attempt to reproduce the eventual breadth of Worldloom.

The current vertical slice is:

    terrain
       ↓
    water/hydrology
       ↓
    settlement suitability
       ↓
    settlement resolution
       ↓
    persistent settlement
       ↓
    event

Its purpose is to establish that one module's output can materially constrain the next module's behaviour and that the resulting fact persists.

The broader roadmap is then:

    Can modules interact?
          ↓
    Can outputs form a coherent shared world?
          ↓
    Can provisional information become persistent facts?
          ↓
    Can detail be generated progressively rather than all at once?
          ↓
    Can existing specialist systems participate?
          ↓
    Can the resulting world remain coherent as it is explored and changed?

Each step should be the smallest experiment capable of answering the question.

A later validation target is an FMG-like broad world projection: a quick, visually useful world with plausible large-scale geography and broad systems, followed by selective deeper resolution. This is a target capability, not a current prototype requirement.


### 6.1 FMG import → progressive detail → Obsidian vault MVP

The first selected MVP is a deliberately **risk-reducing demonstration**: import a real Azgaar Fantasy Map Generator (FMG) full JSON export, adopt it as Worldloom canonical state, resolve one stable level of detail below the FMG representation on demand, render a read-only Obsidian-compatible Markdown vault, and produce a raster export.

This target is intended to be genuinely useful for campaign planning while exercising progressive resolution, provenance, and address-derived identity. It is not expected to demonstrate the eventual aims of Worldloom.

The MVP scope is deliberately narrow:

- FMG full JSON only; other FMG export forms are deferred.
- One-time snapshot import; later FMG re-import/update is deferred.
- Source-file hash and FMG version are retained as import provenance.
- Imported FMG values are adopted as canonical state, with their uncertainty/fuzziness semantics still open.
- Coordinate conversion is an explicit import-space → internal-space → target-space pipeline. The internal coordinate system remains open; the interim representation uses FMG map space through an explicit identity transform.
- JSON is the MVP world-file format. The world file is authoritative and the generated vault is regenerable.
- The vault is read-only in the first release.
- Raster output uses a sensible default resolution with a configurable scale factor.
- GeoJSON is a later likely primary GIS export direction; existing GeoTIFF export remains supported.
- One level of stable on-demand detail is generated below FMG resolution using address-derived identity and keyed randomness, with provenance explaining why the detail exists.

The selected development sequence is:

1. finish the current address-derived identity work, including the order-independence experiment;
2. implement producer-ownership policy enum and exclusive-producer validation only; defer the runtime guard, REFINES, and overlay store until the second-release canon-edit workflow;
3. run a non-grid spatial experiment on the real FMG fixture, including cells/adjacency, burg points, river/route geometry, state polygons, and coordinate-transform objects;
4. implement minimal world save/load;
5. implement the FMG importer with source-hash provenance;
6. implement the read-only vault renderer, consulting the owner before fixing its minimal schema;
7. implement persisted on-demand burg detail;
8. add pinned-input provenance and “why?” explanations in notes;
9. second release: canon edits, overlays, the runtime guard, and continuity checking.

The detailed MVP design and fixture observations are recorded in docs/MVP_FMG_VAULT.md.

The MVP does not settle the canonical coordinate system, imported-data uncertainty model, world-file contents, JSON encoding of tuple keys/sets, SQLite use, vault schema, or the final FMG-to-Worldloom identifier mapping. These remain open questions.

Later directional work includes making GeoJSON the primary GIS export, exploring GIS-to-Worldloom re-import, revisiting FMG re-import/update semantics, and using a Roshar/Stormlight campaign constrained by book canon as a longer-term validation target. Any such copyright-constrained validation should store extracted facts with citations rather than passages, keep imported canon data out of public repositories, and check licence terms before sharing.

## 7. GIS and external-tool interoperability

GeoJSON is a later likely primary GIS export direction. This is not current work; the existing GeoTIFF export should remain working while the direction is evaluated.

GIS is an important early integration target because it provides a concrete test of the adapter philosophy.

Worldloom should be able to exchange canonical spatial data with established GIS tooling such as QGIS rather than recreating a GIS engine.

The exact GIS stack and data formats should be decided during implementation based on the smallest useful integration.

## 8. Progressive generation experiments

The project should explicitly test the central progressive-world hypothesis.

Early experiments should investigate:

1. whether a useful broad projection can be generated cheaply;
2. whether selected regions/entities can be resolved without resolving unrelated regions/entities;
3. whether resolved facts remain stable and are reused by later modules;
4. how dependencies between unresolved and resolved information should be represented;
5. how explicit world edits affect provisional and already-resolved information;
6. how much global coherence must be guaranteed by the broad projection.

These experiments should be small and independently measurable.

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
