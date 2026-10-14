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
