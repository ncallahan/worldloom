---
type: process
status: process
summary: Phase 1 inventory mapping every current documentation heading, planned wiki destination, consolidation, contradictions, and path-reference findings.
updated: 2026-10-03
sources: [docs/ARCHITECTURE.md, docs/SPECIFICATION.md, docs/DEVELOPMENT.md, docs/EXPERIMENTS.md, docs/GLOSSARY.md, docs/INTERFACES.md, docs/REFERENCE_BACKLOG.md, docs/ROADMAP.md, docs/COPILOT_CONTEXT.md, docs/CAMPAIGN DIRECTION.md, README.md, AGENTS.md, TODO.md, .github/copilot-instructions.md]
related: [[index]], [[process/wiki-conventions]], [[process/agent-rules]]
---

# Migration map

This is the **Phase 1 inventory and plan** for migrating the repository documentation into devwiki/. It is temporary and is intended to be deleted in the final retirement commit.

No Phase 2 wiki pages are created by this commit.

## Treatment key

- **verbatim** — normative or otherwise authoritative source text is to be moved without paraphrase. For architecture pages, SPECIFICATION requirements go verbatim in **Requirements** and ARCHITECTURE material goes in **Rationale**; the Requirements status is normative.
- **consolidated** — duplicated/non-normative material is retained once in a canonical wiki page and the other source material is represented by links. The consolidation is recorded below.
- **rewritten** — intentionally slimmed/restructured material required by the new wiki operating model. This is not a license to rewrite normative requirements or settled architectural decisions.
- Experiment results remain experimental; vision remains vision; neither becomes normative merely because it is moved.

## Source inventory

| Source | Lines | Inventory status |
|---|---:|---|
| docs/ARCHITECTURE.md | 301 | Read in full; 16 sections mapped below. |
| docs/CAMPAIGN DIRECTION.md | 194 | Read in full; non-normative direction mapped to vision. The uploaded copy was also supplied for traceability. |
| docs/COPILOT_CONTEXT.md | 99 | Read in full; duplicated orientation/agent guidance to be consolidated. |
| docs/DEVELOPMENT.md | 118 | Read in full; workflow/process guidance to be split by concern. |
| docs/EXPERIMENTS.md | 687 | Read in full; conventions plus 10 experiment records mapped below. |
| docs/GLOSSARY.md | 130 | Read in full; terms become headings in devwiki/glossary.md. |
| docs/INTERFACES.md | 350 | Read in full; non-normative interface vision split into vision pages. |
| docs/REFERENCE_BACKLOG.md | 91 | Read in full; research/reference material split by category. |
| docs/ROADMAP.md | 259 | Read in full; non-normative roadmap moved to vision/roadmap.md. |
| docs/SPECIFICATION.md | 290 | Read in full; normative requirements mapped verbatim to architecture pages. |
| README.md | 42 | Read in full; documentation/navigation content will be updated in Phase 4. |
| AGENTS.md | 25 | Read in full; rewritten to the required <=60-line root agent entry point in Phase 2. |
| TODO.md | 42 | Read in full; active work/questions consolidated into current.md and question notes. |
| .github/copilot-instructions.md | present | Read in full; duplicated agent guidance will become a one-line pointer to AGENTS.md in Phase 2. |
| root COPILOT_CONTEXT.md | absent | Checked; no root file exists. |
| root CLAUDE.md | absent | Checked in the repository tree; no root file exists. |

## Heading-by-heading destination map

### docs/ARCHITECTURE.md

| Source heading | Destination | Treatment |
|---|---|---|
| # Worldloom Architecture | devwiki/index.md + architecture pages | consolidated |
| ## 1. Purpose | architecture/progressive-generation-and-resolution.md | consolidated |
| ## 2. Canonical world state | architecture/canonical-state-vs-observation.md | consolidated |
| ## 3. Modules | architecture/modules-and-contracts.md | consolidated |
| ## 4. State, observation, and provisional information | architecture/canonical-state-vs-observation.md + architecture/progressive-generation-and-resolution.md | consolidated |
| ## 5. Adapters | architecture/adapters.md | consolidated |
| ## 6. Time and orchestration | architecture/time-and-scheduling.md | consolidated |
| ## 7. Projection and resolution | architecture/progressive-generation-and-resolution.md | consolidated |
| ## 8. Statistical states and resolution | architecture/progressive-generation-and-resolution.md | consolidated |
| ## 9. Events | architecture/events-and-history.md | consolidated |
| ## 10. Provenance | architecture/provenance.md | consolidated |
| ## 11. Prototype path | vision/roadmap.md | consolidated |
| ## 12. Architectural boundary | architecture/modules-and-contracts.md + architecture/adapters.md | consolidated |
| ## 13. Snapshot semantics | architecture/snapshots.md | consolidated |
| ## 14. Future interface boundary | vision/interfaces.md | consolidated |
| ## 15. Obsidian-compatible Markdown as the first interface | vision/obsidian-atlas-vtt.md | consolidated |
| ## 16. Declarative run configuration and CLI | architecture/run-configuration-and-cli.md | consolidated |

