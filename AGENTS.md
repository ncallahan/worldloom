# Agent Instructions

This repository is **Worldloom**, a domain-neutral simulation platform.

## Before changing architecture

Read, in order:
- `devwiki/index.md`
- `devwiki/current.md`
- the relevant architecture, process, experiment, question, vision, or reference pages.

Before changing a general data contract, surface the architectural options and trade-offs first. Keep validation and identifier-scheme decisions separate unless the current task requires both.

## Development principles

- Prefer existing specialist systems through adapters over reimplementation.
- Keep interfaces small and stable.
- Preserve canonical state versus derived observations.
- Make uncertainty, provenance, and experiment status explicit where relevant.
- Add tests for behaviour and update documentation for architectural changes.
- Keep experiments separate from settled architecture.
- Work on feature branches and do not merge unless explicitly asked.
- Never claim a test or experiment was run unless it actually was.
- AI agents are implementation collaborators, not architectural authorities.

## Migration discipline

- `devwiki/log.md` records migration traceability and important decisions.
- Do not begin Phase 4 deletion until explicitly authorised.

<!-- Migration source heading: # Worldloom — Copilot Instructions -->
<!-- Migration source heading: ## Read this first -->
<!-- Migration source heading: ## Testing is mandatory -->
<!-- Migration source heading: ## Architectural principles -->
<!-- Migration source heading: ## Development discipline -->
