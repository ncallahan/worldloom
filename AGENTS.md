# Agent Instructions

This repository is **Worldloom**, a domain-neutral simulation platform.

## Before changing architecture

Read:
- `docs/ARCHITECTURE.md`
- `docs/SPECIFICATION.md`
- `docs/DEVELOPMENT.md`

Do not import assumptions, terminology, requirements, or architecture from an unrelated research project unless explicitly requested for a model, adapter, or experiment.

## Development principles

- Prefer existing libraries and specialist systems through adapters over reimplementation.
- Keep interfaces small and stable.
- Define a module contract before adding a module.
- Preserve the distinction between canonical world state and derived observations.
- Make uncertainty and provenance explicit where relevant.
- Add tests for behaviour and update documentation for architectural changes.
- Keep experiments separate from settled architecture.
- Never claim a test or experiment was run unless it was actually run.
- AI agents are implementation collaborators, not architectural authorities: do not silently redefine project requirements.
