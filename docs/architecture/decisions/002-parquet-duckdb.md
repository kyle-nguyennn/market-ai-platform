# ADR 002 — Parquet + DuckDB

**Status:** Accepted

**Context:** Training datasets need reproducible snapshots with fast column-oriented reads. SQL-style analytics must be possible locally without a cluster.

**Decision:** Parquet for artifact storage; DuckDB for local analytics and dataset diffing.

**Consequences:** No dependency on a distributed compute cluster for MVP. DuckDB can be swapped for Spark later if scale requires it.
