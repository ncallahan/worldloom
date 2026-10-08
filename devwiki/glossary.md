---
type: reference
status: settled
summary: Worldloom glossary migrated verbatim from the legacy glossary for Phase 3 traceability.
related: ["[[index]]"]
---

# Glossary

# Worldloom Glossary

This glossary defines the project’s key terms as they are used in the architecture, interface contracts, and tests. Terms may evolve as the project matures, but any change to their meaning should be reflected here as part of the same change.

## Canonical state
The authoritative representation of the simulated world.

Canonical state is the source of truth about what the world currently believes to be true. It includes persistent facts such as entities, fields, events, relationships, constraints, and provenance. It is authoritative, but not immutable: established canonical state is never overridden by derived observations, simulation, projections, or resolution processes. Changes to established canonical state occur only through an explicit, recorded authorial amendment.

## Authorial amendment

An explicit, recorded change to canonical state made by the world's author, for example moving a settlement or changing a ruler. An authorial amendment is part of the world's history and retains provenance describing what changed, from what, by whom, and optionally why. It takes precedence over earlier canonical values, including imported values. Dependent derived values may become stale after an amendment; how that staleness is detected remains an open question.

## Derived observation
A value calculated from canonical state, external data, or explicit inputs for measurement, analysis, decision support, or module operation.

Derived observations are not authoritative world history merely because they are stored. They may be recomputed, cached for performance, or used as input to a resolution process, but they remain distinct from canonical state unless explicitly promoted.

## Projection
A broad, useful representation of the world that does not require every local fact or historical detail to be resolved.

A projection may contain coarse, statistical, uncertain, or candidate information. It exists to make the world useful to inspect and explore before complete resolution. The representation of a projection is intentionally unspecified.

## Provisional information
Information that is useful for representing or reasoning about the world but has not yet been established as canonical persistent fact.

Provisional information may include candidate entities, probability distributions, coarse projections, generated alternatives, or other unresolved descriptions. Its eventual representation is an open architectural question.

## Progressive generation
The process of generating a useful broad world representation and resolving additional detail only where required by exploration, editing, simulation, or dependencies.

Progressive generation is an architectural behaviour, not merely an optimisation. It permits the world to become more detailed without requiring unrelated parts to be fully generated first.

## Field
A structured value associated with a world location or domain, such as a terrain raster, a water mask, a population density map, or another spatially-indexed quantity.

A field is a canonical state concept when it is authoritatively part of the simulation. It may also appear as a derived observation when it is a computed measurement or analytical result.

## Entity
A persistent world fact with stable identity.

An entity represents a distinct object, actor, or fact in the simulated world, such as a settlement, a river segment, a road, or a historical actor. Identity is part of the contract: an entity persists across simulation steps and may be referenced by provenance and events.

## Event
A recorded occurrence with time and effect.

Events are first-class world records. They may change canonical state, trigger dependent modules, resolve uncertainty, or record external or endogenous phenomena. Events should carry enough information to explain when the event occurred and why it matters.

## Relationship
A declared association between entities, values, or state elements.

Relationships represent structural or semantic links in the world, such as adjacency, ownership, membership, dependency, causality, or a graph edge between world objects.

## Constraint
A rule or restriction that limits valid world states or transitions.

Constraints help define what configurations are permitted by the model, such as validity conditions, allowed transitions, conservation laws, or domain-specific rules.

## Provenance
The recorded lineage of a fact or value.

Provenance answers why the world believes something. It may include the producer module, inputs, configuration, simulation time, and uncertainty or confidence where relevant. Provenance is essential for auditing, explainability, and reproducibility.

## Resolution
The process of converting an uncertain, provisional, or derived value into a concrete persistent fact.

Resolution is the explicit transition from an observation or uncertain state into canonical world state. It is not silent re-sampling and should preserve provenance to explain which decision created the persistent fact.

## Module contract
The declared interface of a simulation module.

A module contract describes a module’s identity, inputs, outputs, spatial and temporal resolution, dependencies, uncertainty characteristics, and lifecycle behaviour. The contract is the primary boundary between a module and the rest of the world.

## InputSpec
A typed declaration of a module input.

An `InputSpec` identifies a named input and its semantic kind, such as `STATE`, `OBSERVATION`, or `EVENT`.

## OutputSpec
A typed declaration of a module output.

An `OutputSpec` identifies a named output and its semantic kind, such as `STATE`, `OBSERVATION`, or `EVENT`.

## DataKind
A semantic category for world data.

DataKind distinguishes the meaning of data flowing through the simulation:

- `STATE`: canonical world state
- `OBSERVATION`: derived measurement or analysis
- `EVENT`: historical or triggering occurrence

This is intentionally a semantic contract, not a full scientific or data-model schema.

## Observation boundary
The design rule that keeps derived observations distinct from authoritative state.

A derived observation is not granted the status of canonical state merely because it is stored or passed through an interface. Promotion to canonical state must be explicit and documented via a resolution step.

## Snapshot
A point-in-time capture of a world state.

A snapshot records the state of the world at a given moment, with enough isolation that later mutation does not leak into earlier saved state. Snapshots may include optional metadata such as time, step, or execution context.

## Simulation context
Execution metadata available to a simulation step.

Simulation context includes values such as step count, simulation time, random seed, and other runtime metadata. It does not replace canonical state; it describes the execution conditions under which a step ran.

## World state
The in-memory representation of the current authoritative world and its explicitly separated observations.

World state includes the canonical fields, entities, events, observations, and provenance. The distinction between canonical state and observations is part of the model contract.

## Dependency order
The ordering required to execute modules when one module relies on another’s output.

Worldloom executes modules according to declared dependencies rather than caller-supplied ordering. When modules are ready, execution should remain deterministic and therefore reproducible.

## Interface layer
The architectural boundary containing the contracts that modules and systems must satisfy.

The interface layer defines the module and data contracts that compose the canonical world model without forcing all implementations into a single internal style or package structure.

## Adapter
A thin compatibility layer between a specialist system and Worldloom’s canonical representation.

Adapters preserve provenance and allow established external tools to interoperate without forcing Worldloom to reimplement their domain logic internally.

## State versus observation
The central conceptual distinction in Worldloom.

A value is canonical state when it is part of the authoritative simulated world. A value is an observation when it is derived, contextual, or measured and must not be confused with authoritative fact unless explicitly promoted.
