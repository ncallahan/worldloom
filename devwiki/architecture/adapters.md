---
type: architecture
status: normative
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# Adapters

## 5. Adapters

Worldloom should preferentially reuse established systems rather than reproduce them.

An adapter translates between a specialist system's native representation and the canonical Worldloom representation. For example, GIS data may be exchanged with QGIS or other established GIS tooling rather than having a new GIS engine built inside Worldloom.

Adapters should be thin where possible and should preserve provenance about external calculations and source data.

## 12. Architectural boundary

Worldloom defines interoperability and orchestration contracts. Specialist domain models remain independently replaceable.

The principal architectural asset is therefore the interface between systems, not any one particular domain model.

This also means that broad projection and later local resolution should not force every specialist system into one common internal simulation model. Specialist systems may remain coarse, deterministic, statistical, static, dynamic, or external as appropriate, provided their Worldloom contract is explicit.

## 9. External systems

The architecture SHOULD favour adapters to established specialist software over reimplementation when an appropriate system already exists.

External systems MAY provide either broad/provisional outputs or resolved outputs, provided the adapter makes their semantic status explicit.

## Integration philosophy

Worldloom is the loom, not every thread.

Prefer established specialist systems behind adapters rather than reimplementing GIS, terrain, hydrology, agent-based modelling, language processing, etc. inside Worldloom when an appropriate external system exists.

The repository's research/reference backlog contains systems such as GPlates, GRASS GIS, WhiteboxTools, Landlab, Mesa, GAMA, Neighborly, Canwu, WorldForge, WorldGen/Worldsmith, and others. These are references to investigate, not committed dependencies.

### The loom, not every thread

Worldloom should provide interoperability, orchestration, canonical state, provenance, scheduling, and stable interfaces. It should **not** attempt to reimplement every specialist domain model.

When an established system can provide a capability, prefer a thin adapter/interface layer over reproducing that capability inside Worldloom.

### Existing systems first

Before implementing a substantial capability, check whether a suitable established/open-source system already exists. If so, investigate an adapter before proposing a new implementation. See `docs/REFERENCE_BACKLOG.md`.
