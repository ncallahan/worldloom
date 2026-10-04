---
type: question
status: open
summary: Consolidated identifier/address question note; four original questions retained as separate sections.
related: ["[[devwiki/experiments/question-derived-identity-address-randomness]]", "[[devwiki/architecture/provenance]]"]
---

# Identifier and address model

## Original question: identifier-address-model

What world/seed scope, if any, should be included in entity identity?

## Original question: entity-id-digest-length

Should the identity digest remain 48 bits, or be lengthened after collision-detection evidence is established?

## Original question: entity-alias-uniqueness

Should entity aliases become unique at WorldState.add_entity time rather than only at lookup?

## Original question: address-unicode-normalisation

Should address segments be NFC-normalised, or should NFC and NFD remain distinct canonical addresses?

These remain separate questions within one note. Identifier-scheme and validation decisions remain explicitly separate.

## MVP sequencing status

The identity/address experiment provided enough information to proceed with the MVP path without settling these remaining questions. The remaining choices are therefore deferred and do not block the MVP.

The recorded experiment results are the information available for the current MVP; any later identifier/address decision should be made when implementation evidence makes it relevant.
