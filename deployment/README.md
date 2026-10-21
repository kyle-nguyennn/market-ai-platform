# Promotion to market-maker (skeleton)

This repository **owns** research, features, signals, strategies and approval
evidence. It does **not** run a live exchange/order loop. The independently
maintained `market-maker` repository remains responsible for live strategy
loading, normalized market state, order reconciliation, venue adapters, account
state, and fail-closed risk enforcement.

Proposed promotion lifecycle:

1. Validate point-in-time data quality, performance and leakage controls.
2. Evaluate the same strategy/model/config with historical replay and (where
   meaningful) event-driven `market-sim` tests.
3. Record an immutable release: source commit, dependency lock, model hash,
   strategy identifier/version, config hash, test results and approval.
4. Package/install that **approved** release into `market-maker` via an
   explicit versioned interface or adapter.
5. Paper-trade; verify order lifecycle, reconciliation and risk; then enable
   live execution only through a separately authorized process.

No deployment automation or live-trading integration is enabled here.
`manifests/` is reserved for future versioned promotion records.
