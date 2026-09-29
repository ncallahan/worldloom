# Worldloom Long-Term Roadmap

## Purpose

This document captures the long-term direction so that implementation agents, including GitHub Copilot, can make local changes without losing sight of the larger project.

The roadmap is deliberately **directional rather than a rigid implementation schedule**. The architecture should be validated by progressively more realistic examples, and decisions may change when evidence warrants it.

## 1. Core objective

Build a modular platform capable of constructing, simulating, and exploring a persistent computational world by composing specialised systems.

The central problem is not to write one enormous world simulator. It is to make independently useful models and tools interoperable while preserving a coherent shared world, history, uncertainty, and provenance.

Conceptually:

    specialist systems
          ↓
       adapters
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
       canonical state

The value Worldloom adds is interoperability, persistent state, scheduling, provenance, and a common experimental framework.

## 4. Canonical world model

The core representation should eventually support:

- persistent entities with stable identity
- spatial fields and spatially located entities
- relationships
- constraints
- events and event consequences
- statistical/distributional state
- resolution of uncertain state into persistent facts
- provenance and dependency history
- versioned snapshots/checkpoints

The exact storage technology should be selected only after the requirements are demonstrated by prototypes.

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

## 6. Prototype progression

Before building elaborate domain models, demonstrate the architecture with a small end-to-end world.

A useful first chain is:

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
       ↓
    changed world state

The first prototype should prove that:

1. modules can declare contracts;
2. state can move through canonical interfaces;
3. modules can operate at different resolutions;
4. uncertainty can become persistent fact;
5. events can change subsequent state;
6. provenance can explain derived facts;
7. an external specialist system can be used through an adapter;
8. the entire run can be reproduced from recorded configuration/seed.

The prototype should remain deliberately simple. Its purpose is to validate the architecture, not to produce a sophisticated simulated world.

## 7. GIS and external-tool interoperability

GIS is an important early integration target because it provides a concrete test of the adapter philosophy.

Worldloom should be able to exchange canonical spatial data with established GIS tooling such as QGIS rather than recreating a GIS engine.

The exact GIS stack and data formats should be decided during implementation based on the smallest useful integration.

## 8. Experiments and validation

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

## 9. Agent-assisted development

AI coding agents are expected to contribute substantially to implementation.

They should be treated as implementation collaborators operating under the project's architecture, not as independent sources of project requirements.

Agents should:

- read the architecture and roadmap before structural changes;
- reuse existing systems where possible;
- define and test contracts;
- add tests with code changes;
- preserve reproducibility;
- document significant architectural decisions;
- surface conflicts or uncertainty rather than silently deciding them.

## 10. Success criterion

The long-term success of Worldloom is not measured by how much domain functionality exists inside its own source tree.

It is measured by whether a collection of independently developed specialist models and tools can be composed into a coherent, persistent, inspectable world simulation without each system needing bespoke knowledge of every other system.
