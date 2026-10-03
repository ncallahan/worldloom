---
type: vision
status: vision
summary: Campaign continuity direction; proposals remain explicitly unadopted.
related: ["[[vision/interfaces]]", "[[questions/identifier-address-model]]"]
---

# Worldloom Direction Note: GM-Facing Campaign Continuity

## Status

**Proposed. Not normative.** This note records a design discussion between the project owner and an AI assistant. It captures intended direction and candidate mechanisms so that implementation agents do not have to improvise them.

Per `AGENTS.md`, nothing here silently redefines the architecture. Items are tagged:

- **[Owner decision]**: stated by the project owner as intent or preference.
- **[Proposal]**: a candidate mechanism suggested in discussion. It needs an experiment before it becomes architecture.
- **[Open]**: an unresolved question.

Promotion into `ARCHITECTURE.md` or `SPECIFICATION.md` should follow the normal experiment-first workflow in `DEVELOPMENT.md`.

---

## 1. Motivation

**[Owner decision]** Worldloom is both a *tool* and a *toy*:

- **Tool:** a persistent, trustworthy world for running tabletop RPG campaigns and supporting fiction.
- **Toy:** a simulation that is satisfying to poke at, and that can be left running to see what emerges. Unattended runs should leave a readable history (a chronicle of events), not just a final state.

Both goals need the same properties: determinism and seeds, provenance, snapshots, and a cheap path to extend with new modules. The playful side should be protected: occasionally run the pipeline just to see what comes out, with no experiment attached.

## 2. Primary use case: a GM continuity engine

**[Owner decision]** Worldloom is primarily a **GM (DM) tool, not a player tool.**

- The GM is the **only writer** of canonical state. Players never resolve facts.
- Player-facing access, if any, is a **read-only knowledge projection** limited to what their characters would know, plus general knowledge that helps them place their character in the world.
- The value is backstage: when a player asks an offhand question, the GM can get a grounded answer quickly, and can see the consequences of past deeds that the players may never notice.

**[Owner decision]** Most players are expected not to dig into history. So provenance trails need to be **correct and available on demand**, not polished for frequent exploration.

## 3. Target experience (north star)

**[Owner decision]** The end system should support this kind of zoom:

> Full world map → region → town → a single person, with answers about their daily activities, who they've spoken to, and what they are looking forward to.

and this kind of historical drill-down:

> Notice a culture being wiped out → follow what happened → find the political fight over it → ask who tried to protect it, why outsiders joined them, and why they failed with the resources they had.

Both the discovery of stories (wandering) and system-surfaced stories (flagging pressure points) are wanted.

**[Owner decision]** People are **consistent characters resolved on demand**, not richly simulated agents. Simulation operates on town-scale forces (economy, factions, scarcity, grudges, seasons). Characters are found *within* those forces.

## 4. Campaign use: PCs as a source of events

