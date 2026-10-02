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

The existing terrain → water/hydrology → settlement suitability → settlement resolution vertical slice remains an architectural baseline. The newly selected first MVP is a separate risk-reducing demonstration built around a real external world representation.

### First MVP: FMG import → progressive detail → world vault

The first MVP target is:

    FMG full JSON
          ↓
    one-time pinned import
          ↓
    Worldloom canonical state
          ↓
    stable on-demand detail
          ↓
    provenance / "why?"
          ↓
    read-only Obsidian-compatible Markdown vault
          +
    raster export

The MVP is deliberately limited. It is intended to test progressive resolution, address-derived identity, keyed randomness, provenance, persistence, non-grid spatial representation, and useful campaign-planning output. It is not expected to demonstrate the eventual aims of Worldloom.

The implementation sequence is:

1. Finish the identity work currently under the open identity experiment.
2. Implement producer ownership only to the policy-enum and exclusive-producer-validation level; defer runtime guard, REFINES, and overlay storage until the second release's canon-edit workflow.
3. Run the non-grid spatial experiment against a real FMG fixture, including cells/adjacency, burg points, river/route polylines, state polygons, and explicit coordinate-transform objects.
4. Add minimal versioned world save/load.
5. Import FMG full JSON into canonical state with source-hash and FMG-version provenance.
6. Render a read-only Obsidian-compatible Markdown vault using an owner-reviewed minimal schema.
7. Generate one stable lower-resolution detail layer and persist it.
8. Add pinned-input provenance and "why is this here?" notes.
9. Treat canonical edits, overlays, runtime enforcement, and continuity checking as second-release work.

The MVP is a demonstration of feasibility and architectural risk reduction, not a commitment to FMG as the eventual world-generation source.

### Broader progression

The broader progression remains:

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

A later validation target may use a more authored, constrained setting to test continuity and canon layering.

## 7. GIS and external-tool interoperability

GIS remains an important integration target because it provides a concrete test of the adapter philosophy.

For the FMG MVP:

- keep the existing GeoTIFF export working;
- treat raster export as the immediate tangible GIS output;
- investigate GeoJSON as the likely future primary GIS export;
- defer GIS re-import to later work, where it can also serve as a proof of concept for reading Worldloom-compatible data back from GIS tooling.

The exact GIS stack and interchange formats remain experiment-driven rather than fixed by the MVP.

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

## 10. Agent-assisted development

AI coding agents are expected to contribute substantially to implementation.

They should be treated as implementation collaborators operating under the project's architecture, not as independent sources of project requirements.

Agents should:

- read the architecture and roadmap before structural changes;
- reuse existing systems where possible;
- define and test contracts;
- add tests with code changes;
- preserve reproducibility;
- document significant architectural decisions;
- surface conflicts or uncertainty rather than silently deciding them;
- treat open questions as questions to be experimentally resolved, not invitations to invent architecture.

## 11. Success criterion

The long-term success of Worldloom is not measured by how much domain functionality exists inside its own source tree.

It is measured by whether a collection of independently developed specialist models and tools can be composed into a coherent, persistent, inspectable world simulation without each system needing bespoke knowledge of every other system, while allowing the world to become more detailed as it is explored.


## 12. Future world interfaces

The eventual world should be usable through multiple clients over the same canonical state.

The primary long-term storytelling interface is expected to be a world-guide/wiki-like system, complemented by interactive GIS and a natural-language query/edit interface. Other useful clients include historical timelines, character/observer views, GM/referee dashboards, traveller/gazetteer views, author research tools, continuity inspectors, counterfactual explorers, and visual "god's-eye" observation.

A 3D/CRPG-like client is an aspirational possibility rather than the primary goal. If eventually built, it should consume the same Worldloom state rather than becoming a separate simulation.

These directions imply that the core should preserve stable identity, temporal and spatial scope, provenance, event history, uncertainty/resolution semantics, reproducible snapshots, and queryable relationships. They do not imply that any UI technology should be selected now.

The interface vision is documented separately in docs/INTERFACES.md. It is background for architectural decisions, not a near-term implementation backlog.

## 13. First concrete interface: Obsidian-compatible Markdown

The first user-facing Worldloom interface is deliberately scoped as an **Obsidian-compatible Markdown world vault**.

The FMG MVP is the first concrete vehicle for exercising this interface. The first vault is read-only and regenerable from the authoritative Worldloom world file. It is intended to be useful campaign-planning material while remaining an ordinary Markdown projection rather than a second canonical database.

The initial MVP renderer should preserve:

- human-readable Markdown;
- Obsidian-compatible links and navigation;
- structured metadata where machine-readable semantics are needed;
- explicit distinction between canonical facts, derived/generated descriptions, uncertainty, and in-world knowledge;
- provenance sufficient to explain where generated facts came from;
- compatibility with spatial and map-oriented tooling where practical.

The exact note schema, metadata vocabulary, folder structure, identifier presentation, and Markdown mutation semantics remain deliberately open and require owner review.

### Atlas-VTT compatibility

Atlas-VTT remains a compatibility target, not a Worldloom dependency. The preferred direction is:

    Worldloom
        |
        v
    Obsidian-compatible Markdown
        |
        +---- Obsidian
        +---- Atlas-VTT
        +---- future clients

The Markdown interface is the first implementation target. GIS, natural-language, timeline, observer, GM, author, continuity, scenario, and visual interfaces remain later clients of the same world state.

### Longer-term validation direction

A later directional validation target is a Stormlight/Roshar campaign constrained by published book canon. This is not current implementation work. If pursued, it should test authored-canon layering, observer knowledge, and continuity checking without turning copyrighted source text into repository data.
