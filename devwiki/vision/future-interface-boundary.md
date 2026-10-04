---
type: vision
status: vision
summary: Descriptive interface direction retained verbatim from ARCHITECTURE §14.
related: ["[[devwiki/architecture/future-interface-boundary]]", "[[devwiki/vision/interfaces]]"]
---

# Future interface boundary



Worldloom is intended to support multiple clients over the same canonical world rather than separate world representations.

Long-term clients may include:

- a generated world-guide/wiki;
- interactive GIS;
- natural-language query and controlled world editing;
- historical timeline exploration;
- character/observer perspectives;
- GM/referee tools;
- author research tools;
- consistency and continuity inspection;
- scenario/counterfactual exploration;
- visual observation;
- eventually, a 3D client.

These are future interface directions, not current implementation requirements.

The architectural consequence is that the core should remain capable of exposing a coherent world at a specified simulation time and scope, tracing provenance, distinguishing canonical reality from derived projections and observer knowledge, and making mutations or branch simulations explicit.

A user-facing interface should be treated as a projection or control surface over Worldloom state. It should not become an alternative authority for world facts.

The eventual 3D environment is intentionally secondary to the primary storytelling goals: maintaining a consistent world for TTRPGs and fiction, and making that world inspectable and usable by authors and game masters.
