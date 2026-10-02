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

## 6. First concrete interface: Obsidian-compatible Markdown

The first interface selected for implementation is an **Obsidian-compatible Markdown world vault**.

This turns the previously abstract world-guide/wiki direction into a concrete, low-coupling target. A Worldloom vault should be usable as an ordinary Obsidian vault: notes should remain readable and navigable as Markdown, while structured metadata and links provide machine-readable connections back to the simulated world.

The intended architecture is:

    Worldloom canonical state
             |
             v
    Markdown world vault
             |
       +-----+-----+
       |           |
    Obsidian    Atlas-VTT

### What this means

The vault is the **first human-facing projection of Worldloom**, not a second canonical database. Worldloom remains authoritative for simulated reality. Markdown files represent that reality and may eventually provide controlled inputs back into Worldloom through an explicit mutation workflow.

The first interface should be capable of representing at least:

- places and regions;
- settlements and infrastructure;
- people and populations;
- political entities and institutions;
- cultures and languages;
- religions and organisations;
- natural features;
- economic activity and trade;
- historical events;
- relationships and dependencies;
- current conditions.

The representation should preserve the distinction between simulated reality and information about that reality. In particular, a note may eventually contain or link to canonical facts, derived descriptions, unresolved/uncertain information, provenance, and in-world beliefs or rumours. These must not become semantically interchangeable merely because they appear in the same Markdown file.

### Atlas-VTT compatibility

Atlas-VTT is a compatibility target for this interface, not a Worldloom dependency. Its Obsidian-native workflow and ability to associate Markdown notes with map locations make it a natural first consumer of Worldloom's world vault.

Compatibility should be pursued where it follows naturally from the Markdown contract. Worldloom should not make Atlas-specific scene formats, asset stores, or implementation details part of canonical world state merely to obtain compatibility.

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


## 7. FMG import and MVP projection boundary (provisional)

The first concrete implementation path is an adapter from an FMG full JSON snapshot into Worldloom canonical state, followed by a read-only Markdown projection and raster export.

This is **provisional interface direction**, not a final import or spatial specification.

The MVP should expose two explicit transformation boundaries:

    FMG map coordinates
            |
            v
    source -> internal transformer
            |
            v
    Worldloom internal space
            |
            v
    internal -> target transformer
            |
            v
    export space

The transformers should be replaceable objects. The internal coordinate system remains an open decision; the MVP may use an explicit identity transformer so that the current FMG map space is represented without making that choice normative.

The read-only vault is a regenerable projection of the authoritative world file. Its exact note schema, metadata vocabulary, folder layout, identifier-to-filename mapping, and future mutation semantics remain open and require owner review.

The MVP raster export is another projection of Worldloom state. Existing GeoTIFF support remains useful during this phase; the longer-term GIS interchange direction may move toward GeoJSON without changing the current Markdown interface decision.