### docs/SPECIFICATION.md

| Source heading | Destination | Treatment |
|---|---|---|
| # Worldloom Specification | architecture pages below | consolidated |
| ## Status | architecture pages below | verbatim |
| ## 1. World state | architecture/canonical-state-vs-observation.md | verbatim |
| ## 2. Module contract | architecture/modules-and-contracts.md | verbatim |
| ## 3. State exchange | architecture/modules-and-contracts.md | verbatim |
| ## 4. Time | architecture/time-and-scheduling.md | verbatim |
| ### 4.1 Simulation time | architecture/time-and-scheduling.md | verbatim |
| ### 4.2 Scheduling | architecture/time-and-scheduling.md | verbatim |
| ### 4.3 Execution context | architecture/time-and-scheduling.md | verbatim |
| ## 5. Events | architecture/events-and-history.md | verbatim |
| ## 6. Progressive generation and resolution | architecture/progressive-generation-and-resolution.md | verbatim |
| ### 6.1 Projection | architecture/progressive-generation-and-resolution.md | verbatim |
| ### 6.2 Resolution triggers | architecture/progressive-generation-and-resolution.md | verbatim |
| ### 6.3 Open representation question | architecture/progressive-generation-and-resolution.md + question notes | verbatim |
| ### 6.4 Open consistency questions | architecture/progressive-generation-and-resolution.md + question notes | verbatim |
| ## 7. Provenance | architecture/provenance.md | verbatim |
| ## 8. Reproducibility | process/experiments.md | verbatim |
| ## 9. External systems | architecture/adapters.md | verbatim |
| ## 10. Validation | process/development-workflow.md | verbatim |
| ## 11. Dependency-aware execution | architecture/modules-and-contracts.md | verbatim |
| ## 12. Canonical state versus derived observations | architecture/canonical-state-vs-observation.md | verbatim |
| ### 12.1 Canonical state | architecture/canonical-state-vs-observation.md | verbatim |
| ### 12.2 Derived observations | architecture/canonical-state-vs-observation.md | verbatim |
| ### 12.3 Promotion from observation to state | architecture/canonical-state-vs-observation.md | verbatim |
| ### 12.4 Module contracts | architecture/modules-and-contracts.md | verbatim |
| ### 12.5 Prototype interpretation | architecture/canonical-state-vs-observation.md | verbatim |
| ## 13. Snapshot semantics | architecture/snapshots.md | verbatim |

Normative fidelity rule: no sentence in the Requirements sections above may be paraphrased, merged, shortened, or silently reconciled in Phase 2.

### docs/DEVELOPMENT.md

| Source heading | Destination | Treatment |
|---|---|---|
| # Development Guide | process/development-workflow.md | consolidated |
| ## Principles | process/development-workflow.md | consolidated |
| ## Tests | process/development-workflow.md | consolidated |
| ## Active work and project memory | process/development-workflow.md + current.md | consolidated |
| ## Feature branch workflow | process/development-workflow.md | consolidated |
| ## Adding a module | process/development-workflow.md + architecture/modules-and-contracts.md | consolidated |
| ## Experiments | process/experiments.md | consolidated |
| ## AI-assisted development | process/agent-rules.md | consolidated |
| ## Pull request workflow | process/development-workflow.md | consolidated |

### docs/EXPERIMENTS.md

