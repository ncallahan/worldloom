---
type: process
status: process
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# Development Workflow

# Development Guide

## Principles

Worldloom is intended to grow from a small tested core into a broad interoperability framework.

Before making structural changes:

1. Read `devwiki/architecture/index.md` and the relevant architecture pages.
2. Check `devwiki/current.md` for the current active work.
4. Check existing interfaces and tests.
5. Define the proposed module contract.
6. Prefer an adapter to reimplementation of established specialist software.

## Tests

Run the unit suite with:

    python -m pytest -q tests/unit

Run the experiment suite with:

    python -m pytest -q tests/experiments

Tests should cover observable behaviour and architectural contracts. Experiment tests additionally record behaviours used to explore or document unsettled architectural questions.

Both suites should run on all branches, including feature branches, before code is considered ready for review or merge. Unit-test failures indicate a regression in an established contract; experiment-test failures indicate that an observed experimental behaviour has changed and should be investigated.

### Linting

Run the Python linter with:

    ruff check .

CI installs the exact pinned Ruff version used by the project. The Phase 2 lint configuration selects probable-defect rules (including pyflakes, selected pycodestyle error classes, W605, and the selected bugbear checks) and deliberately ignores E401, E701, E702, E731, and E741 because the repository uses compact style for those cases; these are style rules rather than defect checks for this codebase. E501, import sorting, UP, and the broader warning set are not enabled.

Lint suppressions must be local and justified. Use a line-level `# noqa: CODE` only when the flagged construct is intentional and the reason is documented beside the suppression. Do not add broad per-file ignores or use Ruff auto-fixes as a substitute for review.

## Active work and project memory

Worldloom deliberately separates current work from long-term direction and historical record:

- `devwiki/current.md` is the active working queue. It should contain only current or deliberately upcoming work.
- `devwiki/vision/roadmap.md` records long-term direction and architectural goals, not a detailed task backlog.
- Git history records completed implementation work and provides the historical record of how the project evolved.
- the `devwiki/architecture/` pages describe settled or currently normative architectural decisions.
- `devwiki/process/experiments.md` records exploratory work, configurations, results, and interpretations.

When completing a current-work item:

1. Implement and test the smallest coherent change.
2. Update the relevant architecture/specification documentation if the change establishes or alters a project decision.
3. Remove or rewrite the completed item in `devwiki/current.md` so it remains an accurate picture of active work.
4. Commit the change with a clear message describing what was actually changed.
5. Do not add completed work to `devwiki/current.md` merely to preserve history; use Git history for that.
6. If implementation evidence changes the priority or invalidates a task, update `devwiki/current.md` rather than mechanically following the previous ordering.

When starting work:

1. Read `devwiki/current.md` and identify the smallest current task relevant to the request.
2. Check the specification and architecture before changing interfaces.
3. Inspect existing code and tests before introducing new abstractions.
4. Keep changes narrow enough that their architectural effect can be understood and tested.
5. Update `devwiki/current.md` when the active work changes.

This process is especially important for AI coding agents: the TODO is the current queue, not an authority to invent requirements. Agents should preserve the distinction between active implementation work and historical direction.

## Feature branch workflow

Feature branches should be treated as isolated workspaces for experiment and implementation.

- Feature branches are expected to run both the unit and experiment test suites before they are considered ready.
- Copilot may operate on feature branches while the branch remains isolated from main.
- Main remains the stable baseline, but experiments that have been reduced to deterministic, documented, passing tests may be merged as part of the project's architectural discovery record.
- Experimental tests do not by themselves make the behaviour they record normative architecture; settled decisions belong in the architecture/specification documents.
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

## Pull request workflow

Open a pull request early in the life of a feature branch, normally as a **draft pull request** rather than waiting until the work is considered ready for merge.

Draft PRs are part of the development workspace, not just a final review step. They provide a convenient place to:

- inspect the branch diff against main;
- monitor GitHub Actions and other CI results;
- keep the experiment's implementation and test changes together;
- review the shape of an evolving change before deciding whether it is ready to merge.

The preferred workflow is therefore:

1. Create an isolated feature branch from the current main.
2. Open a draft PR as soon as there is a meaningful first increment to inspect.
3. Continue development on the branch and use the PR to inspect diffs and CI results.
4. Keep the PR in draft status while the experiment or implementation is still being explored.
5. Mark it ready for review only when the change is understood, tested, and ready for the project's normal review/merge decision.
6. Do not merge a draft PR merely because its CI is green.

This early-PR workflow is especially useful for experimental work because the PR itself provides a persistent, convenient view of both the evolving diff and automated evidence without treating the experiment as settled architecture.

## Testing is mandatory

**Every code change must be accompanied by appropriate automated tests.**

- Add or update unit tests for changed behaviour.
- Run the test suite before considering a change complete.
- Do not claim tests pass unless they were actually run.
- Preserve existing tests unless a change in behaviour deliberately requires updating them.
- Prefer small, deterministic, fast unit tests.
- Test architectural contracts and interfaces, not only implementation details.
- For integration/adaptor work, add focused tests for the adapter contract and use fixtures/mocks where practical rather than requiring external services in ordinary unit tests.
- Experimental code must not weaken the project's normal test suite.
- A failing test is a development problem to investigate, not something to hide or bypass.

The repository's CI workflow runs the test suite automatically for pushes and pull requests. A green local test run is useful, but CI is the authoritative check for commits entering shared repository history.
