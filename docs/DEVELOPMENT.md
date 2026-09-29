# Development Guide

## Principles

Worldloom is intended to grow from a small tested core into a broad interoperability framework.

Before making structural changes:

1. Read `docs/ARCHITECTURE.md`.
2. Read `docs/SPECIFICATION.md`.
3. Check existing interfaces and tests.
4. Define the proposed module contract.
5. Prefer an adapter to reimplementation of established specialist software.

## Tests

Run:

    python -m pytest

Tests should cover observable behaviour and architectural contracts.

## Adding a module

A new module should document:

- purpose
- inputs
- outputs
- spatial and temporal resolution
- dependencies
- uncertainty
- lifecycle
- provenance
- validation strategy

Keep the implementation replaceable behind its contract.

## Experiments

Experimental work belongs under `docs/EXPERIMENTS.md` conventions and should not silently become normative architecture.

Record random seeds and relevant software/configuration versions.

## AI-assisted development

AI agents may implement requested changes, but they are not architectural authorities. They must not invent requirements, silently broaden scope, hide failed experiments, or claim unexecuted tests pass.
