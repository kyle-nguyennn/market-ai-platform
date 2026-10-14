# P5 parallel research: shuffled-label null and conditional regimes

Repository: `kyle-nguyennn/market-ai-platform`, branch `feat/alphanova-p0-p1`, PR #23.

The submitted P4 `rank_1` Predictor returned `OVERFITTING_FAILED` on the AlphaNova server. Its historical Sharpe (+0.0050) is not evidence of an accepted strategy.

## P5-A: training-only diagnostics

`research/run_p5a_null.py` measures the actual OLS slope, mean training cross-sectional target IC, and coefficient-sign consistency across eight chronological chunks. It compares these against 79 synchronized target-block permutations (168 time rows per block) using **only the 20,000-row training tail before the 168-row embargo**.

Frozen diagnostic periods 003, 005, 011 (historical losses), 012, 017, 027 (historical wins), 031 (latest). These were chosen after inspecting P4 and are explanatory, **not untouched confirmatory samples**.

The null preserves within-block target autocorrelation and cross-sectional target vectors, but it does NOT reproduce AlphaNova's private permutation retraining gate. The smallest attainable empirical p-value is 1/80.

## P5-B: two predeclared regime hypotheses

`research/regime.py` and `research/run_p5b_regimes.py` fit a rank1 slope conditional on either (a) raw cross-sectional Feature.1 dispersion or (b) Feature.1/Feature.6 cross-sectional rank disagreement, both observable at the current hour.

The threshold for each regime is the training median, never computed from validation. The low/high OLS slopes are shrunk halfway toward the global OLS slope. The baseline is the same factor with a single unconditional coefficient.

Frozen portfolio settings: 240-hour EWM, L1 no-trade band 0.02 and 50% partial rebalancing. Discovery periods 001/004/007/010/013/016/019; later confirmation periods 022/025/028/031. These later periods have also appeared in previous research and are NOT independent hidden test evidence.

Report per-period fitted slopes, thresholds, gross and net Sharpe, cost drag, turnover and pooled summary. Do not select a regime or tune parameters solely to make a previously observed history favorable.

## Execution

CI `.github/workflows/alphanova-p5.yml` has two independent parallel jobs, each fetching only its chosen LFS panels and uploading its own result artifact.

Local commands:

```bash
python -m pytest competitions/alphanova/tests/test_p5a_null.py competitions/alphanova/tests/test_p5b_regimes.py -q
python -m competitions.alphanova.research.run_p5a_null
python -m competitions.alphanova.research.run_p5b_regimes
```

Promotion requires material positive gross and net walk-forward performance, stability beyond a few periods, and ultimately passing the server's proprietary overfitting test. A null-test rejection is evidence against the hypothesis, not a reason to repeatedly resweep the same history.


## Completed measurements — 2026-10-14

### P5-A training-block null (CI 38589454790)

| Period | Training target IC | OLS beta | Empirical two-sided p | Stable beta-sign fraction |
| --- | ---: | ---: | ---: | ---: |
| 003 | +0.02280 | +0.03762 | 0.0375 | 0.75 |
| 005 | +0.01868 | +0.02917 | 0.0250 | 0.62 |
| 011 | -0.02467 | -0.04014 | 0.0375 | 0.62 |
| 012 | -0.01885 | -0.03061 | 0.0375 | 0.75 |
| 017 | -0.00576 | -0.00873 | 0.4875 | 0.62 |
| 027 | -0.01799 | -0.02880 | 0.1000 | 0.62 |
| 031 | -0.01842 | -0.02939 | 0.0750 | 0.62 |

Some training associations are stronger than block-shuffled target alignments, but the relationship changes sign. These period choices were selected after earlier performance inspection; **do not treat the p-values as an unbiased multiple-comparison-adjusted inference**, or conflate them with the server's private gate.

### P5-B low-capacity regime models

A numerical symmetry issue was discovered in the discrete rank-disagreement score: floating-order differences at the training median could flip a regime assignment under ticker reordering. Rounding the rank-disagreement scalar to 12 decimals at construction (both research and standalone class) restores invariant regime assignment. Earlier unrounded findings are superseded.

After the fix, [P5-B full research workflow](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38590603696):

| Regime | Discovery gross | Discovery net | Confirmation gross | Confirmation net | Confirmation positive |
| --- | ---: | ---: | ---: | ---: | ---: |
| Constant rank1 | +0.013395 | +0.007830 | +0.023002 | +0.015400 | 2/4 |
| Feature1 raw dispersion | +0.002977 | -0.002410 | +0.016833 | +0.007937 | 2/4 |
| Feature1/6 rank disagreement | +0.015164 | +0.009452 | +0.031301 | +0.022645 | 4/4 |

The fixed disagreement hypothesis outperforms the unconditional model on these 11 sampled historical periods; however, this is not independent out-of-sample research evidence.

### Full official validation — no-go

`submissions/disagreement_regime_p5.py` is one standalone Predictor subclass. Its synthetic parity, causality, serialization, ticker permutation and missing-value checks pass. The latest-period runner's explicit cross-sectional neutrality check also passed.

[Official full/gauge CI run 38590616667](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38590616667):

| Metric | P5 disagreement-conditioned | P4 rank1 |
| --- | ---: | ---: |
| 31-period official net Sharpe | +0.0041 | +0.0050 |
| Gauge IC | +0.0160 | +0.0185 |
| City novelty | 55.4 deg | 58.6 deg |

**Decision: Do not resubmit P5.** Its favorable sampled-period result does not survive all-history comparison; the previous P4 candidate was already server-rejected for weak evidence against its shuffled-label null. Further tuning these small regimes on the same windows risks researcher overfitting. Prefer genuinely distinct feature mechanisms, stronger target IC, and independent future periods.

Updated artifacts are accessible in the two independent P5 jobs and official standalone job; no server acceptance is claimed.