| Source heading | Destination | Treatment |
|---|---|---|
| # Experiment Conventions | experiments/README.md | consolidated |
| ## Progressive-resolution provenance experiment | experiments/progressive-resolution-provenance.md | verbatim |
| ### Question | experiments/progressive-resolution-provenance.md | verbatim |
| ### Method and result | experiments/progressive-resolution-provenance.md | verbatim |
| ### Interpretation | experiments/progressive-resolution-provenance.md | verbatim |
| ### Follow-up paths | experiments/progressive-resolution-provenance.md | verbatim |
| ## Raster terrain adapter causal integration experiment | experiments/raster-terrain-adapter.md | verbatim |
| ### Question | experiments/raster-terrain-adapter.md | verbatim |
| ### Implementation | experiments/raster-terrain-adapter.md | verbatim |
| ### Configuration | experiments/raster-terrain-adapter.md | verbatim |
| ### Measurements / results | experiments/raster-terrain-adapter.md | verbatim |
| ### Interpretation | experiments/raster-terrain-adapter.md | verbatim |
| ### Limitations | experiments/raster-terrain-adapter.md | verbatim |
| ## Spatial field semantics experiment | experiments/spatial-field-semantics.md | verbatim |
| ### Question | experiments/spatial-field-semantics.md | verbatim |
| ### Candidate representation | experiments/spatial-field-semantics.md | verbatim |
| ### Causal test | experiments/spatial-field-semantics.md | verbatim |
| ### Interpretation | experiments/spatial-field-semantics.md | verbatim |
| ## End-to-end GIS export experiment | experiments/gis-export.md | verbatim |
| ### Question | experiments/gis-export.md | verbatim |
| ### Method | experiments/gis-export.md | verbatim |
| ### Measurements / results | experiments/gis-export.md | verbatim |
| ### Interpretation | experiments/gis-export.md | verbatim |
| ## Declarative run configuration and CLI experiment | experiments/run-configuration-cli.md | verbatim |
| ### Question | experiments/run-configuration-cli.md | verbatim |
| ### Method | experiments/run-configuration-cli.md | verbatim |
| ### Measurements / results | experiments/run-configuration-cli.md | verbatim |
| ### Interpretation | experiments/run-configuration-cli.md | verbatim |
| ## Canonical-state data routing and propagation experiment | experiments/canonical-state-routing.md | verbatim |
| ### Question | experiments/canonical-state-routing.md | verbatim |
| ### Method | experiments/canonical-state-routing.md | verbatim |
| ### Measurements / results | experiments/canonical-state-routing.md | verbatim |
| ### Interpretation | experiments/canonical-state-routing.md | verbatim |
| ### Scope | experiments/canonical-state-routing.md | verbatim |
| ## Competing canonical-state producers experiment | experiments/competing-producers.md | verbatim |
| ### Question | experiments/competing-producers.md | verbatim |
| ### Method | experiments/competing-producers.md | verbatim |
| ### Measurements / results | experiments/competing-producers.md | verbatim |
| ### Interpretation | experiments/competing-producers.md | verbatim |
| ### Scope | experiments/competing-producers.md | verbatim |
| ## Invalidation and reconciliation experiment | experiments/invalidation-reconciliation.md | verbatim |
| ### Question | experiments/invalidation-reconciliation.md | verbatim |
| ### Method | experiments/invalidation-reconciliation.md | verbatim |
| ### Measurements / results | experiments/invalidation-reconciliation.md | verbatim |
| ### Interpretation | experiments/invalidation-reconciliation.md | verbatim |
| ### Scope | experiments/invalidation-reconciliation.md | verbatim |
| ## Canonical output ownership experiment | experiments/canonical-output-ownership.md | verbatim |
| ### Question | experiments/canonical-output-ownership.md | verbatim |
| ### Pass/fail criteria | experiments/canonical-output-ownership.md | verbatim |
| ### Falsification condition | experiments/canonical-output-ownership.md | verbatim |
| ### Results | experiments/canonical-output-ownership.md | verbatim |
| ### Interpretation | experiments/canonical-output-ownership.md | verbatim |
| ### Limitations and open questions | experiments/canonical-output-ownership.md + question notes | verbatim |
| ### Scope | experiments/canonical-output-ownership.md | verbatim |
| ## Question-derived identity and address-keyed randomness integration experiment | experiments/question-derived-identity-address-randomness.md | verbatim |
| ### Question | experiments/question-derived-identity-address-randomness.md | verbatim |
| ### Pass/fail criteria | experiments/question-derived-identity-address-randomness.md | verbatim |
| ### Method | experiments/question-derived-identity-address-randomness.md | verbatim |
| ### Configuration | experiments/question-derived-identity-address-randomness.md | verbatim |
| ### Measurements / results | experiments/question-derived-identity-address-randomness.md | verbatim |
| ### Interpretation | experiments/question-derived-identity-address-randomness.md | verbatim |
| ### Retained as provisional for this experiment, with rationale | experiments/question-derived-identity-address-randomness.md | verbatim |
| ### Not decided | experiments/question-derived-identity-address-randomness.md + question notes | verbatim |
| ### Limitations | experiments/question-derived-identity-address-randomness.md | verbatim |
| ### Scope | experiments/question-derived-identity-address-randomness.md | verbatim |

