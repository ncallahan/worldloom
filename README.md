# Worldloom

A modular framework for constructing, simulating, and exploring persistent computational worlds.

Worldloom is deliberately **domain-neutral**. Rather than implementing every domain itself, it provides a canonical set of interfaces through which specialised simulation, numerical, geospatial, visualisation, and analysis systems can be combined.

## Design goals

- Reuse existing simulation, numerical, visualisation, and analysis systems through adapters.
- Keep the interfaces between modules more stable than their implementations.
- Represent persistent world state, events, observations, and provenance explicitly.
- Make experiments reproducible and inspectable.
- Support agent-assisted development without allowing agents to silently redefine the architecture.
- Permit multiple simulation paradigms: discrete, continuous, agent-based, field-based, graph-based, hybrid, and external simulators.
- Start with the smallest useful implementation and grow through tested interfaces.

## Development documentation

The authoritative development documentation now lives in the [development wiki](devwiki/index.md).

Read `devwiki/index.md` first, then `devwiki/current.md`, then the pages relevant to the task. The wiki contains the current architecture, development process, experiments, open questions, vision, and research/reference material.

## Status

The architecture and interfaces remain intentionally provisional while the project is developed through tested module contracts and experiments.

## Running a configured simulation

Worldloom can run a simulation without writing Python by using a JSON run configuration.

    worldloom run examples/prototype_run.json

The configuration selects participating modules and supplies per-module configuration. Module contracts remain responsible for determining how those modules exchange data; the run configuration does not explicitly wire inputs and outputs.

Outputs are requested separately in the same configuration. Relative output paths are resolved relative to the configuration file.

The current JSON interface is intentionally small and experimental. It is a run configuration and not a general module-composition language.