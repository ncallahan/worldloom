# Worldloom Architecture

## 1. Purpose

Worldloom provides the **loom**, not every thread. It is an orchestration and interoperability layer for constructing persistent computational worlds from specialised systems.

The architecture should make it possible to combine existing geospatial, environmental, demographic, economic, linguistic, social, historical, numerical, and visualisation systems without requiring those systems to become one monolithic simulator.

Worldloom is also a **progressive procedural world model**. It should be possible to obtain a useful broad representation of a world quickly, without first resolving every local detail or simulating its entire history. As the world is explored, queried, edited, or required by another process, selected parts can be resolved to greater detail and made persistent.

The architectural principle is:

> **Generate broadly; resolve deeply where needed.**

This is a system property, not merely a performance optimisation.

## 2. Canonical world state

The simulated world has an authoritative canonical state. Conceptually it contains:

- entities
- fields
- events
- relationships
- constraints
- distributions and other uncertain states
- provenance

Modules read and write canonical state through explicit contracts. Derived observations are kept semantically separate from authoritative state and may be recomputed or cached without becoming world history. A module should not need to know the implementation details of another module.

The canonical state is the persistent part of the world: once a provisional result has been explicitly resolved into canonical state, subsequent modules should consume that established fact rather than independently regenerating it.

## 3. Modules

A module declares at least:

- inputs
- outputs, with each output identified as canonical state, derived observation, or event
- spatial resolution
- temporal resolution
- uncertainty characteristics
- dependencies
- lifecycle/step behaviour

A module may be an in-process Python component, an external executable, a GIS workflow, a numerical model, or an adapter around an existing application.

Modules may consume outputs from other modules and may cause further parts of the world to be resolved. The dependency mechanism therefore represents more than execution order: it is one of the ways in which local world knowledge can become available to later processes.

## 4. State, observation, and provisional information

The canonical state is authoritative simulated reality. A derived observation is a calculation made from canonical state or other declared inputs. Storing an observation does not promote it to world state.

Promotion is explicit: an observation may inform a resolution or simulation process that creates a persistent fact, with provenance linking the new fact to the observation and its underlying inputs.

The prototype represents this distinction directly: WorldState.fields and WorldState.entities hold canonical state, while WorldState.observations holds derived observations. ModuleSpec uses OutputSpec and DataKind to declare output semantics.

Worldloom also needs to represent information that is useful before it has been resolved into a concrete persistent fact. This may include broad statistical projections, candidate entities, probability distributions, or other provisional descriptions. **The representation of this information is intentionally not yet fixed.**

In particular, the architecture does not currently decide whether provisional information should be represented as:

- a special form of observation;
- first-class provisional state;
- generator/prior information from which canonical state is resolved;
- or another mechanism.

The important current requirement is behavioural: provisional information must be usable to produce a useful world representation, and selected portions must be able to become persistent facts without requiring unrelated portions of the world to be fully resolved.

## 5. Adapters

Worldloom should preferentially reuse established systems rather than reproduce them.

An adapter translates between a specialist system's native representation and the canonical Worldloom representation. For example, GIS data may be exchanged with QGIS or other established GIS tooling rather than having a new GIS engine built inside Worldloom.

Adapters should be thin where possible and should preserve provenance about external calculations and source data.

## 6. Time and orchestration

Modules operate at different natural temporal resolutions. For example:

- weather: minutes
- rivers and hydrology: hours/days
- economy: days/months
- population: months/years
- politics: days/years
- culture: decades
- geography: centuries/millennia

Simulation time is a numeric coordinate whose unit is supplied by simulation configuration. A module may declare a positive numeric temporal interval in those simulation-time units. The scheduler invokes each module when its interval is due rather than forcing every module through one universal timestep.

The scheduler is deterministic: when multiple modules are due at the same simulation time, declared dependency order is respected and the original module input order remains the tie-breaker for otherwise independent modules.

Each invocation receives the current simulation time and the elapsed time since that module's previous invocation. A module without a temporal interval is treated as a one-time/static module during a scheduled run.