### docs/GLOSSARY.md

| Source heading | Destination | Treatment |
|---|---|---|
| # Worldloom Glossary | devwiki/glossary.md | consolidated |
| ## Canonical state | devwiki/glossary.md#canonical-state | verbatim |
| ## Derived observation | devwiki/glossary.md#derived-observation | verbatim |
| ## Projection | devwiki/glossary.md#projection | verbatim |
| ## Provisional information | devwiki/glossary.md#provisional-information | verbatim |
| ## Progressive generation | devwiki/glossary.md#progressive-generation | verbatim |
| ## Field | devwiki/glossary.md#field | verbatim |
| ## Entity | devwiki/glossary.md#entity | verbatim |
| ## Event | devwiki/glossary.md#event | verbatim |
| ## Relationship | devwiki/glossary.md#relationship | verbatim |
| ## Constraint | devwiki/glossary.md#constraint | verbatim |
| ## Provenance | devwiki/glossary.md#provenance | verbatim |
| ## Resolution | devwiki/glossary.md#resolution | verbatim |
| ## Module contract | devwiki/glossary.md#module-contract | verbatim |
| ## InputSpec | devwiki/glossary.md#inputspec | verbatim |
| ## OutputSpec | devwiki/glossary.md#outputspec | verbatim |
| ## DataKind | devwiki/glossary.md#datakind | verbatim |
| ## Observation boundary | devwiki/glossary.md#observation-boundary | verbatim |
| ## Snapshot | devwiki/glossary.md#snapshot | verbatim |
| ## Simulation context | devwiki/glossary.md#simulation-context | verbatim |
| ## World state | devwiki/glossary.md#world-state | verbatim |
| ## Dependency order | devwiki/glossary.md#dependency-order | verbatim |
| ## Interface layer | devwiki/glossary.md#interface-layer | verbatim |
| ## Adapter | devwiki/glossary.md#adapter | verbatim |
| ## State versus observation | devwiki/glossary.md#state-versus-observation | verbatim |

### docs/INTERFACES.md

| Source heading | Destination | Treatment |
|---|---|---|
| # Worldloom Interface and Interaction Vision | vision/interfaces.md | consolidated |
| ## Status | vision/interfaces.md | consolidated |
| ## 1. The core idea | vision/interfaces.md | consolidated |
| ## 2. Primary long-term interfaces | vision/interfaces.md | consolidated |
| ### 2.1 World guide / wiki | vision/interfaces.md | consolidated |
| ### 2.2 Interactive GIS | vision/interfaces.md | consolidated |
| ### 2.3 Natural-language world interface | vision/interfaces.md | consolidated |
| ### 2.4 Timeline / historical explorer | vision/interfaces.md | consolidated |
| ### 2.5 Character / observer perspective | vision/interfaces.md | consolidated |
| ### 2.6 GM / referee dashboard | vision/interfaces.md | consolidated |
| ### 2.7 Gazetteer / traveller view | vision/interfaces.md | consolidated |
| ### 2.8 Author research interface | vision/interfaces.md | consolidated |
| ### 2.9 Consistency / continuity inspector | vision/interfaces.md | consolidated |
| ### 2.10 Scenario / counterfactual explorer | vision/interfaces.md | consolidated |
| ### 2.11 Observer / "god's-eye" visualisation | vision/interfaces.md | consolidated |
| ### 2.12 Eventual 3D client | vision/interfaces.md | consolidated |
| ## 3. Shared interface primitives | vision/interfaces.md | consolidated |
| ### World state at time T | vision/interfaces.md | consolidated |
| ### Provenance / "why is this true?" | vision/interfaces.md | consolidated |
| ### Multiple knowledge levels | vision/interfaces.md | consolidated |
| ### Controlled mutation | vision/interfaces.md | consolidated |
| ## 4. Architectural implications | vision/interfaces.md | consolidated |
| ## 5. Relationship to current work | vision/interfaces.md | consolidated |
| ## 6. First concrete interface: Obsidian-compatible Markdown | vision/obsidian-atlas-vtt.md | consolidated |
| ### What this means | vision/obsidian-atlas-vtt.md | consolidated |
| ### Atlas-VTT compatibility | vision/obsidian-atlas-vtt.md | consolidated |
| ### Open design questions | questions/obsidian-markdown-interface.md | consolidated |

