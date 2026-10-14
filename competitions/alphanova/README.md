# AlphaNova research workspace

- [Implementation & Research Plan](IMPLEMENTATION_RESEARCH_PLAN.md): P0-P3 evaluation and submission criteria.
- [P4 Feature Discovery](research/FEATURE_DISCOVERY.md): 48 predeclared same-hour cross-sectional factor hypotheses, strict period selection/confirmation and frozen execution policy.

The original `external/alphanova-2026-cycle4` competition kit is left unchanged. Submit only self-contained classes under `submissions/`; do not import the research package in a submission.

From repository root with Git LFS binaries materialized:

```bash
python -m pytest competitions/alphanova/tests -q
python -m competitions.alphanova.research.run_feature_screen \
    --config competitions/alphanova/configs/p4_factors.json \
    --output-dir competitions/alphanova/results/p4
```

P4's CI workflow downloads precisely the 11 research periods, runs unit tests and uploads structured tables. It does **not** run the hidden server-side overfitting gate or certify an edge.
