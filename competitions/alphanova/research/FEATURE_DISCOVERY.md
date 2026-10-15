# P4: Anonymous-feature alpha discovery

## Motivation

P1 full-history gross Sharpes were all negative (about -0.001 to -0.003).
P2 reduced transaction costs, but its best 31-period net Sharpe remained
negative (-0.00653) with slightly negative gross Sharpe. A better signal
is needed before further execution optimization.

## Hypotheses

The six inputs are anonymous. Do **not** reverse-engineer their identity;
work with contemporaneous, ticker-permutation-equivariant structure.

Frozen search catalog (48 distinct transformations):
- Six row-wise percentile ranks: `rank_1` ... `rank_6`.
- Six row-wise clipped z-scores: `z_1` ... `z_6`.
- Fifteen cross-sectional ranks of raw pairwise differences: `diff_i_j`.
- Fifteen products of rank pairs, cross-sectionally centered: `product_i_j`.
- Six signed cubic rank-tail transforms: `tail_1` ... `tail_6`.

Each candidate is mapped to an OLS coefficient computed using only the
prior 20,000 labeled training hours (excluding the most recent 168 training
hours as an embargo sensitivity). The univariate factor is then smoothed
using the previously tested 240-hour EWM, causally de-tilted, and passed
through the fixed 0.02 L1 no-trade/50%-rebalancing policy.

This policy is **not tuned** per factor. For each candidate, record both
forward-target cross-sectional IC and lagged gross/net Sharpe on the
competition's proprietary return panel. IC and trading PnL are not
interchangeable metrics.

## Validation protocol

Select top 6 factors by aggregate **discovery net Sharpe** across fixed
nonadjacent periods 001, 004, 007, 010, 013, 016, 019. These validation
segments are separated by several cumulative-history months (>800 new
hours) to limit duplicate timestamps.

Only after the six names are frozen, evaluate them on 022, 025, 028, 031.
The latter were used in earlier P0–P3 work, so this is a *relative,
chronological confirmation*, **not** untouched final holdout evidence.

The search intentionally limits itself to 48 prespecified factors and one
fixed position policy. Winner's curse / multiple-comparison risk remains.
Compare period-level stability, not merely pooled Sharpe. Examine
train-slope sign consistency and signed target IC versus gross/net Sharpe.

Potential target-overlap leakage is reduced by a 168-hour embargo, but
because the forward target's horizon is undisclosed, this is not a
mathematical guarantee of complete purging.

## Running

```bash
git lfs pull
python -m pytest competitions/alphanova/tests/test_feature_screen.py -q
python -m competitions.alphanova.research.run_feature_screen \
  --config competitions/alphanova/configs/p4_factors.json \
  --output-dir competitions/alphanova/results/p4
```

GitHub Actions workflow:
`.github/workflows/alphanova-feature-discovery.yml`
selectively fetches 11 periods via Git LFS, runs the tests, outputs
`discovery_per_period.csv`, `discovery_summary.csv`,
`confirmation_per_period.csv`, `confirmation_summary.csv`, and
`manifest.json` into a downloadable artifact.

## Promotion decision

Promote a factor to standalone `Predictor` implementation only if it
shows positive aggregate **gross and net** Sharpe on confirmation, positive
period consistency and plausible forward-target IC. Then test with the
official full walk-forward runner and gauge-fix. The server-side
shuffled-label overfitting gate cannot be reproduced locally.

If all factors fail, stop searching increasingly complicated parameter
grids and study feature-target relationships/regime instability before
building more models. Do not manufacture a positive score by reporting
the maximum among 48 experiments.


## Measured findings — 2026-10-14

The screen ran successfully on actual Git LFS binary panels. The top two confirmation leads were `rank_1` (net Sharpe +0.01540, IC +0.08622) and `diff_3_6` (+0.01515, IC +0.08459), but only 2 of the 4 confirmation periods had positive net Sharpe for each. The earliest discovery leaders `tail_6` and `rank_6` weakened considerably in confirmation, an example of selection instability.

The selected factor families were packaged as single-file predictors with the **same fixed training and turnover settings** as the research screen. Full 31-period official evaluator:

| Predictor | Full net Sharpe | Gauge IC | City novelty |
| --- | ---: | ---: | ---: |
| Feature.1 cross-sectional rank | +0.0050 | +0.0185 | 58.6° |
| Rank of Feature.3 minus Feature.6 | +0.0045 | +0.0185 | 58.0° |
| Fixed 50/50 equal-weight blend | +0.0046 | +0.0195 | 59.4° |

The blend increased city novelty but did not improve Sharpe. The two individual predictors' period-level Sharpe vectors correlate approximately 0.982 (not the same as trajectory correlation), suggesting substantial shared regime dependence. The observed IC is positive but small. Only 15 of the 31 rank1 period evaluations were positive; 10 were negative and 6 flat.

Source runs:
- [Factor screen, frozen discovery/confirmation](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38581694045)
- [Official single-factor scoring](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38582412074)
- [Official fixed-weight ensemble](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38583089218)

**Result:** First positive *historical* AlphaNova net Sharpe candidates, but no established stable alpha or server-side gate acceptance. No hidden/live submission has been made. The next research branch should target factor conditional structure genuinely different from these two highly similar profiles.
