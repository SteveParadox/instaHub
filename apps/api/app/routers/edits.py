import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import UserProfile, current_user, require_workspace_access
from app.database import get_db
from app.models import AssetOperation, AssetVariant, MediaAsset
from app.tasks_edits import edit_asset

router = APIRouter(prefix="/v1", tags=["image editing"])
OPS = {"variation", "upscale", "edit", "crop", "background_remove"}
RATIOS = {"1:1", "4:5", "9:16", "16:9"}


class EditIn(BaseModel):
    operation: str
    prompt: str | None = Field(default=None, max_length=4000)
    aspect_ratio: str | None = None
    factor: int = Field(default=2, ge=2, le=4)

    @model_validator(mode="after")
    def validate_operation(self):
        if self.operation not in OPS: raise ValueError("Unsupported edit operation")
        if self.operation == "edit" and not self.prompt: raise ValueError("A prompt is required for prompt-based edits")
        if self.operation == "crop" and self.aspect_ratio not in RATIOS: raise ValueError("Choose a supported crop ratio")
        return self


class VariantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    operation: str
    delivery_url: str
    width: int | None
    height: int | None
    metadata_json: dict


class OperationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    error_message: str | None
    variant_id: uuid.UUID | None


@router.post("/assets/{asset_id}/operations", response_model=OperationOut, status_code=status.HTTP_202_ACCEPTED)
def create(asset_id: uuid.UUID, payload: EditIn, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    asset = db.get(MediaAsset, asset_id)
    if not asset or asset.media_type != "image": raise HTTPException(404, "Image asset not found")
    require_workspace_access(db, user, asset.workspace_id)
    operation = AssetOperation(asset_id=asset_id, operation=payload.operation, created_by=user.id, settings_json=payload.model_dump(exclude_none=True)); db.add(operation); db.commit(); db.refresh(operation)
    try: edit_asset.delay(str(operation.id))
    except Exception as exc:
        operation.status = "failed"; operation.error_message = "Editing queue is unavailable"; db.commit(); raise HTTPException(503, "Editing queue is unavailable") from exc
    return operation


@router.get("/asset-operations/{operation_id}", response_model=OperationOut)
def operation(operation_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    op = db.get(AssetOperation, operation_id)
    if not op: raise HTTPException(404, "Operation not found")
    asset = db.get(MediaAsset, op.asset_id); require_workspace_access(db, user, asset.workspace_id); return op


@router.get("/assets/{asset_id}/variants", response_model=list[VariantOut])
def variants(asset_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    asset = db.get(MediaAsset, asset_id)
    if not asset: raise HTTPException(404, "Asset not found")
    require_workspace_access(db, user, asset.workspace_id)
    return list(db.scalars(select(AssetVariant).where(AssetVariant.parent_asset_id == asset_id).order_by(AssetVariant.created_at.desc())))
