# Strategy research

Strategies are **developed and evaluated in this repository**, then packaged as
immutable, approved releases for execution in `market-maker`.

Proposed namespaces:
- `market_making/`: pricing, inventory-aware quoting and sizing;
- `statistical_arbitrage/`: spread and relative-value strategies;
- `portfolio/`: portfolio construction, rebalancing and allocation;
- `competition/`: challenge-specific research.

**Production contract:** `market-maker/quoter/base_quoter.py` currently exposes
`BaseQuoter.quote(MarketState) -> list[Quote]` (and `BaseMMQuoter` for
market-making). Any market-making implementation intended for deployment must
use that interface or an explicitly versioned adapter. Its internal
`MarketState` and `Quote` are venue-neutral, using `Decimal`.

Do not copy those types or introduce a competing `BaseQuoter` here. A generic
portfolio/multi-asset strategy interface should be designed and versioned with
`market-maker` *before* implementing its production adapter.

The AlphaNova organizer kit remains at `external/alphanova-2026-cycle4/` for
now. `competition/alphanova/` is reserved for *our* strategy code only; no
competition files are moved by this scaffold.

Strategies must remain deterministic under fixed inputs/configuration,
avoid direct exchange I/O, and emit desired trading actions; the production
runtime handles reconciliation and independent risk checks.
