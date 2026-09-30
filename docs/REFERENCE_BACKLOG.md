# Worldloom Research and Reference Backlog

## Status

This is a **research/reference backlog**, not a dependency list and not an architecture specification.

The projects and resources below were identified during early Worldloom research because they may provide useful algorithms, domain models, interfaces, data structures, or implementation ideas. They should be investigated when a relevant Worldloom module is being designed.

No item here is a commitment to integrate, depend on, reproduce, or emulate the referenced system.

## 1. Geography, terrain, GIS, and spatial processes

- **GPlates** — plate-tectonic reconstruction and deep-time geographic modelling.
- **GRASS GIS** — established GIS and raster/vector geoprocessing ecosystem.
- **WhiteboxTools** — terrain analysis and geospatial processing.
- **Landlab** — component-based modelling of Earth-surface processes.
- **Canwu** — procedural/world-generation research reference.
- **WorldGen / Worldsmith** — world-generation and procedural-world references.
- **WorldForge** — persistent/world simulation and game-world reference.
- **Hinterland** — procedural settlement/world-generation reference.
- **Chronopixel** — procedural/historical world-generation reference.

These are particularly relevant to the long-term geography/GIS and broad-world-projection goals.

## 2. Agent-based, social, and population modelling

- **Mesa** — Python agent-based modelling framework.
- **GAMA** — agent-based simulation and spatial modelling platform.
- **Neighborly** — simulation of populations, settlements, relationships, and social dynamics.
- **ESL** — agent/simulation-related research reference.
- **tacoma** — simulation/agent-system research reference.

These are references for possible population, settlement, social, economic, and institutional modules. They are not proposed Worldloom dependencies.

## 3. Environmental and biological process references

- **Onset**
- **RootTrace**
- **Ymir**

These were identified as potentially useful references for environmental/biological or spatial process modelling. Their relevance should be evaluated when concrete modules in those areas are designed.

## 4. Language and culture research backlog

Previously identified resources include:

- **Linguistic Linked Open Data** — possible structured language-resource ecosystem.
- **PolyGlot** — computational language-generation/reference tooling.
- **PanPhon** — phonological feature representation and analysis.
- **SakanaAI / IASC research** — research reference for language/AI-related modelling.
- Sociology and culture research channels/worksheets, including **The Grainbound**, as inspiration for modelling social structures and cultural processes.

These are research inputs only. Worldloom should not commit to a language or culture model until its module contracts and requirements are established.

## 5. Procedural generation and constraint references

- **Wave Function Collapse / Model Synthesis** — constrained procedural generation and local-consistency techniques.
- **WorldGen / Worldsmith / Aurelia / World Engine** — references for procedural generation and world representation.
- **Worlds**, **AEON**, **Oikoumene**, and **Sovereign** — additional world-simulation/worldbuilding references identified during research.
- **Worldsimulator** — broader world-simulation reference.

These may provide useful approaches to generating broad structures, resolving local detail, or maintaining constraints, but should not be treated as evidence that Worldloom should copy their architecture.

## 6. Reference policy

When a concrete Worldloom module is proposed:

1. Search this backlog for relevant established systems.
2. Investigate whether one or more can supply the required capability.
3. Compare their data model, resolution, determinism, licensing, performance, and interoperability characteristics with the Worldloom contract.
4. Prefer a thin adapter when a system is suitable.
5. Keep the Worldloom contract independent of the external implementation.
6. If none is suitable, document why before reimplementing substantial specialist functionality.

A reference becoming technically useful does not automatically make it an architectural decision.

## 7. Relationship to architecture

The backlog deliberately does not determine:

- the module graph;
- the canonical data model;
- the identifier scheme;
- validation architecture;
- storage technology;
- UI technology;
- dependency choices;
- implementation order.

Those decisions belong in the architecture/specification and should be made from demonstrated requirements and experiments.
