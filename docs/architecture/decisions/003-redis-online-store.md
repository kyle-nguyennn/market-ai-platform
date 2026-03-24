# ADR 003 — Redis Online Store

**Status:** Accepted

**Context:** The inference gateway needs sub-millisecond feature retrieval per symbol. A database round-trip on each score request is too slow.

**Decision:** Redis as the online feature cache. Feature snapshots are keyed by symbol and updated by the ingestion worker.

**Consequences:** Feature freshness must be tracked explicitly. Stale-feature detection is required in the serving path.
