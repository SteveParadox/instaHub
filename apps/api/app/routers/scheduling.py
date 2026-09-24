import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import UserProfile, current_user, require_workspace_access
from app.database import get_db
from app.models import MediaAsset, SocialAccount
from app.publishing_models import Post

router = APIRouter(prefix="/v1", tags=["scheduling"])


class ScheduleIn(BaseModel):
    workspace_id: uuid.UUID
    media_asset_id: uuid.UUID
    caption: str = Field(max_length=2200)
    platform: str = "instagram"
    scheduled_at: datetime
    board_id: str | None = None
    title: str | None = Field(default=None, max_length=100)
    link: str | None = Field(default=None, max_length=2048)


class ScheduleUpdate(BaseModel):
    caption: str | None = Field(default=None, max_length=2200)
    scheduled_at: datetime | None = None
    board_id: str | None = None
    title: str | None = Field(default=None, max_length=100)
    link: str | None = Field(default=None, max_length=2048)


class Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    media_asset_id: uuid.UUID
    status: str
    scheduled_at: datetime | None
    caption: str
    platform: str
    platform_settings: dict


def validate_time(value: datetime):
    if value.tzinfo is None or value <= datetime.now(UTC): raise HTTPException(422, "Choose a future timezone-aware time")


@router.post("/scheduled-posts", response_model=Out)
def create(payload: ScheduleIn, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, payload.workspace_id); validate_time(payload.scheduled_at)
    if payload.platform not in {"instagram", "pinterest"}: raise HTTPException(422, "Unsupported publishing platform")
    if payload.platform == "pinterest" and not payload.board_id: raise HTTPException(422, "Choose a Pinterest board")
    asset = db.scalar(select(MediaAsset).where(MediaAsset.id == payload.media_asset_id, MediaAsset.workspace_id == payload.workspace_id))
    if not asset: raise HTTPException(404, "Asset not found")
    account = db.scalar(select(SocialAccount.id).where(SocialAccount.workspace_id == payload.workspace_id, SocialAccount.platform == payload.platform, SocialAccount.is_active.is_(True)))
    if not account: raise HTTPException(409, f"Connect {payload.platform.title()} before scheduling")
    post = Post(workspace_id=payload.workspace_id, media_asset_id=payload.media_asset_id, caption=payload.caption, platform=payload.platform, platform_settings={"board_id": payload.board_id, "title": payload.title, "link": payload.link}, status="scheduled", scheduled_at=payload.scheduled_at.astimezone(UTC), created_by=user.id)
    db.add(post); db.commit(); db.refresh(post); return post


@router.get("/workspaces/{workspace_id}/scheduled-posts", response_model=list[Out])
def list_posts(workspace_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, workspace_id)
    return list(db.scalars(select(Post).where(Post.workspace_id == workspace_id, Post.status.in_(("scheduled", "queued", "publishing"))).order_by(Post.scheduled_at)))


@router.patch("/scheduled-posts/{post_id}", response_model=Out)
def edit(post_id: uuid.UUID, payload: ScheduleUpdate, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post or post.status != "scheduled": raise HTTPException(404, "Scheduled post not found")
    require_workspace_access(db, user, post.workspace_id)
    if payload.scheduled_at is not None: validate_time(payload.scheduled_at); post.scheduled_at = payload.scheduled_at.astimezone(UTC)
    if payload.caption is not None: post.caption = payload.caption
    values = post.platform_settings.copy()
    for key in ("board_id", "title", "link"):
        value = getattr(payload, key)
        if value is not None: values[key] = value
    post.platform_settings = values; db.commit(); db.refresh(post); return post


@router.delete("/scheduled-posts/{post_id}", status_code=204)
def cancel(post_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post or post.status != "scheduled": raise HTTPException(404, "Scheduled post not found")
    require_workspace_access(db, user, post.workspace_id); post.status = "cancelled"; db.commit()
