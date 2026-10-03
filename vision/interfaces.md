---
type: vision
status: vision
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# interfaces

# Worldloom Interface and Interaction Vision

## Status

This document records long-term interface direction and design context. It is **not** a current implementation specification and does not require any of these interfaces to be built now.

The purpose is to ensure that near-term architecture and implementation choices do not accidentally make the eventual ways of using a Worldloom world difficult or incoherent.

## 1. The core idea

Worldloom's simulation is the source of truth. User-facing interfaces should be different projections, views, or control surfaces over the same persistent world state rather than separate representations of the world.

Conceptually:

```
                         canonical world
                       state + history
                              |
          +-------------------+-------------------+
          |                   |                   |
       query              projection            edit
          |                   |                   |
     +----+----+         +----+----+         +----+----+
     |    |    |         |    |    |         |    |    |
    wiki map chat      GIS timeline views   GM author scenario
     |    |    |         |    |    |         |    |    |
     +----+----+         +----+----+         +----+----+
                              |
                         future clients
                              |
                            3D view
```

The important architectural consequence is that a wiki, map, chatbot, GM tool, authoring tool, or eventual 3D environment should not need its own competing world model.

## 2. Primary long-term interfaces

### 2.1 World guide / wiki

A generated or semi-generated world encyclopedia should provide browsable views of:

- places and regions
- settlements and infrastructure
- people and populations
- political entities and institutions
- cultures and languages
- religions and organisations
- natural features
- economic activity and trade
- historical events
- relationships and dependencies
- current conditions

The guide should ideally distinguish simulated facts from in-world beliefs, rumours, incomplete knowledge, and disputed accounts.

### 2.2 Interactive GIS

GIS is both a practical inspection tool and a likely end-user interface.

Useful layers may include:

- terrain and elevation
- rivers and watersheds
- climate and weather
- vegetation and ecology
- agriculture and resources
- population density
- settlements and infrastructure
- roads and transport
- political boundaries
- languages and cultures
- religions
- trade routes
- migration
- historical boundaries and changes

Time should eventually be an explicit map dimension. A user should be able to inspect how geography, settlements, populations, borders, and other spatial systems change through history.

### 2.3 Natural-language world interface

A chatbot or equivalent query interface could provide both world enquiry and controlled world administration.

Examples:

- "Why is this settlement here?"
- "What was happening here 200 years ago?"
- "What languages would a traveller from this region speak?"
- "Show me what this character would know about the war."
- "Establish that the eastern kingdom invades in 843."
- "Run a counterfactual in which the drought lasts another twelve years."

The interface should distinguish querying, proposing/editing canonical state, and running a scenario or experiment. Natural-language output must ultimately be grounded in the canonical world model and its provenance rather than becoming an independent source of facts.

### 2.4 Timeline / historical explorer

A temporal interface should support inspection from very broad periods down to individual events.

It may combine:

- political change
- population and migration
- wars and conflicts
- technological change
- linguistic change
- environmental change
- settlement founding/abandonment
- important individuals
- economic changes

Events should be explorable through their causal and provenance relationships where those relationships are represented by the simulation.

### 2.5 Character / observer perspective

A particularly useful storytelling interface would answer questions from a bounded observer's perspective.

The view may depend on:

- location
- occupation
- culture
- language
- education
- social position
- personal history
- contacts
- witnessed events
- rumours and available information

This should not change canonical reality. It is an information projection over the world state.

### 2.6 GM / referee dashboard

For TTRPG use, a session-oriented view could expose:

- current date and weather
- party location
- nearby entities
- current political and economic conditions
- rumours
- active events
- faction objectives
- travel information
- recent developments
- simulation-generated situations

The system should provide world developments rather than assuming that it is a plot generator.

### 2.7 Gazetteer / traveller view

A deliberately in-world presentation can provide descriptions, approximate populations, notable features, routes, customs, and other information that a traveller could plausibly know.

Different information views can expose different levels of knowledge without changing canonical state.

### 2.8 Author research interface

For fiction and worldbuilding, useful queries include:

- what was happening in a place at a given date;
- what a person could plausibly know or have experienced;
- plausible occupations, journeys, languages, and backgrounds;
- causal explanations for why a place, institution, or population has its current form.

