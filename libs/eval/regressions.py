"""Regression guard checks: block model promotion if key metrics regress."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RegressionGuardResult:
    passed: bool
    violations: dict[str, tuple[float, float]] = field(default_factory=dict)
    # metric_name -> (threshold, actual_value)


def check_regression_guards(
    metrics: dict[str, float],
    guards: dict[str, float],
) -> RegressionGuardResult:
    """Verify that each guarded metric meets its minimum threshold.

    Args:
        metrics: Computed metrics from the eval run.
        guards: Mapping of metric name to the minimum acceptable value.
                Example: ``{"roc_auc": 0.60, "f1": 0.45}``.

    Returns:
        A :class:`RegressionGuardResult` listing any violated constraints.
    """
    violations: dict[str, tuple[float, float]] = {}

    for metric_name, threshold in guards.items():
        actual = metrics.get(metric_name)
        if actual is None:
            violations[metric_name] = (threshold, float("nan"))
        elif actual < threshold:
            violations[metric_name] = (threshold, actual)

    return RegressionGuardResult(passed=not violations, violations=violations)
