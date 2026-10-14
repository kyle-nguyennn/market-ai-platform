I’d build one reliable signal first, then expand into distinct candidates for later cycles. The priorities are net Sharpe, generalization, novelty, and submission reliability.
1. Set up the project and establish the baseline.
   Keep the supplied files unchanged. Create an isolated Python environment and run the quick validation on demo_engineered.py to confirm dependencies, runtime, and output format.
   Add a separate research directory for experiments and results. Reserve the latest few periods for final evaluation; use earlier periods for development. Because periods are cumulative, restrict development to the earlier files.
   Deliverable: working environment, baseline results, and a fixed validation split.
2. Audit the data and scoring mechanics.
   Examine feature distributions, missing values, zero-target stretches, cross-sectional relationships, and changes between periods. Confirm prediction alignment and the runner’s signal lag and turnover calculation.
   Avoid assigning economic meanings to anonymous features or learning persistent ticker identities. Keep targets, returns, dispersion, and gauge matrices out of inference inputs.
   Deliverable: a short data report identifying useful transformations and data-handling requirements.
3. Build a small set of causal feature families.
   Start with:
   - Same-hour cross-sectional ranks and standardized feature values.
   - Pairwise feature differences and interactions.
   - Relationships between each asset and the cross-sectional distribution.
   - Selected trailing changes and averages, introduced only when they improve validation.
   Begin with contemporaneous features: the baseline documents problems with rolling features inflating the shuffled-data null. Add temporal complexity cautiously.
   Deliverable: reusable feature methods inside the predictor class.
4. Compare low-complexity models.
   Test a regularized linear model and shallow XGBoost models against the supplied baseline. Use shared model parameters across assets, strong regularization, fixed seeds, and a small experiment budget.
   Record configuration, per-period Sharpe, aggregate net Sharpe, gross performance, turnover, and runtime. Favor gains that persist across periods over one unusually strong result.
   Deliverable: a reproducible experiment table and one selected model family.
5. Optimize the actual trading signal.
   Tune causal smoothing and, where justified, removal of persistent asset tilts. Always de-mean the final output.
   Compare improvements in net Sharpe against their gross-versus-net cost gap. Test feature additions and smoothing separately so we can identify what contributes the edge.
   Deliverable: a signal whose advantage survives transaction costs.
6. Check robustness and novelty.
   Test missing values, short batches, overlapping train/predict indices, repeated inference, and permuted rows. These checks should reveal crashes and unintended state changes; they cannot certify passage through the server’s overfitting gate.
   Run gauge evaluation on development periods. Treat city distance as a navigation aid, while remembering that prize selection uses absolute signal correlation. Remove redundant candidates.
   Deliverable: one robust candidate, plus genuinely different alternatives if supported by evidence.
7. Freeze, evaluate, and package.
   Freeze the model and settings before evaluating the reserved periods. If performance falls apart, return to development and acknowledge that the holdout has now been used.
   Create submission.py with all model logic inside its Predictor subclass, declare extra dependencies, and verify serialization and CPU resource use. Run:
   python runner.py submission.py
   python runner.py submission.py --full
   python runner.py submission.py --gauge-fix
   Deliverable: a submission file and a concise report covering performance, novelty, runtime, and remaining uncertainty.
The first milestone should be a reproducible baseline and trustworthy validation setup. The server’s overfitting gate and hidden scoring history remain the final tests; local results alone cannot guarantee acceptance or a prize.