---
type: experiment
status: process
summary: Maintainability audit of the Markdown-vault exporter, using the source-complexity baseline and targeted review of implementation, tests, and interface documentation.
related: ["[[devwiki/experiments/src-function-complexity-audit]]", "[[devwiki/architecture/obsidian-markdown-interface]]", "[[devwiki/vision/fmg-import-vault-mvp]]"]
---

# Markdown-vault exporter maintainability audit

## Purpose

Assess the maintainability risks in the current Markdown-vault exporter before considering refactoring.

This is a review of the existing implementation, not a refactoring proposal or a rule-setting exercise. The audit is intended to identify responsibility boundaries, coupling, test-coverage risks, and plausible future refactoring seams while preserving the distinction between evidence and future decisions.

## Scope and evidence

The review covers:

- `src/worldloom/adapters/markdown_vault/exporter.py`
- `tests/unit/test_markdown_vault.py`
- the normative Markdown-interface boundary recorded in `devwiki/architecture/obsidian-markdown-interface.md`
- the source function-size and cyclomatic-complexity baseline produced by the companion audit

The companion complexity audit identified `export_markdown_vault` as the strongest source-level hotspot: 162 lines of source span and cyclomatic complexity 55 (Radon rank F). Other substantial functions include `_note` (97 lines, CC 23), `_import_note` (62 lines, CC 21), and `_display_map` (substantial branching and policy logic). These measurements are triage evidence, not quality thresholds.

The Markdown-vault test module currently reports approximately 46% coverage for the Markdown-vault implementation. The existing tests nevertheless exercise a number of important end-to-end behaviours, including determinism, filename sanitisation, duplicate-title disambiguation, link resolution, collision protection, hand-edit detection, rollback after write failures, malformed values, surrogate handling, and non-FMG worlds.

## Maintainability assessment

### 1. Responsibility density

`export_markdown_vault` is an orchestration point for several distinct responsibilities:

1. Build the projection model: derive titles, paths, display names, path collisions, and inverse relationships.
2. Validate source data: entity identifiers, strings, and JSON serialisability.
3. Render Markdown: entity notes, kind indexes, the root index, and the import report.
4. Construct projection metadata: world fingerprint, per-file hashes, and the vault marker.
5. Reconcile an existing vault: marker validation, hand-edit detection, protection of foreign files, and removal of obsolete generated files.
6. Perform transactional filesystem replacement: staging, backup, copying, and rollback.

The high complexity therefore reflects responsibility density at the orchestration boundary, rather than uniformly complicated helper functions.

### 2. Helper structure

Several lower-level helpers already have relatively narrow purposes, including:

- `_id_parts`
- `_title`
- `_filename`
- `_yaml_value`
- `_frontmatter`
- `_safe_text`
- `_display`
- `_link`
- `_items`
- `_mesh`

This is evidence that the implementation is not simply an undifferentiated monolith.

The larger helpers have broader semantic responsibilities. In particular:

- `_display_map` contains the policy for choosing human-readable disambiguation labels.
- `_note` combines frontmatter construction, imported-fact rendering, relationship rendering, inverse relationships, and provenance rendering.
- `_import_note` interprets import diagnostics and renders the import report.
- `export_markdown_vault` coordinates these operations with validation and filesystem lifecycle management.

These are plausible future seams, but the audit does not establish that they should be extracted.

### 3. Filesystem and transactional complexity

The latter portion of `export_markdown_vault` is materially different from the projection/rendering work.

It handles:

- refusing unsafe target paths;
- recognising Worldloom-managed vaults;
- detecting changes to previously generated files;
- refusing to overwrite unlisted files;
- staging generated output;
- backing up managed files;
- removing obsolete generated files;
- copying new files into place;
- restoring the previous state after a failure.

This logic represents a meaningful safety invariant: a failed export should not leave the existing vault partially replaced.

The existing tests explicitly exercise injected failures during both backup and write phases. Any future separation of filesystem responsibilities therefore needs to preserve these transactional semantics, rather than merely reduce function length.

### 4. Test coverage and refactoring risk

The approximately 46% coverage makes internal refactoring comparatively risky.

The current test suite has strong end-to-end coverage of several externally visible invariants, but coverage alone does not establish that every branch in the exporter is protected. In particular, the complexity audit indicates substantial branching in code responsible for:

- disambiguation;
- diagnostic interpretation;
- validation;
- existing-vault reconciliation;
- rollback.

Before a structural refactor, targeted characterization tests would provide more useful protection than relying on the existing aggregate coverage figure alone.

This is a risk assessment, not a recommendation to increase coverage to a particular threshold. No threshold is established by this audit.

