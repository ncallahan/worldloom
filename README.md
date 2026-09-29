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

## Initial structure

- `docs/ARCHITECTURE.md` — system architecture and module boundaries.
- `docs/SPECIFICATION.md` — initial normative specification.
- `docs/DEVELOPMENT.md` — development and agent workflow.
- `docs/EXPERIMENTS.md` — experiment/reproducibility conventions.
- `src/worldloom/` — implementation package.
- `tests/` — automated tests.

## Status

Architecture v0.1 — foundation only. Interfaces are intentionally provisional until exercised by a minimal end-to-end prototype.
