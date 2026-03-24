# ADR 004 — Canary Routing

**Status:** Accepted

**Context:** Model rollouts need to be gradual to detect regressions under live traffic before full promotion.

**Decision:** Canary routing at the inference gateway layer, controlled by a percentage config in the model deployment record.

**Consequences:** Routing logic must be deterministic enough for testing and reproducible replay.
