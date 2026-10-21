# Backtesting integration (skeleton)

Research and strategy evaluation live in `market-ai-platform`.

Planned engines:
1. **Fast historical backtests** for broad model/parameter screening,
   using point-in-time features and explicit transaction cost assumptions.
2. **Event-driven simulation**, integrating the independently installed
   `market-sim` engine for order matching, latency, fills, and market-impact
   experiments where supported.
3. **Paper/shadow validation** through `market-maker` before any live
   promotion.

The same strategy artifact and versioned model/config should be evaluated
across engines, with adapters at the data/execution boundaries. Simulated
fills and market impact are assumptions, not live-execution guarantees.

No backtester or market-sim adapter is implemented by this scaffold.
