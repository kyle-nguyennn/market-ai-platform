# Research-to-live trading architecture

## Purpose

`market-ai-platform` is the **research and experiment workspace**. Features,
alpha signals and strategies all live in this repository. The production
trading framework (`market-maker`) and event-driven market simulator
(`market-sim`) remain independent, installable components.

## Ownership and dependencies

| Component | Owns | Does not own |
| --- | --- | --- |
| `market-ai-platform` | Data prep, feature computation, signal research, strategy development, experiments, evaluation, strategy approval artifacts | Live order lifecycle or exchange connectivity |
| `market-sim` | Simulation mechanics, matching and synthetic execution where implemented | Research signals, portfolio decisions, live orders |
| `market-maker` | Production strategy runtime, normalized market I/O, order management, risk gates and venue adapters | Research experiments or strategy optimization |

Current code retained in place:
- `libs/features/`: existing features and feature registry (new category namespaces are additive).
- `libs/models/`: existing model registry/loaders and inference support.
- `libs/eval/`: existing evaluation utilities.
- `services/`: current data, inference, evaluation/control plane services.
- `external/alphanova-2026-cycle4/`: external organizer kit; untouched.

New skeleton namespaces:
- `libs/signals/`: candidate alpha signals.
- `libs/strategies/`: executable decision logic under research.
- `libs/backtesting/`: future replay/simulation integration adapters.
- `experiments/`: configs, reproducibility and local ignored results.
- `deployment/`: future approved-release packaging and promotion artifacts.

All `libs/*` namespaces remain installable via the existing setuptools
`include = ["libs*"]` rule; no dependency or service migration is required.

## Contract boundary

The existing `market-maker` interface for market-making is
`BaseQuoter.quote(MarketState) -> list[Quote]`. Reuse its venue-neutral
`MarketState`/`Quote` contract for deployable quoter strategies, using an
explicit adapter when a research representation differs. Venue-specific
symbol/tick/precision conversion, signed requests and SDKs remain in the
production framework. Do not duplicate production trading types here.

**Open design decision:** generic cross-sectional, portfolio and multi-asset
strategies may need a separate versioned strategy protocol. Define it with
`market-maker` before implementation; do not force these strategies into
`BaseMMQuoter`.

## Lifecycle

```text
data (time-correct)
    -> libs/features
    -> libs/signals
    -> libs/strategies
    -> experiments + libs/eval
    -> [fast historical backtest | optional market-sim event simulation]
    -> review + immutable versioned approval artifact
    -> install approved artifact in market-maker
    -> paper/shadow validation + independent risk gates
    -> live exchange adapters (explicit separate authorization)
```

Promotion must preserve strategy logic and versioned model/config across
research and deployment, while allowing the *data source and execution adapter*
to change. Comparability still requires documenting simulation assumptions
(e.g. fill mechanics, latency, cost model) and time/leakage boundaries.

## Scope of this first scaffold

This change creates package namespaces, experiment/promotion placeholders,
and import smoke tests. It **does not** introduce a new strategy contract,
refactor existing feature/model services, install `market-sim` or
`market-maker`, implement a backtester, or authorize live trading.

## Next logical milestones

1. Build a working signal -> strategy -> fast backtest loop in
   `market-ai-platform` using a reproducible experiment specification.
2. Version signal/strategy outputs and freeze release manifests with actual
   validation criteria.
3. Define and test the `market-maker` contract adapter; integrate
   `market-sim` as a separate optional simulation engine.
4. Add paper-trading and risk-gated release promotion when end-to-end tests
   are reliable.