### 5. Architectural boundary

The exporter is consistent with the documented semantic boundary in which Markdown is a human-facing representation of Worldloom state rather than an independent authority for world facts.

Consequently, maintainability work should preserve the distinction between:

- canonical Worldloom state;
- derived projection data;
- human-readable presentation;
- and filesystem management of generated projection artifacts.

The audit does not propose changing that boundary.

## Candidate future seams

The following areas appear to be plausible candidates for future investigation:

| Area | Why it is a possible seam | Main risk to preserve |
| --- | --- | --- |
| Projection-model preparation | Separates derived paths, titles, displays, and inverse relationships from I/O | Deterministic ordering and cross-reference consistency |
| Markdown rendering | Separates representation construction from filesystem lifecycle | Exact filenames, frontmatter, links, and projection vocabulary |
| Import-report rendering | Has its own diagnostic interpretation and output structure | Correct treatment of heterogeneous diagnostic shapes |
| Vault reconciliation | Separates managed-file safety checks from generation | Never overwrite hand-edited or foreign files unexpectedly |
| Transactional write/rollback | Is conceptually independent of Markdown semantics | Atomic-enough replacement and restoration after failure |
| Display/disambiguation policy | Encapsulates human-readable naming decisions | Stable, unique displays without changing entity-ID-based paths |

These are hypotheses for future design work, not prescribed decomposition.

## Invariants identified for future work

Any future refactoring should preserve, at minimum, the behaviours currently represented by the implementation and tests:

- entity-ID-based projected filenames;
- deterministic output;
- unique and stable display labels within a kind;
- resolvable generated wikilinks;
- safe filename sanitisation and reserved-name handling;
- protection against path collisions;
- protection against Markdown/code-fence injection in rendered values;
- rejection of unsafe string values before writing;
- rejection of non-JSON-serialisable values with useful source paths;
- preservation of foreign files;
- detection of hand-edited managed files;
- safe handling of deleted managed files;
- marker integrity and file hashes;
- rollback when filesystem writes fail;
- provenance and import-report representation;
- projection-only semantics rather than Markdown becoming canonical state.

This list records observed/required behaviours for later characterization; it is not a new normative architecture specification.

## Interpretation

The exporter is maintainable enough to continue serving the MVP, but it has a clear concentration of orchestration complexity and several responsibilities that could eventually be separated.

The principal concern is not function length by itself. The more important issue is that projection construction, rendering, validation, vault reconciliation, and transactional filesystem management are coordinated within the same top-level operation.

At the same time, the existing helper structure and end-to-end tests provide a reasonable starting point. The approximately 46% coverage means that structural refactoring should not be undertaken merely because the complexity metrics are high.

The safest future sequence would be to improve characterization of the behaviours that matter most, then evaluate individual seams against those tests. No such refactoring is proposed or authorised by this audit.

## Question | Evidence | Tentative conclusion

| Question | Evidence | Tentative conclusion |
| --- | --- | --- |
| Is the exporter unusually complex? | `export_markdown_vault` has 162 source lines and CC 55; several helpers are also substantial. | Yes; it merits maintainability attention. |
| Is the complexity solely caused by poor factoring? | The implementation already has several narrow helpers, while the top-level function coordinates multiple genuinely distinct responsibilities. | No; some complexity is inherent orchestration and safety logic. |
| Is immediate refactoring justified? | The exporter has approximately 46% test coverage despite meaningful end-to-end tests. | No; refactoring should wait for stronger characterization of critical behaviours. |
| Are there plausible refactoring seams? | Projection preparation, rendering, report generation, reconciliation, transactional writing, and display policy have distinguishable responsibilities. | Yes, but the correct decomposition remains an open design question. |
| Does the audit establish complexity or coverage thresholds? | The companion complexity audit is explicitly diagnostic and proposes no hard limits. | No. |
| Does this audit change the Markdown architectural boundary? | The current implementation and architecture documentation treat Markdown as a projection of canonical Worldloom state. | No. |

## Unresolved questions

- Which of the candidate seams, if any, produces a materially clearer design without obscuring projection invariants?
- Which behaviours need additional characterization before a structural refactor can be considered low risk?
- Should filesystem transaction handling eventually be represented as a separately testable component?
- How much of the current rendering policy should remain together because its output semantics are tightly coupled?
- Whether the current end-to-end tests sufficiently characterize deterministic output across larger FMG worlds remains to be established.

## Status

**Process / audit only.**

No production-code changes, refactoring, coverage threshold, complexity threshold, or new architectural rule follows from this record.
