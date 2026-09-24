import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import UserProfile, current_user, require_workspace_access
from app.database import get_db
from app.models import GenerationJob, MediaAsset, Workspace
from app.provider_registry import resolve
from app.routers.brands import creative_context
from app.settings import settings
from app.tasks import generate_images

router = APIRouter(prefix="/v1", tags=["generation"])
RATIOS = {"1:1", "4:5", "16:9"}
STYLES = {"Photorealistic", "Editorial", "3D render", "Anime", "Minimal product"}


class Create(BaseModel):
    workspace_id: uuid.UUID
    prompt: str = Field(min_length=3, max_length=4000)
    brand_profile_id: uuid.UUID | None = None
    provider_name: str | None = None
    style_preset: str = "Photorealistic"
    aspect_ratio: str = "1:1"
    output_count: int = Field(default=1, ge=1, le=4)


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    media_type: str
    delivery_url: str
    thumbnail_url: str | None
    width: int | None
    height: int | None
    mime_type: str


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    error_message: str | None
    prompt: str
    provider_name: str
    settings_json: dict
    assets: list[AssetOut]


@router.post("/generation-jobs", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def create_generation(payload: Create, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, payload.workspace_id)
    if payload.aspect_ratio not in RATIOS or payload.style_preset not in STYLES:
        raise HTTPException(422, "Unsupported generation setting")
    workspace = db.get(Workspace, payload.workspace_id)
    provider = resolve(payload.provider_name or workspace.default_provider)
    if "image_generation" not in provider.capabilities:
        raise HTTPException(422, "Selected provider cannot generate images")
    prompt = "\n\n".join(x for x in [creative_context(db, payload.workspace_id, payload.brand_profile_id), payload.prompt] if x)
    job = GenerationJob(workspace_id=payload.workspace_id, provider_name=provider.name, model_name=settings.openai_image_model, prompt=prompt, created_by=user.id, settings_json={"brand_profile_id": str(payload.brand_profile_id) if payload.brand_profile_id else None, "style_preset": payload.style_preset, "aspect_ratio": payload.aspect_ratio, "output_count": payload.output_count})
    db.add(job); db.commit(); db.refresh(job)
    try:
        generate_images.delay(str(job.id))
    except Exception as exc:
        job.status = "failed"; job.error_message = "Generation queue is unavailable"; db.commit()
        raise HTTPException(503, "Generation queue is unavailable") from exc
    return job


@router.get("/generation-jobs/{job_id}", response_model=JobOut)
def get_job(job_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    job = db.scalar(select(GenerationJob).options(selectinload(GenerationJob.assets)).where(GenerationJob.id == job_id))
    if not job: raise HTTPException(404, "Generation job not found")
    require_workspace_access(db, user, job.workspace_id); return job


@router.get("/workspaces/{workspace_id}/assets", response_model=list[AssetOut])
def assets(workspace_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, workspace_id)
    return list(db.scalars(select(MediaAsset).where(MediaAsset.workspace_id == workspace_id).order_by(MediaAsset.created_at.desc()).limit(100)))
