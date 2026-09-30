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

## 7. GIS and external-tool interoperability

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
