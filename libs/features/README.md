# Feature research namespaces

The platform already implements reusable computations in `libs/features/rolling.py`,
`event.py`, `liquidity.py`, `greeks.py`, and other modules. **Do not move or
duplicate them as part of the skeleton.**

New research features can be organized under:

- `microstructure/`: order-book and trade microstructure;
- `volatility/`: realized and forecast volatility;
- `cross_sectional/`: relative-value and universe-level features;
- `technical/`: price/volume transformations.

Reuse `libs/features/registry.py` where applicable. Preserve as-of timestamps,
feature versions, point-in-time validity, and offline/online parity. No new feature
computations are included in this scaffold.