Event-triggered scheduling is intentionally outside the current scheduler contract and remains future work.

## 7. Projection and resolution

Worldloom should distinguish two related activities:

**Projection** produces a broad, useful representation of what the world probably looks like. It may be generated at coarse spatial or temporal resolution and may contain unresolved or statistical information. Projection should be cheap enough that a user can obtain something useful to inspect without waiting for complete world generation.

**Resolution** turns selected provisional or uncertain information into concrete persistent facts. Resolution may be requested because a user asks about something, edits the world, a simulation step requires the information, or another module depends on it.

For example:

    broad world projection
      terrain / climate / broad regions
                |
                v
        user explores a river
                |
                v
       local hydrology resolved
                |
                v
       settlement history queried
                |
                v
      local demographic facts resolved

Resolution is selective. Unrelated parts of the world should not need to be fully resolved before a local question can be answered.

A resolved result becomes part of the world's history. Later modules consume that fact rather than independently resampling it.

## 8. Statistical states and resolution

A world may begin with uncertain, statistical, or otherwise provisional information. A resolution mechanism turns selected uncertainty into concrete persistent facts when the simulation requires it.

Example:

    Before:
    village candidate
      location: probability distribution
      population: distribution
      founding date: distribution

    After resolution:
    village
      location: concrete coordinate
      population: concrete value
      founded: concrete simulated date

Once resolved, the result is part of the world's history. Later modules consume that fact rather than independently resampling it.

The unresolved-state representation, invalidation rules, and dependency tracking required to support this behaviour remain open architectural questions until experiments provide enough evidence to choose among alternatives.

## 9. Events

Events are first-class records. An event may:

- change canonical state
- trigger dependent modules
- resolve an uncertainty
- record an external or endogenous occurrence
- carry provenance and uncertainty

This allows long-running simulations to explain how present state emerged from earlier state transitions.

## 10. Provenance

Worldloom should retain enough provenance to answer questions such as "Why does the world believe this?"

A derived value should be traceable to its producing module/version, inputs, event history, simulation time, configuration, and confidence/uncertainty where applicable.

Progressive resolution adds a further requirement: when a provisional result becomes canonical, its provenance should preserve the relationship between the resolved fact and the information or process from which it was resolved.

## 11. Prototype path

The first end-to-end prototype should be deliberately small. Its immediate purpose is to demonstrate **meaningful module-to-module interaction**, not to implement progressive world generation in miniature.

A useful chain is:

    module A
        ↓
    output available
        ↓
    module B consumes A
        ↓
    B produces something
        ↓
    module C consumes B + existing state
        ↓
    C resolves or changes state
        ↓
    persistent fact / event

The current terrain → water → settlement suitability → settlement resolution chain is a suitable vertical slice. It should remain small while making the dependency causal enough that tests demonstrate that downstream results actually depend on upstream outputs.

Progressive projection and resolution should be tested separately once the prototype can support meaningful module interaction.

## 12. Architectural boundary

Worldloom defines interoperability and orchestration contracts. Specialist domain models remain independently replaceable.

The principal architectural asset is therefore the interface between systems, not any one particular domain model.

This also means that broad projection and later local resolution should not force every specialist system into one common internal simulation model. Specialist systems may remain coarse, deterministic, statistical, static, dynamic, or external as appropriate, provided their Worldloom contract is explicit.

## 13. Snapshot semantics

Snapshots are point-in-time captures of the world state intended to support reproducibility, restoration, and eventually branching.

The current snapshot contract is deliberately narrow:

- fields, entities, events, observations, and provenance are captured;
- captured state is deep-copied so later mutation cannot alter the snapshot;
- the snapshot container is immutable at the container level;
- optional metadata may record execution context;
- restoring a snapshot deep-copies its contents back into the world, so the restored world does not share mutable nested state with the snapshot.

Snapshot metadata is contextual rather than canonical world state. More advanced checkpointing and branching semantics remain future work until they are required by the simulation engine.