Out-of-scope guard: this migration will not design, scaffold, or specify the eventual Worldloom world-vault schema. The vision page may state that Obsidian-compatible Markdown is a future/first interface boundary and may preserve the existing non-normative direction, but folder layout, frontmatter/property vocabulary, identifier mapping, generated-content markers, provenance syntax, uncertainty representation, and mutation semantics remain out of scope and open.

### docs/REFERENCE_BACKLOG.md

| Source heading | Destination | Treatment |
|---|---|---|
| # Worldloom Research and Reference Backlog | references/README.md | consolidated |
| ## Status | references/README.md | consolidated |
| ## 1. Geography, terrain, GIS, and spatial processes | references/geography-terrain-gis.md | verbatim |
| ## 2. Agent-based, social, and population modelling | references/agent-social-population.md | verbatim |
| ## 3. Environmental and biological process references | references/environmental-biological.md | verbatim |
| ## 4. Language and culture research backlog | references/language-culture.md | verbatim |
| ## 5. Procedural generation and constraint references | references/procedural-constraints.md | verbatim |
| ## 6. Reference policy | references/README.md | verbatim |
| ## 7. Relationship to architecture | references/README.md | verbatim |

### docs/ROADMAP.md

| Source heading | Destination | Treatment |
|---|---|---|
| # Worldloom Long-Term Roadmap | vision/roadmap.md | consolidated |
| ## Purpose | vision/roadmap.md | consolidated |
| ## 1. Core objective | vision/roadmap.md | consolidated |
| ## 2. Domains to support | vision/roadmap.md | consolidated |
| ## 3. Integration-first philosophy | vision/roadmap.md | consolidated |
| ## 4. Canonical world model | vision/roadmap.md | consolidated |
| ## 5. Multi-scale simulation | vision/roadmap.md | consolidated |
| ## 6. Feasibility-driven prototype progression | vision/roadmap.md | consolidated |
| ## 7. GIS and external-tool interoperability | vision/roadmap.md | consolidated |
| ## 8. Progressive generation experiments | vision/roadmap.md | consolidated |
| ## 9. Experiments and validation | vision/roadmap.md | consolidated |
| ## 10. Agent-assisted development | process/agent-rules.md | consolidated |
| ## 11. Success criterion | vision/roadmap.md | consolidated |
| ## 12. Future world interfaces | vision/interfaces.md | consolidated |
| ## 13. First concrete interface: Obsidian-compatible Markdown | vision/obsidian-atlas-vtt.md | consolidated |
| ### Atlas-VTT compatibility | vision/obsidian-atlas-vtt.md | consolidated |

### docs/COPILOT_CONTEXT.md

| Source heading | Destination | Treatment |
|---|---|---|
| # Copilot Context: Worldloom Big Picture | index.md + process/agent-rules.md | consolidated |
| ## Mission | index.md | consolidated |
| ## Architectural consequence | architecture/canonical-state-vs-observation.md + architecture/modules-and-contracts.md | consolidated |
| ## Progressive world generation | architecture/progressive-generation-and-resolution.md | consolidated |
| ## Integration philosophy | architecture/adapters.md + references/README.md | consolidated |
| ## Storytelling perspective | vision/interfaces.md + vision/gm-campaign-continuity.md | consolidated |
| ## Working rule for agents | process/agent-rules.md | consolidated |
| ## First concrete user interface | vision/obsidian-atlas-vtt.md | consolidated |

### docs/CAMPAIGN DIRECTION.md

