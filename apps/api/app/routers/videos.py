import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.auth import UserProfile, current_user, require_workspace_access
from app.database import get_db
from app.models import MediaAsset
from app.provider_registry import REGISTRY
from app.video_models import VideoGenerationJob

router = APIRouter(prefix="/v1", tags=["video generation"])


class Create(BaseModel):
    workspace_id: uuid.UUID
    prompt: str = Field(min_length=3, max_length=4000)
    provider_name: str = "fal"
    model_name: str = ""
    duration_seconds: int = Field(default=5, ge=2, le=20)
    fps: int = Field(default=24, ge=12, le=60)
    aspect_ratio: str = "9:16"
    motion_strength: float = Field(default=.5, ge=0, le=1)
    reference_asset_ids: list[uuid.UUID] = Field(default_factory=list, max_length=4)


class Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    progress_percent: int
    provider_name: str
    model_name: str
    error_message: str | None


@router.post("/video-generation-jobs", response_model=Out, status_code=status.HTTP_202_ACCEPTED)
def create(payload: Create, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, payload.workspace_id)
    provider = REGISTRY.get(payload.provider_name)
    if provider is None:
        raise HTTPException(422, "Unknown AI provider")
    if "video_generation" not in provider.capabilities: raise HTTPException(422, "Selected provider does not support video generation")
    for asset_id in payload.reference_asset_ids:
        asset = db.get(MediaAsset, asset_id)
        if not asset or asset.workspace_id != payload.workspace_id: raise HTTPException(422, "One or more reference assets are invalid")
    job = VideoGenerationJob(workspace_id=payload.workspace_id, provider_name=provider.name, model_name=payload.model_name or "provider-default", prompt=payload.prompt, created_by=user.id, settings_json=payload.model_dump(mode="json", exclude={"workspace_id", "prompt", "provider_name", "model_name"}), status="queued" if provider.enabled else "awaiting_provider")
    db.add(job); db.commit(); db.refresh(job); return job


@router.get("/video-generation-jobs/{job_id}", response_model=Out)
def get(job_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    job = db.get(VideoGenerationJob, job_id)
    if not job: raise HTTPException(404, "Video job not found")
    require_workspace_access(db, user, job.workspace_id); return job