The simulation should provide the factual substrate; an LLM may help present or query it but should not silently invent canon.

### 2.9 Consistency / continuity inspector

Worldloom should eventually be able to inspect the world as a system and identify issues such as:

- incompatible facts;
- implausible or unsupported population/resource relationships;
- entities that violate declared constraints;
- historical inconsistencies;
- provenance gaps;
- results that no longer agree with their dependencies.

Where possible, diagnostics should explain the causal or data path behind the finding rather than simply reporting an error.

### 2.10 Scenario / counterfactual explorer

A user should eventually be able to branch from a known world state and explore alternatives without mutating the canonical world.

For example:

- change a climate event;
- introduce a war;
- alter a resource discovery;
- test a migration;
- compare alternative policy or infrastructure histories.

Branching, reproducibility, and snapshot semantics are prerequisites for this and remain future work.

### 2.11 Observer / "god's-eye" visualisation

A visual observer could show the world changing over simulation time:

- population movement
- caravans and ships
- armies
- migration
- settlements
- borders
- weather
- fires, floods, and other events
- trade flows

This is useful both as a future interface and as a development/validation tool for seeing emergent behaviour.

### 2.12 Eventual 3D client

A 3D, CRPG-like environment would be an exciting long-term possibility, but it is explicitly **not the primary goal**.

If it is ever built, it should be treated as another client of the same Worldloom world state, not as the simulation itself.

The primary user goals remain:

1. maintain a coherent persistent world for storytelling;
2. support TTRPG preparation and play;
3. support authors writing fiction;
4. allow inspection and exploration of the simulated world.

## 3. Shared interface primitives

These future interfaces suggest several capabilities that should remain easy to expose from the core architecture:

### World state at time T

A general query should be able to obtain a consistent view of the world at a specified simulation time, potentially scoped spatially and by entity.

### Provenance / "why is this true?"

A user should eventually be able to trace a fact to:

- producing module/model;
- inputs;
- events;
- configuration;
- simulation time;
- random seed where relevant;
- uncertainty/resolution history;
- external source or adapter where applicable.

### Multiple knowledge levels

The same canonical world should support views such as:

- simulated reality;
- broad statistical projection;
- resolved local reality;
- public/common knowledge;
- individual observer knowledge;
- deliberately incomplete or uncertain knowledge.

These are projections or information states, not separate competing canonical worlds.

### Controlled mutation

Interfaces that change the world should make the transition explicit:

- query/observe;
- propose;
- edit canonical state;
- schedule an event;
- run a branch/counterfactual.

The architecture should avoid conflating these operations.

## 4. Architectural implications

These interface ideas do **not** require building UI now. They imply that the core should preserve:

- stable entity identity;
- explicit canonical versus derived semantics;
- spatial and temporal addressing;
- provenance;
- event history;
- uncertainty and resolution semantics;
- reproducible snapshots/checkpoints;
- adapter boundaries;
- queryable relationships and dependencies;
- outputs suitable for GIS and other visualisation systems.

The strongest near-term requirement is therefore not a UI framework. It is maintaining a world representation and module contracts that can support many independent projections later.

## 5. Relationship to current work

Nothing in this document changes the current TODO queue by itself.

When an implementation decision has implications for future interfaces, agents should surface that architectural consequence rather than implementing an interface prematurely.

A future interface becomes an implementation task only when it is deliberately selected as active work.

## 12. Future world interfaces

The eventual world should be usable through multiple clients over the same canonical state.

The primary long-term storytelling interface is expected to be a world-guide/wiki-like system, complemented by interactive GIS and a natural-language query/edit interface. Other useful clients include historical timelines, character/observer views, GM/referee dashboards, traveller/gazetteer views, author research tools, continuity inspectors, counterfactual explorers, and visual "god's-eye" observation.

A 3D/CRPG-like client is an aspirational possibility rather than the primary goal. If eventually built, it should consume the same Worldloom state rather than becoming a separate simulation.

These directions imply that the core should preserve stable identity, temporal and spatial scope, provenance, event history, uncertainty/resolution semantics, reproducible snapshots, and queryable relationships. They do not imply that any UI technology should be selected now.

The interface vision is documented separately in docs/INTERFACES.md. It is background for architectural decisions, not a near-term implementation backlog.

