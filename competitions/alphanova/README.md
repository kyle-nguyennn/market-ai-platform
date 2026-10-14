# AlphaNova research workspace

See [IMPLEMENTATION_RESEARCH_PLAN.md](IMPLEMENTATION_RESEARCH_PLAN.md) for the milestones, constraints and experiment protocol.

The supplied `external/alphanova-2026-cycle4` kit is an immutable reference. Research scripts here can use shared packages, while files under `submissions/` are **self-contained** Predictor classes that can be uploaded individually.

From the repository root:

```bash
git lfs pull
python -m pytest competitions/alphanova/tests -q
python -m competitions.alphanova.research.run_experiments --scope latest
python -m competitions.alphanova.research.run_experiments --scope full
```

Results are written to `competitions/alphanova/results/`. Each invocation overwrites that output directory's `summary.csv`, `per_period.csv` and `manifest.json`, so use `--output-dir` for distinct experiments.

Baseline model: upstream `demo_engineered.py`. P1 candidates: `ridge_v1.py`, `xgb_interactions_v1.py`.
