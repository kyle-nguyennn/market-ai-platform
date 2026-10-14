# AlphaNova Season 1 Cycle 4 — Implementation & Research Plan

**Status:** P0/P1 initial implementation prepared on `feat/alphanova-p0-p1`, based on `alphanova-2026-4`. The original kit is immutable under `external/alphanova-2026-cycle4`.

## Objective and constraints

Maximize the competition's unannualized Sharpe on the proprietary return panel, **after** the 5 bp L1 position-turnover charge. Submit a **single standalone Predictor subclass** with de-meaned hourly cross-sectional outputs over 20 rotating ticker identities. Inputs are six anonymized per-ticker features.

Official local backtest convention:

- `gross[t] = sum_j P[t-1,j] * returns[t,j]`
- `turnover[t] = sum_j abs(P[t-1,j] - P[t-2,j])`
- `net[t] = gross[t] - 0.0005 * turnover[t]`
- The first row is set to zero; each local period's evaluation resets positions.
- Official scorer can have additional cost adjustments. Hidden history and live behavior are not reproducible locally.

Constraints: train <= 240 s, predict <= 60 s, <= 8 GB RAM, CPU only; no look-ahead, all submission logic within the Predictor class, no row-order/data-derived assertions. The server-side shuffled-label overfitting gate is **not** reproduced by local runner. Passages in the kit warn that rolling features can inflate the shuffled null; stay contemporaneous first.

## Baseline (measured before P0/P1)

| Metric | Supplied `demo_engineered.py` |
| --- | ---: |
| Latest period 031 validation Sharpe | +0.0068 |
| Full 31-period net Sharpe (24,800 scored rows) | -0.0155 |
| Gauge-fixed IC | +0.0002 |
| City novelty | 38.3 degrees |
| Typical training | ~1-2 s / period |
| Positive periods | 10 of 31 |

References: `external/alphanova-2026-cycle4/out/demo_engineered_full.log` and `out/demo_engineered_gauge_gix.log`.

**Do not claim profitable alpha from a gate pass.** The baseline is fast and correctly de-meaned, but has negative aggregate net Sharpe and insufficient city separation.

## Directory contract

- `external/alphanova-2026-cycle4/`: upstream kit, LFS inputs, runner, evaluator; do not edit.
- `competitions/alphanova/research/diagnostics.py`: P0 official-compatible gross/turnover/cost/net decomposition.
- `competitions/alphanova/research/run_experiments.py`: P0/P1 period-by-period evaluation, structured comparisons, overlap trim.
- `competitions/alphanova/submissions/ridge_v1.py`: P1 regularized linear model.
- `competitions/alphanova/submissions/xgb_interactions_v1.py`: P1 shallow interaction XGBoost model.
- `competitions/alphanova/configs/p1_grid.json`: frozen first experiment matrix.
- `competitions/alphanova/tests/`: synthetic parity, prediction contract and shuffled-row crash checks.
- `competitions/alphanova/results/`: generated experiment artifacts; do not commit large outputs.
- `.github/workflows/alphanova-research.yml`: unit tests and latest-period P0/P1 smoke experiment with selective LFS pulls.

## P0 — Baseline parity and diagnostics

- [x] Implement PnL components matching the kit's lag and 5bp cost semantics.
- [x] Add synthetic regression/parity tests against kit `evaluation.backtest`.
- [x] Add gross Sharpe, net Sharpe, mean turnover, mean cost, positive-period counts, maximum train/predict times, and per-period CSV.
- [x] Add both baseline and sign-inverted PnL; **costs do not change sign**.
- [x] Add a non-overlapping cumulative-history *diagnostic*: retain validation rows first appearing after the previous period's total row count.
- [x] Add an optional trailing training-label embargo as a sensitivity check; do not claim its width purges the undisclosed target horizon.
- [ ] Run full 31-period reproduction and confirm aggregate P0 baseline net Sharpe is -0.0155 within numerical tolerance.
- [ ] Inspect gross vs net gap and cost distribution; document root cause of negative net score.
- [ ] Confirm LFS binary availability in the actual CI/workstation environment.

**Validity caveat for non-overlap metric:** cumulative row positions must represent the same chronological timestamps from period to period; independent ticker rotations do not affect that temporal alignment. The method trims repeated rows but cannot recover new rows outside the runner's last-800 holdout. It is an additional diagnostic, not an official metric.

## P1 — Predictive structure and cheap ablations

| ID | Candidate | Feature hypothesis | Current implementation |
| --- | --- | --- | --- |
| E1 | `baseline` ± sign | Existing direction may be wrong; cost remains positive | Integrated |
| E2 | `ridge` | Linear combinations of 6 cross-sectional ranks and 4 differences | Implemented |
| E3 | `xgb_interactions` | Nonlinear feature interactions among the anonymized inputs | Implemented |
| E4 | All candidates, EWM span 24 and 120 | Turnover/predictive decay trade-off | Integrated |