**[Owner decision]** A campaign is set in an interesting situation in the world. The GM can state "the characters did X" (killed someone, razed half a village, kept an item from a villain's minions) and get a **realistic, consistent reaction** from the rest of the world. Questions to answer include whether consequences stay local and how events look from the PCs' perspective.

**[Owner decision]** Items have histories (chains of custody), and entities may seek them.

**[Owner decision]** Technology and magical effects should be explorable for their consequences on social structures (informally, "SimMiddleEarth").

### 4.1 Consistency and the "hand of god"

**[Owner decision]** The world must **always resolve to a consistent outcome around PC actions.** Where a PC action contradicts a canonical future, the system applies a repair ("you broke time; here is the hand of the gods putting you back into something that works, but still allows the future to occur").

**[Owner decision]** Fixed points are **truly fixed** for Cosmere-style play (the owner's next real campaign). For more generic campaigns, the preferred feel is Terminator-style: the outcome is fixed, but how, why, and when vary with the protagonists' actions.

**[Proposal]** Model both as one mechanism: a **fixed point is a constraint on a destination, with declared degrees of freedom** (which of date, cause, participants, location may vary).

- Terminator-style: pin the outcome; leave most freedoms open.
- Cosmere-style: pin laws and key facts; allow very little to vary.

**[Proposal]** Repairs are **explicit, visible events**, never silent rewrites. A repair records: the contradiction that triggered it, the facts it changed, and the justification. Repairs prefer the smallest change that preserves the pinned destination (substitute a person, delay an event, reroute the cause).

**[Proposal]** The system **proposes** candidate repairs; the **GM selects** one. Authority stays with the GM.

**[Proposal]** If no repair satisfies the pinned constraints under their allowed freedoms, the system must return a **loud, explicit "no valid repair exists"** result. It must not fudge. The GM then loosens a freedom or adds an in-world mechanism.

**[Proposal]** Distinguish **pivotal** facts (fixed points the world bends around) from **incidental** facts (recomputable). Marking this is a small authoring act and tells the repair pass what it may change.

### 4.2 Information propagation and reactions

**[Proposal]** "Does it stay local?" is an information-propagation problem. The world reacts when news arrives (by route, at travel speed, distorted en route), not at the instant of the deed. What the world *believes* happened is a projection distinct from what happened, and the PCs' reputation may differ from their deeds. This motivates **event-triggered scheduling** (currently future work): reactions fire when a belief changes.

Actors act on **beliefs**, not truth (for example, seekers of an item act on where they believe it is).

### 4.3 Technology and magic

**[Proposal]** Treat technology and magic as **modifiers on the coarse forces** (productivity, military capacity, communication speed, who can do what) rather than special cases. Their consequences then flow through the same machinery that explains ordinary history.

**[Proposal]** For capacity-based explanations ("why did they lose with what they had?"), capacity must be a **comparable quantity** so that explanations are derived rather than invented.

## 5. Two interleaved eras (first planned campaign)

**[Owner decision]** The first planned campaign is Mistborn-based: two sets of characters in two eras roughly three centuries apart, **interleaved** (a few levels of advancement in one era, then the other), for roughly **five cycles**. The owner recalls about three events that must occur in the first era, plus the book canon events. The owner has not finished reading the source material, so avoid spoilers unless asked.

**[Owner decision]** Ripples from the earlier party's actions should show up automatically for their later counterparts.

**[Proposal]** Structure:

- Era 2 is a **continuation of the Era 1 branch**: take the Era 1 end state, coarsely simulate the intervening centuries, and resolve Era 2 locally where its party plays.
- What Era 2 *believes* about Era 1 (legend, religion, institutions) is a **degraded belief projection**, separate from what happened. Legends are a cheap way to add flavour without constraining Era 1.
- Because play is interleaved, **causality runs both ways.** Era 2 resolutions become **pins on Era 1's unplayed future**, each with declared degrees of freedom. The repair pass must satisfy constraints from both ends.
- Each Era 1 stint ends with a **commit point**: its deeds lock into canonical history. Everything beyond the latest commit remains projected until played.
- Resolve Era 2 **lazily**. Every detail pinned early reduces what Era 1 players can still do.
- Each Era 2 fact's provenance must record which Era 1 facts or projections it rests on (see section 8, item 1).

**Copyright caution:** encode only the structure and rules needed for the table's own campaign, hand-authored in a small slice. Do not attempt to ingest a copyrighted setting wholesale. Setting rules (such as magic systems) should enter through ordinary module contracts, which also tests whether a rule-bound magic system can plug in without special cases.

## 6. Player knowledge model

**[Owner decision]** Players never resolve facts. Any player access is limited to character knowledge and general knowledge.

**[Proposal]** Two tiers:

- **General knowledge:** what anyone raised in a given culture, region, and era would know.
- **Character knowledge:** what a specific person has plausibly learned.

**[Proposal]** The player view must be **built up from knowledge records, not filtered down from canon.** Starting from canon and hiding secrets makes every new fact a potential leak; starting from what a character believes and adding deliberately is safe by default. Character knowledge may be **wrong** (distorted legends, rumours); that is a feature.

**[Proposal]** In the Obsidian interface: one full GM vault, and generated per-character or per-party vaults containing only approved knowledge records.

### 6.1 Knowledge record shape

**[Owner decision]** The owner prefers eventually **system-proposed, GM-approved** knowledge updates, while accepting that a **hand-curated first iteration** is easier and still very useful.

**[Proposal]** Design the data so proposals need no migration later, only a new writer:

- A record does not know who wrote it. Fields: `subject` (the character), `content_ref` (an ID of a fact, event, or rumour), `source` (witnessed, hearsay, legend, taught), `acquired` (session and/or simulation time), `status`, `author`.
- `status` exists from day one (`proposed`, `approved`, `rejected`). Hand-written records are created `approved` with `author: GM`.
- Records **reference** canon rather than copying it, with an optional "as the character believes it" override for distorted or wrong beliefs.
- Only `approved` records appear in player-facing views.

**[Proposal]** Later, "witnessed" proposals become a query over event participant/witness data (see section 8, item 3). Start with **presence only**; plausibility modelling (distance, language, comprehension) is a later refinement and should not be built prematurely. Secondhand knowledge (rumours, legends) remains hand-written, since that is where GM judgement adds most.

## 7. Resolution principles

**[Proposal]** **Order-independent resolution:** derive a character's seed from the world seed plus their stable ID, so the same character resolves identically regardless of when or in what order they are examined. Once resolved, facts are written to canonical state and stay fixed. This addresses part of the "per-module seeds" open question.

**[Proposal]** **Coarse constraints on fine detail:** town-level totals (population, occupations) and coarse history (a culture vanished by year N) act as constraints. Detail generated later must satisfy them. Going down in zoom is easy; going down without contradicting what was seen from above is the core difficulty.

**[Proposal]** **Tensions as first-class coarse objects** (a debt, a rivalry, a failing well) that drive both history and the characters discovered within it, and make a town's trajectory legible without simulating individuals.

**[Proposal]** **Historical causation:** extend provenance from data lineage to event causation. Events need causal links to other events; actors need recorded stakes and capacities at the relevant time.

**[Proposal]** A **salience pass** over the event log can flag extinctions, collapses, and reversals as places worth drilling into.

## 8. Concrete gaps in the current code

These follow from the above and are grounded in the present implementation. They are candidates for small experiments, not approved tasks.

1. **Provenance does not retain source fingerprints.** Already shown by the invalidation experiment. Detecting that a resolved fact rests on a changed upstream value (essential for repairs and for Era 2 → Era 1 dependencies) needs the fingerprint of each input recorded at resolution time.
2. **Competing producers.** Last-writer-wins on `WorldState.fields` is unsafe once multiple processes (including repairs and cross-era resolutions) can write related values. Decide ownership or arbitration before building on shared field names.
3. **`Event` lacks participants/witnesses.** It currently has `kind`, `time`, and a `data` dict. A small addition (participant and witness identifiers, plus optional causal links to other events) supports knowledge records and causal explanation.
4. **No event-triggered scheduling.** Needed for belief-driven reactions.
5. **No branching.** Campaign branches and counterfactual comparison depend on versioned snapshots and branch semantics (already listed as future work).
6. **No belief/knowledge representation.** Knowledge records (section 6.1) are the first concrete form this could take.
7. **No constraint/fixed-point representation.** Needed for pins with degrees of freedom.

## 9. Suggested experiment order

Each should be the smallest experiment that answers one question, following `EXPERIMENTS.md` conventions.

1. **Progressive resolution coherence.** A town whose population is a distribution; resolve one person, then another; verify aggregates hold and that nothing else changes. Includes order-independent seeding.
2. **Source fingerprints in provenance.** Resolve a fact from an observation, change the observation, and detect staleness from live state alone.
3. **Item chain of custody.** An item as an entity whose history is derived from events; one crossing a notional era boundary.
4. **Knowledge records.** Characters as entities, hand-written records with `status`, a generated view containing only approved records, and a test that unapproved or unreferenced canon never appears.
5. **Fixed point with degrees of freedom.** A pinned outcome, a PC deed that breaks the planned path, a repair proposal that reaches the same outcome by a different route, and a deliberately unrepairable case that returns a clear failure.
6. **Five-cycle toy.** A scripted two-era run with toy deeds, pins from both eras, and a commit point per cycle, to see whether the constraint model holds under interleaving.

## 10. Guidance for implementation agents

- Treat this note as **direction, not requirements.** Surface choices that affect data shape before committing.
- Preserve the **GM-as-sole-writer** principle. Do not add any player write path.
- Preserve the distinction between canonical state, derived observations, and **beliefs**. Belief is information *about* the world, not a competing world.
- Never implement silent repair. Every change forced by a contradiction must be a recorded, GM-visible event.
- Do not build perception/plausibility simulation, a general constraint solver, or a player-facing explorer unless explicitly selected as active work.
- Keep setting-specific content (for example Mistborn or Cosmere rules) out of core. It belongs in modules and data authored for a specific table.
- Keep Atlas-VTT and Obsidian compatibility at the Markdown boundary, as already specified.
- Do not claim any experiment was run unless it was.

## 11. Suggested additions to `TODO.md`

Under **Questions / Decisions Needed**:

- What is the minimal shape of a fixed-point constraint, including declared degrees of freedom, and how should a repair proposal and a "no valid repair" result be represented?
- What is the minimal knowledge-record schema (subject, content reference, source, acquired, status, author, optional believed-as override), and where should it live relative to canonical state?
- Should `Event` gain participants, witnesses, and causal links, and in what minimal form?
- Should provenance record the fingerprints of the inputs that informed a resolution?
- How should a branch and its commit points be represented for interleaved two-era campaigns?

Under **Later**:

- Hand-curated knowledge records and a per-party Obsidian view.
- System-proposed knowledge entries derived from event presence (after the hand-curated version has been used at the table).
- Event-triggered scheduling for belief-driven reactions.
- Salience flagging over the event log.
