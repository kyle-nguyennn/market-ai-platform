# ADR 001 — Monorepo

**Status:** Accepted

**Context:** Three services share data contracts, feature schemas, and storage abstractions. Keeping them separate repos would duplicate contracts and make cross-cutting changes expensive.

**Decision:** Single monorepo with `libs/` for shared code and `services/` for deployable units.

**Consequences:** All services version together. Inter-service contracts are enforced via shared `libs/contracts`.
