# AlphaNova Season 1 — Cycle 5 kickoff

**Planned start:** 2026-10-15 UTC boundary (15 October, 08:00 Singapore time). **Verify the official contest page for exact cycle opening, submission window and any rule changes.** Begin from merged PR #23, not from an unreviewed Cycle 4 experiment.

## Day 0: ingest and validate the new cycle

1. Confirm Cycle 5 source kit, submission API, scoring formula, target construction disclosures, server overfitting-gate rules, dependency availability, runtime limits, and entry quota; **do not assume Cycle 4 rules are identical**.
2. On a new development branch (e.g. `feat/alphanova-cycle5`), keep the new kit in `external/alphanova-2026-cycle5/`. Never overwrite the Cycle 4 reference data/logs. Compare kit files/metadata before running any reused code.
3. Store new large training files using Git LFS; update `.gitattributes` and `.gitignore` allowlist for the Cycle 5 path. Verify that `git lfs pull` materializes valid Parquet, not pointer text.
4. Run the official provided demo / baseline as a reference. Save environment versions, hashes, splits, gross/net PnL, mean cost, train and predict timings, and gauge/novelty. Validate the exact official backtest contract with a synthetic regression test.
5. Port the research scripts using explicit `--data-dir` and `--output-dir` paths where supported. The Cycle 4 scripts currently import the Cycle 4 `data_loader` and `Predictor` interface; **adapt and test interfaces**, don't blindly run them against different schema.

## Research priority: learn stronger alpha before policy search

### C5-P0 — frozen methodology

- Reserve genuinely unseen **future Cycle 5 observations** for later evaluation; earlier Cycle 4 periods are already heavily studied, including the four P4 confirmation periods.
- Specify discovery/train/embargo, model selection, final confirmation, selection metric and a small hypothesis budget *before reading scores*.
- Record each attempted signal and its multiple-testing footprint. Use signed IC on the forward target and gross/net proprietary-return Sharpe separately.
- Add per-period bootstrap/sign-consistency and a clearly labeled approximate null; never claim the locally permuted block null replicates the server's proprietary test.

### C5-P1 — new cross-sectional information

- Investigate **factor residuals orthogonal to rank1**, not a near-duplicate of rank(Feature3–Feature6).
- Predeclare a small number of causal interactions or rank-conditioned signals with a reason they should forecast the target and earn lagged proprietary returns.
- Check structural invariants: ticker permutation, zero cross-sectional exposure, training-row reorder tolerance, finite output, no future-looking transforms, overlapping train/predict slices.

### C5-P2 — robust policy after a gross signal

- Gate progression: positive gross Sharpe and coherent target IC first; only then test turnover, smoothing, and size scaling on a **frozen small grid**.
- Assess effectiveness over separated chronological periods, including worst-regime behavior, not just a pooled maximum. Compare cost drag versus predictive signal decay.
- Test city novelty and pairwise signal correlation separately; don't chase an angle by sacrificing profitable alpha.

### C5-P3 — submission readiness

- Single self-contained Python `Predictor` subclass; all helpers inside, imports only at module level; satisfy the official local quick de-mean check, full walk-forward and gauge, plus the server-side gate.
- Keep a submission ledger with filename + Git commit, model hypothesis, full and non-overlap performance, IC, novelty, server verdict, and reason for promotion/rejection. Avoid repeated uploads of correlated variants.
- If the gate rejects for a weak null, demand materially stronger **training-only predictability** and independent chronological evidence before another upload.

## Repo runbook

```bash
git switch alphanova-2026-4  # or merged integration base
git pull --ff-only
git switch -c feat/alphanova-cycle5

# After downloading and versioning the new official kit and LFS files:
git lfs pull
python -m pytest competitions/alphanova/tests -q

# Cycle 4 regression comparisons; only when its LFS data are available:
python -m competitions.alphanova.research.run_experiments --scope latest
python -m competitions.alphanova.research.run_p2 --scope latest
```

CI workflows under `.github/workflows/alphanova-*.yml` prove Cycle 4 algorithms and source contracts; when adapting to Cycle 5, update the workflow's branch triggers, data paths, schema checks, and official runner invocation. Maintain explicit, named artifact directories for every experiment and preserve raw logs. The workflows are not a live trading or signal-monitoring service.

## First Cycle 5 deliverable

A **baseline-and-methodology report**, plus at most a few prespecified model hypotheses and their falsifiable prediction/return relationships. No submission until an experiment exceeds the tiny, gate-rejected Cycle 4 edge on independent evidence.

**Do not erase Cycle 4 failures.** They explain why the next iteration emphasizes statistical detectability, non-overlap validation, and independent alpha over cosmetic score improvements.