## 14. Future interface boundary

Worldloom is intended to support multiple clients over the same canonical world rather than separate world representations.

Long-term clients may include:

- a generated world-guide/wiki;
- interactive GIS;
- natural-language query and controlled world editing;
- historical timeline exploration;
- character/observer perspectives;
- GM/referee tools;
- author research tools;
- consistency and continuity inspection;
- scenario/counterfactual exploration;
- visual observation;
- eventually, a 3D client.

These are future interface directions, not current implementation requirements.

The architectural consequence is that the core should remain capable of exposing a coherent world at a specified simulation time and scope, tracing provenance, distinguishing canonical reality from derived projections and observer knowledge, and making mutations or branch simulations explicit.

A user-facing interface should be treated as a projection or control surface over Worldloom state. It should not become an alternative authority for world facts.

The eventual 3D environment is intentionally secondary to the primary storytelling goals: maintaining a consistent world for TTRPGs and fiction, and making that world inspectable and usable by authors and game masters.

## 15. Obsidian-compatible Markdown as the first interface

The first concrete user-facing interface for Worldloom is an **Obsidian-compatible Markdown world vault**. This is an architectural boundary, not merely an export format: the vault is the first human-facing projection of the simulated world and should be useful directly in Obsidian.

The Markdown representation should remain human-readable and navigable while carrying enough structured metadata and links for Worldloom to maintain a meaningful connection between notes and world entities, places, events, and relationships. The detailed note schema, metadata vocabulary, folder conventions, and mutation semantics remain to be designed separately.

The intended relationship is:

    canonical Worldloom state
              |
              v
    Obsidian-compatible Markdown vault
              |
       +------+------+
       |             |
    Obsidian      Atlas-VTT

Atlas-VTT is a compatibility target rather than a Worldloom core dependency. Where Atlas-VTT conventions provide useful interoperability without distorting Worldloom semantics, Worldloom should support them through the Markdown/interface boundary. Atlas-specific scene or asset formats should not become canonical Worldloom state merely because Atlas can consume them.

The core semantic boundary remains important: Worldloom owns the meaning and authority of the simulated world; Markdown is a human-facing representation of that state. A future mutation workflow may interpret edits to Markdown as requests to change canonical state, but the file itself does not automatically become an independent authority for world facts.

This establishes a concrete first interface while preserving the broader architectural principle that other clients, including GIS, natural-language interfaces, timelines, observer views, and future visual clients, consume the same underlying world rather than maintaining competing world models.


## 16. Declarative run configuration and CLI

Worldloom should be usable for basic simulation experiments without requiring a user to write Python. The first implementation therefore provides a small JSON run configuration and a command-line entry point:

    worldloom run <configuration.json>

A run configuration describes:

- simulation time settings;
- the modules participating in the run;
- configuration for each module instance;
- requested output projections;
- execution options such as a run seed.

It deliberately does **not** describe inter-module wiring. Module contracts, semantic input/output names, and declared dependencies remain responsible for determining how participating modules interact.

This establishes three distinct configuration concerns:

    module contract
        how a module communicates

    run configuration
        which modules participate and how each instance is configured

    future composition/integration configuration
        explicit wiring or reusable multi-module compositions when the
        simpler run configuration is no longer sufficient

The third category is intentionally deferred. The current run configuration should remain a thin orchestration layer rather than becoming a second simulation architecture.

Module-specific configuration is allowed to have module-specific structure. A module may provide its own configuration decoding rather than requiring Worldloom to define a universal parameter schema.

Output adapters are similarly selected by a small adapter name and supplied with adapter-specific configuration. This is an initial mechanism for experimentation, not a commitment to a final plugin/discovery architecture.

The run configuration is execution metadata, not canonical world state. The resulting WorldState remains the authoritative simulation state, while requested outputs are projections of that state.

This separation should make it possible to save and reproduce an experiment as a small human-editable file while preserving the architectural boundary between orchestration, module semantics, canonical state, and external representations.
