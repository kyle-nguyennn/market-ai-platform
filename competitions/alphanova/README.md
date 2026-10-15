# AlphaNova competition research workspace

## Season 1 cycle status

- [Cycle 4 retrospective](CYCLE4_RETROSPECTIVE.md) — **closed**; the only submitted P4 signal failed AlphaNova's server overfitting gate. The framework is validated, not a winning strategy.
- [Cycle 5 kickoff and acceptance plan](CYCLE5_KICKOFF.md) — starts with the official Cycle 5 kit and new unobserved validation evidence; do not assume the target or API remains unchanged.
- [P0–P3 implementation and research plan](IMPLEMENTATION_RESEARCH_PLAN.md).
- [P4 anonymous feature discovery](research/FEATURE_DISCOVERY.md).
- [P5 parallel null and regime research handoff](research/P5_HANDOFF.md).

The original `external/alphanova-2026-cycle4/` kit and Git LFS binaries are left unchanged. The `research/` modules may share dependencies; `submissions/` must remain single-class standalone `Predictor` scripts. All Cycle 4 submission candidates are **research artifacts**, not accepted competition signals.

## Reproduce previous experiment results

From repository root, with AlphaNova Cycle 4 LFS binaries materialized:

```bash
git lfs pull
python -m pytest competitions/alphanova/tests -q
python -m competitions.alphanova.research.run_experiments --scope latest
python -m competitions.alphanova.research.run_p5a_null
python -m competitions.alphanova.research.run_p5b_regimes
```

Use `--output-dir` to preserve separate experiment results. GitHub Actions stores CSV/log artifacts; generated outputs are not checked into Git. Full-history official `runner.py --full` and novelty `--gauge-fix` are the acceptance harness, but neither substitutes for the private shuffled-label gate.

## Merge contract

A successful PR merge delivers reproducible research code, dataset parity tests, unit tests, archived results and a Cycle 5 runbook. It does **not** promote the weak P4 or P5 candidates for resubmission. Keep experiment scores, selected parameters, and validation-period exposure explicit.
