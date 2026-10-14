# AlphaNova Season 1 — Cycle 4 closeout

**Closed for research on 2026-10-14 (Asia/Singapore).** The next submission window is expected at the 15 October 2026 UTC boundary, subject to AlphaNova's live contest page. This is a research retrospective, not an accepted competition entry.

## Final disposition

- Submitted **P4 Feature.1 rank** (`submissions/factor_rank1_p4.py`) to Cycle 4.
- Server verdict: **OVERFITTING_FAILED**. No accepted AlphaNova Cycle 4 signal from this research line.
- Do **not** resubmit P4 clones or P5's weak conditional model. Freeze P0–P5 experiment settings and source history as a reusable baseline.
- PR #23 merges a reproducible research and submission-validation framework, **not a profitable trading strategy**.

## Scoring is the optimization target

The contest trades proprietary returns, **not** ordinary market price returns. The training **target** is a separate, undisclosed forward-looking series: target IC is a diagnostic and must not be confused with the net-return Sharpe objective.

Local position profit is `P(t-1) · proprietary_returns(t)` minus `0.0005 * L1(P(t-1)-P(t-2))`; cross-sectional weights must be de-meaned. The official scorer, including hidden behavior and shuffled-label gate, is authoritative. Training and inference must be CPU-safe and self-contained in one Predictor class.

## Observed quantitative progression

| Iteration | Local 31-period net Sharpe | What changed |
| --- | ---: | --- |
| Engineered baseline (P0/P1 CI environment) | -0.01526 | Reproducible pipeline parity established |
| P1 shallow XGB interactions | -0.01483 | Weak/negative gross edge |
| P1 Ridge | -0.01744 | Simpler model not necessarily better |
| P2 turnover-optimized engineered baseline | -0.00653 | Execution drag reduced; gross Sharpe still approximately -0.00021 |
| P4 cross-sectional rank Feature.1 | +0.0050 | First marginal positive local history, rejected by server gate |
| P4 rank(Feature.3 - Feature.6) | +0.0045 | Highly similar behavior to Feature.1 rank |
| P4 fixed 50/50 blend | +0.0046 | Did not improve net Sharpe |
| P5 disagreement-conditioned rank1 | +0.0041 | Improved preselected samples, worse across all 31 periods |

P4 rank1 had IC approximately +0.0185 and city novelty 58.6°. Its approximate naive iid t-statistic using 24,800 nominal holdout rows is only 0.79; overlapping cumulative windows and repeated factor screening weaken inference further. P5 rank1/6 disagreement gave sampled discovery net +0.00945 and confirmation net +0.02265, yet full-history net was only +0.0041, IC +0.0160, novelty 55.4°. Its strong sampled result was **not sufficient**.

P5-A approximate training-block null found sign-changing OLS slopes across periods; several post hoc empirical block-null p-values were small, but the private shuffled-label retraining gate was **not reproduced**. These p-values are neither server gate probabilities nor selection-adjusted evidence.

## Lessons carried into Cycle 5

1. **Optimize the official net Sharpe and the gate early.** Test actual PnL, not only target loss/IC or model accuracy; compare with server-side rejection feedback.
2. **Separate modeling from execution.** Record gross and net Sharpe, turnover, mean cost, IC, novelty, and positive-period count. Avoid a no-trade policy that creates appealing net scores without predictive edge.
3. **Avoid researcher overfitting.** A 48-factor search plus repeated grid comparisons consumes apparent out-of-sample evidence. Fix discovery/selection/evaluation splits in advance, and treat prior Cycle 4 validation periods as explored.
4. **Cumulative data can repeat holdout hours.** Track non-overlapping chronological segments and label-horizon embargo sensitivity. Do not count repeated validation windows as independent observations.
5. **Ticker identities rotate by period.** Use cross-sectional, permutation-equivariant factors; never rely on stable ticker IDs across months. Test column reorder and row shuffle.
6. **Numerical invariance matters.** Rank-derived regime thresholds can flip at machine-precision ties when columns are reordered; a tiny regime switch can cascade through portfolio hysteresis. Deterministic threshold representations and explicit tests are necessary.
7. **Cheap, simple models can still be too weak.** Low-capacity OLS can fail the null gate due to a vanishing signal. More regularization or smoothing does not manufacture statistically detectable alpha.
8. **Novelty is a separate requirement.** City angle near 60° is heuristic, not the official correlation gate; passing novelty cannot replace positive, reliable Sharpe.
9. **Keep the upstream kit immutable.** Git LFS materializes real Parquet/NumPy data in CI. Research modules are reusable; submission files are single-class, self-contained `Predictor` implementations.
10. **Stop unproductive sweeps.** When fixed-parameter tuning reaches a plateau, test a new, predeclared conditional or orthogonal mechanism rather than fitting constants to prior holdouts.

## Reproducibility / provenance

- Competition kit: `external/alphanova-2026-cycle4/` (untouched; LFS training panels).
- Experiments: `competitions/alphanova/research/`, `configs/`, `submissions/`, `tests/`.
- Research and reported result: `IMPLEMENTATION_RESEARCH_PLAN.md`, `research/FEATURE_DISCOVERY.md`, `research/P5_HANDOFF.md`.
- Official local runner logs and artifacts: [P1 full history](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38576305259), [P2 policy](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38577733392), [P4 models](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38583089218), [P5 parallel](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38590603696), [P5 official](https://github.com/kyle-nguyennn/market-ai-platform/actions/runs/38590616667).

**Cycle 4 outcome:** competition gate failed, but the reproducible platform and methodological lessons are a concrete deliverable. No claims of leaderboard acceptance or prize eligibility.