| Source heading | Destination | Treatment |
|---|---|---|
| # Worldloom Direction Note: GM-Facing Campaign Continuity | vision/gm-campaign-continuity.md | consolidated |
| ## Status | vision/gm-campaign-continuity.md | verbatim |
| ## 1. Motivation | vision/gm-campaign-continuity.md | verbatim |
| ## 2. Primary use case: a GM continuity engine | vision/gm-campaign-continuity.md | verbatim |
| ## 3. Target experience (north star) | vision/gm-campaign-continuity.md | verbatim |
| ## 4. Campaign use: PCs as a source of events | vision/gm-campaign-continuity.md | verbatim |
| ### 4.1 Consistency and the "hand of god" | vision/gm-campaign-continuity.md | verbatim |
| ### 4.2 Information propagation and reactions | vision/gm-campaign-continuity.md | verbatim |
| ### 4.3 Technology and magic | vision/gm-campaign-continuity.md | verbatim |
| ## 5. Two interleaved eras (first planned campaign) | vision/gm-campaign-continuity.md | verbatim |
| ## 6. Player knowledge model | vision/gm-campaign-continuity.md | verbatim |
| ### 6.1 Knowledge record shape | vision/gm-campaign-continuity.md | verbatim |
| ## 7. Resolution principles | vision/gm-campaign-continuity.md | verbatim |
| ## 8. Concrete gaps in the current code | vision/gm-campaign-continuity.md | verbatim |
| ## 9. Suggested experiment order | vision/gm-campaign-continuity.md | verbatim |
| ## 10. Guidance for implementation agents | process/agent-rules.md | consolidated |
| ## 11. Suggested additions to TODO.md | current.md + question notes | consolidated |

The campaign-direction note is explicitly non-normative and will remain marked as vision. It must not promote its [Proposal] items into architecture/specification merely by migration. The uploaded campaign-direction copy carries the same proposed/non-normative status and tagging scheme.

### README.md

| Source heading | Destination | Treatment |
|---|---|---|
| # Worldloom | index.md | consolidated |
| ## Design goals | index.md | consolidated |
| ## Initial structure | index.md + README update in Phase 4 | rewritten |
| ## Status | index.md | consolidated |
| ## Running a configured simulation | architecture/run-configuration-and-cli.md | consolidated |

### AGENTS.md

| Source heading | Destination | Treatment |
|---|---|---|
| # Agent Instructions | AGENTS.md (new slim form) | rewritten |
| ## Before changing architecture | process/agent-rules.md + root read order | consolidated |
| ## Development principles | process/agent-rules.md | consolidated |

The new root AGENTS.md is intentionally not a verbatim copy. It will be <=60 lines and will state the project, core rules, required read order (devwiki/index.md, then devwiki/current.md, then pages as needed), and the duty to append to devwiki/log.md.

### TODO.md

| Source heading | Destination | Treatment |
|---|---|---|
| # Worldloom TODO | current.md | rewritten |
| ## Now | current.md | consolidated |
| ## Later | current.md + roadmap/vision links | consolidated |
| ## Questions / Decisions Needed | current.md + question notes | consolidated |

The active queue is not history. Completed items will not be copied into current.md merely for preservation; historical evidence remains in Git/experiment notes.

### .github/copilot-instructions.md

| Source heading | Destination | Treatment |
|---|---|---|
| # Worldloom — Copilot Instructions | AGENTS.md | rewritten |
| ## Read this first | AGENTS.md | consolidated |
| ## Testing is mandatory | process/development-workflow.md | consolidated |
| ## Architectural principles | process/agent-rules.md + architecture pages | consolidated |
| ### The loom, not every thread | architecture/adapters.md | consolidated |
| ### Canonical world state | architecture/canonical-state-vs-observation.md | consolidated |
| ### Replaceable modules | architecture/modules-and-contracts.md | consolidated |
| ### Time and events | architecture/time-and-scheduling.md + architecture/events-and-history.md | consolidated |
| ### Uncertainty becomes history | architecture/progressive-generation-and-resolution.md | consolidated |
| ### Provenance matters | architecture/provenance.md | consolidated |
| ### Interfaces are projections, not separate worlds | vision/interfaces.md | consolidated |
| ### Existing systems first | architecture/adapters.md + references/README.md | consolidated |
| ### Keep experiments separate | process/experiments.md | consolidated |
| ## Development discipline | process/agent-rules.md | consolidated |

The final .github/copilot-instructions.md, if retained, will contain only a one-line pointer to AGENTS.md, as required.

## Planned question inventory

These are the open questions found in TODO, SPECIFICATION, experiment open lists, and interface vision. Phase 2 should deduplicate them rather than create one note per repeated wording.

