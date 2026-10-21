# Research experiments

This directory organizes experiment **configurations** and reproducibility
metadata. Reuse existing `notebooks/` and `libs/eval/` functionality rather
than creating parallel systems.

For every run, record: data snapshot, point-in-time cutoff, code revision,
feature/signal/strategy versions, model artifact, configuration, seed,
backtest engine, cost assumptions, and evaluation metrics.

`configs/` holds checked-in experiment definitions.
`results/` is a local scratch output location and is git-ignored.
Large trained models and datasets should use external artifact storage, not
ordinary Git. Competition-provided files stay in `external/` until separately
integrated.
