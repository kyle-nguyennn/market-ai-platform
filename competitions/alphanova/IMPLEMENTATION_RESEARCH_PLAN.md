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
- [x] Run full 31-period baseline reproduction: our net Sharpe -0.01526; official runner prints -0.0153 with identical CI dependencies.
- [x] Inspect gross vs net gap: all three model variants have negative gross Sharpe, so modeling, not transaction costs alone, is the first bottleneck.
- [x] Confirm all 31 periods' LFS binaries can be read in GitHub Actions (full-history job passed).

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

## P0/P1 full-history results — 2026-10-14

[Full-history GitHub Actions run 38576305259](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38576305259) completed successfully using **all 31 LFS-backed periods**. Synthetic tests passed, full P0/P1 comparison completed, and the supplied `runner.py demo_engineered.py --full` independently reported overall Sharpe **-0.0153**, agreeing with the research harness's baseline **-0.01526**.

| Predictor | Span | Gross Sharpe | Net Sharpe | Nonoverlap net Sharpe | Mean L1 turnover |
| --- | ---: | ---: | ---: | ---: | ---: |
| XGB interactions | 120 | -0.00123 | **-0.01483** | -0.01280 | 0.004137 |
| Engineered baseline | 120 | -0.00171 | -0.01526 | -0.01332 | 0.003490 |
| Ridge | 120 | -0.00347 | -0.01744 | -0.01602 | 0.005498 |

A previous fixed, evenly-spaced **three-period** sample (001, 016, 031) yielded +0.02448 for XGB interactions, +0.02023 for baseline, and +0.01286 for Ridge. That optimistic slice **did not generalize to all 31 periods**.

**Decision:** None of these P1 implementations has a positive local full-history edge. Do not submit them as-is. Since gross Sharpe is already negative, further smoothing alone cannot produce convincing alpha. Keep span 120 as a controlled reference and spend subsequent P1 iterations on substantially stronger cross-sectional predictive structure. Candidate ideas: univariate/difference/interaction ablations, regularized polynomial or spline features, feature-conditioned rank relationships, then low-capacity nonlinear ensemble. Apply unchanged 31-period backtests, nonoverlap checks and overfitting-gate constraints; avoid selecting models from one lucky period.

Global repository lint remains failing on pre-existing files including the untouched upstream `external/` kit; this P0/P1 implementation was independently validated by its synthetic CI and research workflow. The branch remains a **draft PR**, pending a model with credible edge.


## P1 full-history gate: completed 2026-10-14

The 31-period CI run 38576305259 completed successfully, including exact pipeline-vs-official parity to printed rounding precision (our baseline net Sharpe -0.01526; official printed -0.0153; original prior log -0.0155 due to environment versions).

| Candidate | Full gross Sharpe | Full net Sharpe | Nonoverlapping net Sharpe |
| --- | ---: | ---: | ---: |
| XGB interaction | -0.00123 | -0.01483 | -0.01280 |
| Upstream baseline | -0.00171 | -0.01526 | -0.01332 |
| Ridge | -0.00347 | -0.01744 | -0.01602 |

**Interpretation:** negative gross PnL means lack of robust predictive alpha, even before costs. The latest-period positive results and 001/016/031 sampled results were not representative. Do not promote these P1 candidates for submission.

## P2 — Turnover-aware position construction

Code:
- `research/positions.py` contains a causal L1 no-trade band and partial rebalancing controller. A no-trade decision compares the current desired 20-asset vector with the **last held** vector, not next-period returns.
- `research/run_p2.py` fits each P1 model once per period, then applies all turnover controls to the same inferred signal, avoiding retraining for every policy.
- `configs/p2_grid.json` freezes initial models, EWM spans (120 and 240), absolute L1 trade bands (0, 0.005, 0.02), and partial rebalancing fractions (1.0, 0.5).

The outputs include gross/net Sharpe, cost drag, non-overlapping novel-history metrics, rebalancing frequency, training and inference runtimes and model configuration. Large grids are exploratory and **do not** constitute independent out-of-sample validation.

Tasks:
- [x] Causal no-trade and partial-rebalance policy.
- [x] Neutrality, finite-output and prefix-invariance tests.
- [x] Full-walk-forward P2 experiment workflow with Git LFS.
- [ ] Review full 31-period P2 results; identify whether turnover control can improve net Sharpe without degrading gross signal.
- [ ] Check robustness on a frozen chronological validation segment not used for further tuning.
- [ ] Do not interpret improved net Sharpe with still-negative gross Sharpe as learned alpha.

Run:

```bash
python -m competitions.alphanova.research.run_p2 --scope full \
  --output-dir competitions/alphanova/results/p2-full
```

## P3 — Submission hardening (experimental candidate)

The provisional `submissions/turnover_xgb_v1.py` is a **single-file, self-contained** `Predictor` using the P1 same-hour XGBoost interaction design and a default L1 no-trade band. It is **not** a promoted or recommended submission: P1 gross performance is negative and P2 remains exploratory.

Contract checks in `tests/test_hardening.py`:
- AST-level structure checks: module docstring, imports and a single Predictor class only; no module-level training/data reads.
- No forbidden backward fills, shifted future labels, centered rolling windows or circular roll calls in the submission source.
- Market-neutral 20-asset outputs with finite values.
- Prefix invariance of predict() against future append (causality).
- Inference may overlap train data; a permuted row order retrain does not crash.
- Deterministic serialized/pickled model reloading.
- Ticker-order equivariance and tolerance of NaN/inf feature inputs.