All model features use only the same timestamp. Each model is ticker-permutation equivariant: train a single regression over ticker rows, never use an asset ID as a predictor. Ridge regularization and XGBoost capacity are deliberately conservative to reduce shuffled-label memorization. Neither candidate's alpha or gate acceptance has been established.

**Research progression:**

1. Fast smoke check on 031, comparing gross vs net vs flipped sign.
2. Full 31-period apples-to-apples evaluation with identical train/validation rows.
3. Compare overlap-trimmed, non-overlapping metrics and period consistency, not just latest Sharpe.
4. If gross > 0 but net <= 0, expand EWM spans / position no-trade controls.
5. If gross <= 0 and IC near zero, investigate improved same-hour cross-sectional transforms and feature interactions; avoid wide hyperparameter searches.
6. Select one candidate for the *official* local runner and `--gauge-fix` novelty measurement.
7. Before submission: inspect code for look-ahead and top-level calls; check overlapping train/predict and permuted-row retrains; expect server overfitting gate behavior to differ.

## Reproducible commands

Run from repository root with Python environment containing pandas, numpy, scikit-learn, XGBoost, matplotlib, pyarrow and pytest. Retrieve LFS binaries first:

```bash
git lfs pull
python -m pytest competitions/alphanova/tests -q
python -m competitions.alphanova.research.run_experiments --scope latest
python -m competitions.alphanova.research.run_experiments --scope full
```

To test a single model and sensitivity embargo:

```bash
python -m competitions.alphanova.research.run_experiments \
  --scope full --models ridge --spans 24 120 --signs 1 -1 --embargo-rows 24 \
  --output-dir competitions/alphanova/results/ridge_embargo24
```

The driver writes `summary.csv`, `per_period.csv`, and `manifest.json` to the selected output directory. An unqualified run overwrites those three artifacts: choose separate output directories to retain historical experiments.

For official-equivalent validation, change into the upstream kit directory:

```bash
cd external/alphanova-2026-cycle4
export COMP6_DISABLE_PIP_INSTALL=1
python runner.py ../../competitions/alphanova/submissions/ridge_v1.py --full
python runner.py ../../competitions/alphanova/submissions/ridge_v1.py --gauge-fix
python runner.py ../../competitions/alphanova/submissions/xgb_interactions_v1.py --full
```

This is a local validation only. The server gate's repeated shuffled-label retraining, hidden return history and execution costs are not reproduced.

## Promotion gates (internal, not official rules)

- Valid, finite 20-asset demeaned outputs; run on train/predict overlap and reordered tickers.
- Runtime comfortably within 240s/60s and 8GB.
- Positive aggregate *net* Sharpe on official walk-forward; evaluate gross/net gap.
- Positive or credible non-overlap performance, plus period consistency (avoid one lucky latest period).
- Prefer city novelty >60 degrees; the official quality-set admission condition is |mean pairwise signal correlation| <=0.5, which city distance only approximates.
- Run final untouched validation once after choosing candidate; track every experiment tested to avoid researcher-overfitting.

## Immediate handoff

- Inspect CI and/or local smoke logs; fix any test/parity failure before trusting comparisons.
- Run P0 parity on the full LFS dataset; compare baseline net Sharpe with -0.0155.
- Report a table of gross/net/new-history Sharpe, turnover, cost drag and time for all first-grid candidates.
- Do not submit on the strength of synthetic tests or local latest-period results alone.


## Initial CI results — 2026-10-14 (latest period 031 only)

[GitHub Actions run 38574775651](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38574775651): synthetic tests **9 passed**; latest-period smoke **passed** with actual Git LFS binaries (031 features: 50,815 rows x 120 columns). Results artifact: `alphanova-p0-p1-latest`.

| Model | Span | Sign | Gross Sharpe | Net Sharpe | Mean L1 turnover |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ridge | 120 | +1 | +0.06262 | **+0.03152** | 0.007072 |
| XGB interactions | 120 | +1 | +0.04525 | +0.01517 | 0.004901 |
| Engineered baseline | 120 | +1 | +0.03952 | +0.00868 | 0.004231 |
| Ridge | 24 | +1 | +0.03286 | -0.02969 | 0.024195 |

The sign-reversed span-120 variants were all negative net Sharpe. The strong drop from span 120 to 24 supports turnover control in this period. Numbers are from the CI dependency versions (Python 3.12, pandas 3.0.6, XGBoost 3.4.1), which differ from the previously logged baseline (+0.0068 latest). **These are single-period local validations, not full-history alpha or leaderboard outcomes.** Full 31-period P0 parity, non-overlap robustness and novelty remain unmeasured for the P1 models.
