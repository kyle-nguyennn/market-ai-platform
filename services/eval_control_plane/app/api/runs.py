"""Evaluation run trigger and status API."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from libs.common.ids import new_uuid
from libs.contracts.eval_spec import EvalRunRecord, EvalSpec

router = APIRouter()

_runs: dict[str, EvalRunRecord] = {}


@router.post("/", response_model=EvalRunRecord, status_code=status.HTTP_202_ACCEPTED)
async def trigger_eval(spec: EvalSpec) -> EvalRunRecord:
    """Submit an evaluation job. Returns immediately with a run record."""
    run = EvalRunRecord(id=new_uuid(), spec=spec, status="queued")
    _runs[run.id] = run
    # Stub: in production, dispatch to a background worker here.
    return run


@router.get("/", response_model=list[EvalRunRecord])
async def list_runs() -> list[EvalRunRecord]:
    return list(_runs.values())


@router.get("/{run_id}", response_model=EvalRunRecord)
async def get_run(run_id: str) -> EvalRunRecord:
    run = _runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return run