Server-side gate still cannot be reproduced by the local runner, especially its shuffled-label overfitting null and private execution adjustments. Tests here do **not** certify acceptance.

Tasks:
- [x] Implement and test standalone Predictor candidate.
- [x] Add full official runner and `--gauge-fix` job to CI.
- [ ] Inspect actual full-run, novelty and serialization results from CI.
- [ ] Run a static scan of submitted file before upload, as the official checker scans comments too.
- [ ] Final sign-off requires **positive gross and net walk-forward Sharpe**, non-overlap stability and novelty; otherwise reject candidate.

The final package always contains only the selected `.py` file; no local research module imports or changed upstream kit modules.


## P2/P3 measured results and promotion decision — 2026-10-14

Source: [P2/P3 full CI run 38577733392](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38577733392). All 31 LFS-backed periods and all 31 gauge matrices loaded successfully. The initial policy sweep and official runner validation **passed**.

| P2 config | EWM | No-trade L1 band | Rebalance fraction | Gross Sharpe | Net Sharpe | Non-overlap net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Upstream engineered baseline | 240 | 0.020 | 0.50 | -0.00021 | **-0.00653** | -0.00503 |
| XGB interactions | 240 | 0.020 | 0.50 | -0.00016 | -0.00700 | -0.00534 |
| XGB interactions | 240 | 0.020 | 1.00 | +0.00004 | -0.00809 | -0.00610 |

The selected parameter combination improves the original -0.01526 P1 net Sharpe but still has non-positive gross Sharpe. **This is an execution policy improvement, not alpha discovery.** The grid is exploratory: optimized against the same 31 periods, subject to selection bias.

Provisional `turnover_xgb_v1.py` P3 official full runner:
- Net Sharpe **-0.0139**; IC **+0.0009**; city novelty **39.6°** (same closest city as baseline). Not promotable.
- CI source: `p3_official_full.log`, `p3_gauge_fix.log` in the uploaded artifact.

`submissions/candidate_p3.py` now packages the **measured best P2 configuration** as one standalone Predictor subclass. `tests/test_candidate_p3.py` verifies parity with the upstream model followed by `research.positions.position_policy`, causality, serialized inference, ticker equivariance, and overlapping inference. CI additionally executes its standalone full runner and gauge metrics, which must be checked before any use.

**Decision:** No competition submission from the current model family. Neither negative net Sharpe nor <60° city novelty meets internal promotion requirements. Next research work should seek independent predictive structure in the six input features; further smoothing sweeps alone are unlikely to supply alpha. Treat this P3 file as a reproducibility artifact and ready-to-change packaging template.


## P4 — Anonymous-feature discovery (completed, 2026-10-14)

A prespecified catalog of **48 contemporaneous cross-sectional factors** (6 ranks, 6 clipped z-scores, 15 ranked pair differences, 15 rank products, 6 cubic tails) was screened on 7 spaced discovery periods. Top 6 were frozen *before* evaluating 4 later confirmation periods. See `research/FEATURE_DISCOVERY.md` and `configs/p4_factors.json` for the exact protocol.

Selected discovery → confirmation net Sharpes:
- `rank_1`: +0.00783 → +0.01540; confirmation target IC +0.08622.
- `diff_3_6`: +0.00776 → +0.01515; confirmation target IC +0.08459.
- `z_6`: +0.00956 → +0.00813; `rank_6`: +0.01568 → +0.00307.
- `tail_6`: +0.01577 → +0.00298; `diff_1_2`: +0.01226 → 0.00000.

Standalone submissions for rank1, diff36 and a fixed-weight 50/50 ensemble passed contract and policy parity tests. **All 31-period official local walk-forward and gauge evaluations completed successfully**:

| Candidate | Full-history net Sharpe | Target IC | City novelty | Decision |
| --- | ---: | ---: | ---: | --- |
| `factor_rank1_p4.py` | **+0.0050** | +0.0185 | 58.6° | Leading *experimental* candidate |
| `factor_diff36_p4.py` | +0.0045 | +0.0185 | 58.0° | Fallback hypothesis |
| `factor_blend_p4.py` | +0.0046 | +0.0195 | 59.4° | More novel but weaker Sharpe than rank1 |

The rank1 factor has 15 positive, 10 negative and 6 zero period Sharpes in the printed official 31-period runner logs. The two single-factor strategies' *period-level Sharpe* sequences correlate approximately 0.982, indicating little observed regime diversification; this is **not** the official pairwise signal correlation admission metric.

- [P4 discovery CI](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38581694045)
- [Official full-history rank1/diff36](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38582412074)
- [Full-history blend and component retest](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38583089218)

**Caveats / no automatic submission:** This Sharpe is small and likely fragile to sampling error. Confirmation periods were already used in previous modeling experiments; the entire 31-period history has been inspected. Novelty angles are below the preferred 60° proxy, although official admission is based on absolute time-averaged pairwise correlation ≤0.5 (not city angle). The hidden shuffled-label overfitting gate has not been run or reproduced. The kit's unknown target horizon means the chosen 168-hour embargo is a sensitivity precaution, not a guaranteed full purge.

Next: freeze rank1 as research leader; test stability in later genuinely unseen data or external live competition feedback **only when a user explicitly authorizes submission**. If continuing model research, seek **orthogonal** features/conditional effects rather than parameter-sweeping rank1 and diff36 on the already-used history.
