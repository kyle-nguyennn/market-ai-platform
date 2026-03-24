"""Feature definition API."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from libs.common.ids import new_uuid  # noqa: F401  # TODO: assign IDs on feature registration
from libs.contracts.feature_store import FeatureDefinition

router = APIRouter()

_features: dict[str, FeatureDefinition] = {}


@router.get("/", response_model=list[FeatureDefinition])
async def list_features() -> list[FeatureDefinition]:
    return list(_features.values())


@router.post("/", response_model=FeatureDefinition, status_code=status.HTTP_201_CREATED)
async def register_feature(definition: FeatureDefinition) -> FeatureDefinition:
    if definition.name in _features:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Feature '{definition.name}' is already registered.",
        )
    _features[definition.name] = definition
    return definition


@router.get("/{name}", response_model=FeatureDefinition)
async def get_feature(name: str) -> FeatureDefinition:
    feat = _features.get(name)
    if feat is None:
        raise HTTPException(status_code=404, detail=f"Feature '{name}' not found.")
    return feat
