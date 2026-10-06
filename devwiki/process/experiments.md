---
type: process
status: process
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# Experiments

## Experiments

Experimental work belongs under the process conventions below and should not silently become normative architecture.

Experiment documentation records live under [[devwiki/experiments/README]]. Executable experiment code, configurations, generated results, and other working artifacts remain under the repository's top-level `experiments/` tree. The two locations are deliberately distinct: the devwiki records the knowledge produced by an experiment, while the top-level tree holds the reproducible working artifacts.

The FMG export scale and structure record is [[devwiki/experiments/fmg-export-scale-and-structure]].

Record random seeds and relevant software/configuration versions.

CI records a provenance header for every job. Pull-request runs print both the merge SHA and pull-request head SHA so the tested merge result is traceable to both inputs.

The `Python 3.11 tests` job runs both test suites against the lowest supported Python version. `Coverage (informational)` provides branch coverage as a review aid without a threshold or upload. `FMG digest reproducibility (informational)` regenerates the digest into a temporary path and compares it with the committed reference without modifying committed results or references.

### Keep experiments separate

Experiments are evidence about models and architecture. They are not automatically normative architecture. Keep experimental code/configuration/results separate from the stable framework.
