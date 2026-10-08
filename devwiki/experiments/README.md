---
type: experiment
status: experiment
summary: Migrated documentation page; source material retained verbatim for Phase 3 traceability.
related: ["[[index]]"]
---

# README

# Experiment Conventions

Experiments are evidence about the architecture or a model, not architecture by themselves.

Each substantial experiment should record:

- purpose and question
- model implementation/version
- configuration
- random seed(s)
- software/environment versions
- execution parameters
- measurements
- output locations
- interpretation, kept distinct from raw results

Repository layout separates experiment knowledge from experiment artifacts:

    devwiki/experiments/<id>.md    # experiment record and interpretation
    experiments/<id>/              # code/configuration/raw results where needed

The experiment record should point to the artifact locations when they are relevant. Experiments should be reproducible where practical and should not overwrite raw outputs without recording the change.

## Current audit records

- [[src-function-complexity-audit]] — informational source function-size, cyclomatic-complexity, and nesting baseline.
