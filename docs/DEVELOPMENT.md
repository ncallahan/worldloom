# Development Guide

## Principles

Worldloom is intended to grow from a small tested core into a broad interoperability framework.

Before making structural changes:

1. Read `docs/ARCHITECTURE.md`.
2. Read `docs/SPECIFICATION.md`.
3. Check `TODO.md` for the current active work.
4. Check existing interfaces and tests.
5. Define the proposed module contract.
6. Prefer an adapter to reimplementation of established specialist software.

## Tests

Run:

    python -m pytest

Tests should cover observable behaviour and architectural contracts.

The project should run the test suite on all branches, including feature branches, before code is considered ready for review or merge.

## Active work and project memory

Worldloom deliberately separates current work from long-term direction and historical record:

- `TODO.md` is the active working queue. It should contain only current or deliberately upcoming work.
- `docs/ROADMAP.md` records long-term direction and architectural goals, not a detailed task backlog.
- Git history records completed implementation work and provides the historical record of how the project evolved.
- `docs/ARCHITECTURE.md` and `docs/SPECIFICATION.md` describe settled or currently normative architectural decisions.
- `docs/EXPERIMENTS.md` records exploratory work, configurations, results, and interpretations.

When completing a TODO item:

1. Implement and test the smallest coherent change.
2. Update the relevant architecture/specification documentation if the change establishes or alters a project decision.
3. Remove or rewrite the completed item in `TODO.md` so it remains an accurate picture of active work.
4. Commit the change with a clear message describing what was actually changed.
5. Do not add completed work to `TODO.md` merely to preserve history; use Git history for that.
6. If implementation evidence changes the priority or invalidates a task, update `TODO.md` rather than mechanically following the previous ordering.

When starting work:

1. Read `TODO.md` and identify the smallest current task relevant to the request.
2. Check the specification and architecture before changing interfaces.
3. Inspect existing code and tests before introducing new abstractions.
4. Keep changes narrow enough that their architectural effect can be understood and tested.
5. Update `TODO.md` when the active work changes.

This process is especially important for AI coding agents: the TODO is the current queue, not an authority to invent requirements. Agents should preserve the distinction between active implementation work and historical direction.

## Feature branch workflow

Feature branches should be treated as isolated workspaces for experiment and implementation.

- Feature branches are expected to run the project test suite before they are considered ready.
- Copilot may operate on feature branches while the branch remains isolated from main.
- Main remains the stable baseline and should not accept speculative changes without review.
- Feature branches should not silently drift from the architectural documents or the current TODO queue.
- A feature branch is ready for merge only when the relevant tests pass and the architecture remains coherent.

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

AI agents may implement requested changes, but they are not architectural authorities. They must not invent requirements, silently broaden scope, hide failed experiments, or claim unexecuted tests as evidence. The repository architecture, specification, and tests remain the authoritative boundaries for implementation.
