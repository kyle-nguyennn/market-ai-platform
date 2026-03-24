"""Eval report assembly: combine metrics, slice results, drift, and guards."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from libs.common.ids import new_uuid
from libs.common.time import utc_now
from libs.contracts.eval_spec import (  # noqa: F401  # TODO: persist eval runs via EvalRunRecord
    EvalMetric,
    EvalRunRecord,
    EvalSpec,
)
from libs.eval.drift import DriftReport
from libs.eval.regressions import RegressionGuardResult


@dataclass
class EvalReport:
    run_id: str
    spec_name: str
    model_id: str
    passed: bool
    metrics: list[EvalMetric]
    drift: DriftReport | None
    guards: RegressionGuardResult | None
    created_at: datetime = field(default_factory=utc_now)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "spec_name": self.spec_name,
            "model_id": self.model_id,
            "passed": self.passed,
            "metrics": [m.model_dump() for m in self.metrics],
            "drift_passed": self.drift.passed if self.drift else None,
            "guards_passed": self.guards.passed if self.guards else None,
            "created_at": self.created_at.isoformat(),
            "notes": self.notes,
        }


def build_report(
    spec: EvalSpec,
    slice_metrics: dict[str, dict[str, float]],
    drift: DriftReport | None = None,
    guards: RegressionGuardResult | None = None,
    notes: str = "",
) -> EvalReport:
    """Assemble an :class:`EvalReport` from component results.

    Args:
        spec: The evaluation spec that was run.
        slice_metrics: Mapping of slice name → metric dict.
        drift: Optional drift detection result.
        guards: Optional regression guard result.
        notes: Free-text notes for the report.
    """
    metrics = [
        EvalMetric(name=metric_name, value=value, slice_name=slice_name)
        for slice_name, mdict in slice_metrics.items()
        for metric_name, value in mdict.items()
    ]

    drift_ok = drift.passed if drift else True
    guards_ok = guards.passed if guards else True
    passed = drift_ok and guards_ok

    return EvalReport(
        run_id=new_uuid(),
        spec_name=spec.name,
        model_id=spec.model_id,
        passed=passed,
        metrics=metrics,
        drift=drift,
        guards=guards,
        notes=notes,
    )
