"""Dataset CRUD API."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from libs.common.ids import new_uuid
from libs.contracts.dataset import DatasetRecord, DatasetSpec

router = APIRouter()

# In-memory store for scaffolding — replace with metadata_store calls.
_datasets: dict[str, DatasetRecord] = {}


@router.get("/", response_model=list[DatasetRecord])
async def list_datasets() -> list[DatasetRecord]:
    return list(_datasets.values())


@router.post("/", response_model=DatasetRecord, status_code=status.HTTP_201_CREATED)
async def create_dataset(spec: DatasetSpec) -> DatasetRecord:
    record = DatasetRecord(id=new_uuid(), spec=spec)
    _datasets[record.id] = record
    return record


@router.get("/{dataset_id}", response_model=DatasetRecord)
async def get_dataset(dataset_id: str) -> DatasetRecord:
    record = _datasets.get(dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    return record


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(dataset_id: str) -> None:
    if dataset_id not in _datasets:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    del _datasets[dataset_id]
