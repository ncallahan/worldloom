---
type: architecture
status: process
summary: Prototype path retained verbatim from ARCHITECTURE §11.
related: ["[[devwiki/architecture/index]]", "[[devwiki/process/development-workflow]]"]
---

# Prototype path



The first end-to-end prototype should be deliberately small. Its immediate purpose is to demonstrate **meaningful module-to-module interaction**, not to implement progressive world generation in miniature.

A useful chain is:

    module A
        ↓
    output available
        ↓
    module B consumes A
        ↓
    B produces something
        ↓
    module C consumes B + existing state
        ↓
    C resolves or changes state
        ↓
    persistent fact / event

The current terrain → water → settlement suitability → settlement resolution chain is a suitable vertical slice. It should remain small while making the dependency causal enough that tests demonstrate that downstream results actually depend on upstream outputs.

Progressive projection and resolution should be tested separately once the prototype can support meaningful module interaction.
