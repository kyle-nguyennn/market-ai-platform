"""Data quality report API."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class QualityReport(BaseModel):
    dataset_id: str
    passed: bool
    null_violations: dict[str, float] = {}
    schema_errors: list[str] = []
    staleness_ok: bool = True
    notes: str = ""


_reports: dict[str, QualityReport] = {}


@router.get("/{dataset_id}", response_model=QualityReport)
async def get_quality_report(dataset_id: str) -> QualityReport:
    report = _reports.get(dataset_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"No quality report for dataset '{dataset_id}'.")
    return report


@router.post("/", response_model=QualityReport, status_code=status.HTTP_201_CREATED)
async def submit_quality_report(report: QualityReport) -> QualityReport:
    _reports[report.dataset_id] = report
    return report