| Question note | Sources |
|---|---|
| questions/provisional-state-representation.md | SPECIFICATION 6.3; architecture section 4/8 |
| questions/invalidation-reconciliation.md | SPECIFICATION 6.4; TODO; progressive-resolution/invalidation experiments |
| questions/projection-storage-and-reproducibility.md | SPECIFICATION 6.4; TODO |
| questions/projection-coherence.md | SPECIFICATION 6.4; TODO/roadmap progressive-generation work |
| questions/observation-version-history.md | TODO; invalidation experiment |
| questions/source-fingerprint-provenance.md | campaign direction; invalidation experiment |
| questions/deterministic-seeding.md | TODO; provenance experiment; identity/randomness experiment |
| questions/spatial-data-model.md | TODO; raster/spatial-field experiments |
| questions/gis-interchange.md | raster/GIS export experiments; TODO |
| questions/crs-and-spatial-reference.md | raster/spatial-field/GIS export experiments |
| questions/spatial-indexing-and-query.md | spatial-field experiment |
| questions/vector-spatial-data.md | spatial-field/GIS export experiments |
| questions/large-spatial-data.md | raster/GIS export experiments |
| questions/external-source-identity.md | TODO; raster adapter experiment |
| questions/adapted-data-semantic-status.md | raster adapter experiment |
| questions/derived-output-storage.md | TODO; provenance experiment; progressive-generation spec |
| questions/external-specialist-interface.md | TODO; architecture/roadmap/reference policy |
| questions/canonical-authority-boundary.md | TODO; SPECIFICATION 12; architecture state model |
| questions/snapshot-branching.md | TODO; interface vision; campaign direction |
| questions/output-ownership-and-arbitration.md | competing-producers and ownership experiments |
| questions/refines-and-overlay-semantics.md | ownership experiment |
| questions/overlay-consumption.md | ownership experiment |
| questions/validation-architecture.md | TODO; multiple experiments |
| questions/identifier-address-model.md | TODO; ownership and identity experiments |
| questions/entity-id-digest-length.md | TODO; identity experiment |
| questions/entity-alias-uniqueness.md | TODO; identity experiment |
| questions/address-unicode-normalisation.md | TODO; identity experiment |
| questions/world-seed-identity-scope.md | TODO; identity experiment |
| questions/randomness-keying-policy.md | TODO; identity experiment |
| questions/randomness-and-execution.md | identity experiment |
| questions/random-generation-provenance.md | identity experiment |
| questions/branch-and-commit-semantics.md | campaign direction; TODO |
| questions/event-participants-witnesses-causality.md | campaign direction |
| questions/event-triggered-scheduling.md | campaign direction; architecture; experiment open lists |
| questions/knowledge-records.md | campaign direction |
| questions/fixed-point-repair.md | campaign direction |
| questions/capacity-comparability.md | campaign direction |
| questions/atlas-vtt-support.md | interfaces vision |
| questions/obsidian-markdown-interface.md | interfaces vision |
| questions/configuration-schema-and-validation.md | CLI experiment |
| questions/plugin-discovery.md | CLI experiment |
| questions/multi-module-composition.md | CLI/routing/ownership experiments |
| questions/configuration-versioning.md | CLI experiment |
| questions/temporal-cadence-staleness.md | routing experiment |
| questions/general-routing.md | routing experiment |

Some of these are intentionally grouped only at the question-note level; Phase 2 must check for exact duplicate meanings before creating all of them.

## Contradictions and tensions to preserve explicitly

No source contradiction will be silently resolved during migration. The following tensions require explicit treatment:

1. **Current scheduler vs future event triggering.** SPECIFICATION explicitly says the current scheduler does not require event-triggered scheduling, while architecture/roadmap/campaign direction identify event-triggered reactions as future work. This is a staged distinction, not permission to rewrite the current requirement.
2. **Canonical output ownership vs historical last-writer-wins experiment.** The competing-producers experiment records historical last-writer-wins behaviour; the later ownership experiment documents a provisional EXCLUSIVE policy. Both results must remain intact and clearly scoped to their experiments.
3. **Ownership experiment vs final architecture.** The ownership experiment explicitly calls its protocol provisional and leaves validation, identifier, overlay consumption, and REFINES semantics open. It must not be promoted into normative architecture.
4. **Obsidian world-vault direction vs this development wiki.** Existing architecture/roadmap/interface documents call the eventual user-facing Obsidian-compatible world vault the first concrete Worldloom interface. The new devwiki/ is a development wiki and is not that vault. The migration must not design or scaffold the eventual world-vault schema.
5. **Campaign-direction proposals vs normative architecture.** The campaign note contains owner decisions, proposals, and open questions but is explicitly non-normative. Proposals remain proposals after migration.
6. **Identity/validation separation.** Several experiment notes mention both identifier and validation questions. Existing project direction explicitly keeps those decisions separate; the migration will not combine them into one architectural decision.
7. **Experiment verification scope.** Experiment notes contain historical verification claims tied to specific commits/runs. They are historical evidence, not claims about Phase 3 verification of the migrated wiki.

