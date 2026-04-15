# Options Market Data Replay and Analytics Workbench

## Why this project

This is a single coherent project that mixes:

- Python data engineering and data science
- HDF5 storage
- Options pricing mechanics
- Greeks and implied volatility
- Networking with UDP
- Linux debugging and operational workflows

It is a strong quant-dev style project because the components fit together naturally instead of feeling bolted on.

## What the system does

You simulate a small options market data environment:

1. A UDP publisher sends synthetic underlying price ticks and option quote updates.
2. A Python consumer listens on UDP, parses packets, checks sequence numbers, detects gaps, and normalizes events.
3. A pipeline layer writes:
   - raw packet and event stream
   - normalized quotes and trades
   - option chain snapshots
   - derived analytics
   into HDF5.
4. An analytics engine computes:
   - mid prices
   - implied vol
   - delta, gamma, theta, vega
   - simple vol smile and surface slices
   - PnL of simple strategies like delta-hedged straddle
5. A debug and replay CLI lets you replay a time range from HDF5 and reproduce bugs.

## Why this is the right project

A lot of project ideas only cover one or two target topics. This one covers all of them with natural dependencies:

- Networking is the ingestion mechanism.
- HDF5 becomes the numeric research store.
- Pricing transforms raw quotes into trader-facing analytics.
- Linux debugging becomes real because multiple processes can fail or misbehave.
- Data engineering becomes raw -> normalized -> enriched -> replayable datasets.

## Recommended architecture

### Process 1: Market data simulator

A Python process that publishes UDP packets:
- underlying spot updates
- option quote updates
- maybe occasional trade prints
- packet fields: session_id, sequence number, timestamp, symbol, bid, ask, size
- session_id is a monotonic identifier that increments each time the publisher restarts, allowing the consumer to distinguish a fresh sequence-number space from a gap in the previous session

Start simple with one underlying, maybe 10-30 strikes, and 1-2 expiries.

### Process 2: UDP listener and normalizer

A Python service that:
- binds to a UDP socket
- decodes packets
- validates sequence numbers scoped to the current session_id
- detects session_id changes (publisher restarts) and resets gap tracking
- logs missing or duplicated messages
- converts events into structured records
- batches writes to HDF5

### Process 3: Analytics engine

Runs either streaming or batch:
- compute time to expiry
- Black-Scholes fair value
- implied vol from observed mid
- Greeks
- smile by expiry
- simple surface snapshots

### Process 4: Replay and analysis notebook or CLI

Tools to:
- replay a specific time window
- rebuild analytics from raw events
- compare raw vs cleaned vs enriched data
- inspect packet loss impact

## HDF5 layout

Use HDF5 as a compact research store.

A clean structure could be:

- `/raw/packets/session={session_id}/date=...`
- `/events/quotes/session={session_id}/date=...`
- `/events/trades/date=...`
- `/chains/snapshots/date=...`
- `/analytics/greeks/date=...`
- `/analytics/iv_surface/date=...`

For each dataset, store numeric columns as arrays instead of Python objects whenever possible.

Good practice:
- separate metadata from numeric blocks
- chunk by time
- compress
- keep symbol mapping dictionaries outside the hot path

## Quant mechanics to implement

Keep the model side pragmatic.

### Phase 1
- Black-Scholes call and put price
- delta, gamma, vega, theta
- mid price from bid and ask
- implied vol via Newton or bisection

### Phase 2
- simple skew and smile visualization
- compare observed market price vs model price
- flag stale or arbitrage-like quotes
- strategy example: long straddle analytics

### Phase 3
- delta-hedged option PnL attribution
- realized vol vs implied vol comparison
- shock scenarios on underlying or volatility

## Networking topics you will practice

This project gives you real reasons to discuss:

- why UDP instead of TCP
- session_id for restart continuity (distinguishing new session vs gap)
- sequence numbers (scoped per session)
- packet loss
- duplicate packets
- out-of-order delivery
- replay and recovery design
- batching vs per-packet overhead

You can add a small gap-injector mode in the publisher:
- skip every Nth packet
- shuffle order occasionally
- burst-send updates
- delay one symbol stream

Then the consumer has to log and recover gracefully.

## Linux debugging topics you will practice

Run the publisher and consumer as separate Linux processes and deliberately break things.

Examples:
- bind to the wrong port
- kill and restart the consumer
- make the HDF5 file path read-only
- send malformed packets
- simulate high CPU from inefficient pandas operations
- leave an old process bound to the socket

Then practice with:
- `ps`, `top`, `htop`
- `ss` or `netstat`
- `lsof -i`
- `tail -f`
- `grep`
- checking exit codes and logs

## Suggested implementation phases

### Phase 1 - end-to-end skeleton
Build the smallest working system:
- UDP publisher
- UDP consumer
- parse packets
- write raw events to HDF5
- replay one minute of data

Deliverable:
one underlying, 5 strikes, 1 expiry

### Phase 2 - pricing and Greeks
Add:
- Black-Scholes
- implied vol solver
- Greeks
- HDF5 enriched datasets

Deliverable:
table of quotes with IV and Greeks

### Phase 3 - analytics
Add:
- smile chart
- simple surface by expiry
- summary notebook
- basic data quality checks

Deliverable:
research notebook or script that loads HDF5 and produces analytics

### Phase 4 - robustness
Add:
- missing packet detection
- duplicate detection
- malformed message handling
- replay and rebuild pipeline
- structured logs

Deliverable:
documented failure scenarios and how the system behaves

### Phase 5 - stretch
Add one of:
- multicast-style fanout simulation
- small Flask or FastAPI UI
- Parquet vs HDF5 benchmark
- asynchronous consumer
- Numba acceleration for pricing loops

## Resume bullet

Built a Python options market-data replay and analytics system with UDP-based tick ingestion, HDF5 research storage, normalized option-chain pipelines, and real-time computation of implied volatility and Greeks; added replay/debug tooling and failure handling for dropped and out-of-order packets.

## Best MVP scope for 7-10 days

A good MVP is:

- synthetic UDP market data generator
- consumer with sequence tracking
- HDF5 store for raw and normalized quotes
- Black-Scholes + IV + Greeks
- notebook that loads the store and plots smile
- CLI to replay a time window
- a short writeup on Linux debugging scenarios