## Consolidations recorded

These are intentional non-normative deduplications planned for Phase 2:

- docs/COPILOT_CONTEXT.md + .github/copilot-instructions.md agent-orientation material -> process/agent-rules.md and root AGENTS.md.
- docs/DEVELOPMENT.md AI/branch/PR guidance + agent guidance repeated in campaign direction, roadmap, and Copilot instructions -> process/development-workflow.md and process/agent-rules.md.
- README.md design goals/status + Copilot mission -> index.md.
- docs/ROADMAP.md interface sections + docs/INTERFACES.md -> vision/interfaces.md and vision/obsidian-atlas-vtt.md.
- Obsidian/Atlas-VTT compatibility repeated in ARCHITECTURE, ROADMAP, INTERFACES, and COPILOT_CONTEXT -> vision/obsidian-atlas-vtt.md; no world-vault schema is designed.
- Canonical-state/observation language repeated in ARCHITECTURE, SPECIFICATION, GLOSSARY, COPILOT_CONTEXT, and Copilot instructions -> architecture/canonical-state-vs-observation.md plus glossary links.
- Progressive-generation language repeated in ARCHITECTURE, SPECIFICATION, ROADMAP, COPILOT_CONTEXT, and GLOSSARY -> architecture/progressive-generation-and-resolution.md plus glossary links.
- Adapter/integration-first language repeated in ARCHITECTURE, ROADMAP, COPILOT_CONTEXT, Copilot instructions, and reference policy -> architecture/adapters.md plus references/README.md.
- Experiment conventions repeated in DEVELOPMENT, ROADMAP, Copilot instructions, and EXPERIMENTS -> process/experiments.md plus experiments/README.md.
- Long-term interface descriptions repeated in ROADMAP, INTERFACES, COPILOT_CONTEXT, and ARCHITECTURE -> vision pages.
- Current TODO questions repeated by experiment “Still open”/“Not decided” lists -> individual question notes with links from each source experiment.
- Root TODO active-work process duplicated in DEVELOPMENT -> current.md plus process/development-workflow.md.

## Items with no obvious home

These require either a deliberate home or explicit omission decision in Phase 2:

- docs/CAMPAIGN DIRECTION.md copyright caution and Mistborn-specific first-campaign details: planned for the non-normative vision/gm-campaign-continuity.md, but no setting-specific content should be expanded.
- Campaign-direction proposed mechanisms for fixed points, knowledge records, repairs, causal event links, and salience: planned as vision/questions/experiment links only; none are architecture requirements.
- Historical experiment details tied to closed/older branches or specific commits: retained in their experiment notes because they are evidence, not active work.
- The README's exact “Architecture v0.1 — foundation only” status wording: planned for index as a current status statement, but it must be checked against the current repository state during Phase 2 rather than silently modernised.
- docs/GLOSSARY.md is one source document but its terms are cross-cutting; all terms will remain in one glossary as required rather than becoming separate pages.
- The eventual world-vault schema is intentionally **no home** in devwiki/; it is out of scope.

## Code, test, workflow, and README path-reference check

The repository tree contains src/, tests/, .github/workflows/, README.md, and the documentation files listed above.

Targeted scans of all listed source/test files were performed in three batches for the documentation path names and root queue/context names. **No matches were found in src/ or tests/.** A scan of .github/workflows/tests.yml also found no documentation path references.

Known documentation-path references that will need Phase 4 updates are in:
- README.md;
- AGENTS.md;
- .github/copilot-instructions.md;
- docs/DEVELOPMENT.md;
- docs/COPILOT_CONTEXT.md;
- other documentation files themselves.

No source/test path edits are therefore currently planned. If Phase 2/3 discovers a missed reference, it must be added to the migration map before any path is changed.

## Phase 1 boundary

This commit intentionally contains **only** devwiki/migration-map.md.

Phase 2 must not begin until the project owner approves this map. No old documentation is deleted in Phase 1, no source/test files are changed, no CI/plugin/sync configuration is changed, and the pull request remains draft.
