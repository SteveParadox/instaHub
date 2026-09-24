import secrets
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import UserProfile, current_user, require_workspace_access
from app.database import get_db
from app.models import MediaAsset, SocialAccount
from app.publish_tasks import queue_publish
from app.publishing_models import Post, PublishAttempt

router = APIRouter(prefix="/v1", tags=["publishing"])


class PublishIn(BaseModel):
    workspace_id: uuid.UUID
    media_asset_id: uuid.UUID
    platform: str = "instagram"
    caption: str = Field(max_length=2200)
    board_id: str | None = None
    title: str | None = Field(default=None, max_length=100)
    link: str | None = Field(default=None, max_length=2048)


class AttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    post_id: uuid.UUID
    status: str
    external_post_id: str | None
    error_message: str | None
    response_json: dict
    retry_count: int


class PostOut(BaseModel):
    id: uuid.UUID
    status: str
    platform: str
    caption: str
    published_at: datetime | None
    attempts: list[AttemptOut]


@router.post("/posts", response_model=AttemptOut, status_code=status.HTTP_202_ACCEPTED)
@router.post("/instagram/posts", response_model=AttemptOut, status_code=status.HTTP_202_ACCEPTED, include_in_schema=False)
def publish(payload: PublishIn, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, payload.workspace_id)
    if payload.platform not in {"instagram", "pinterest"}: raise HTTPException(422, "Unsupported publishing platform")
    if payload.platform == "pinterest" and not payload.board_id: raise HTTPException(422, "Choose a Pinterest board")
    asset = db.scalar(select(MediaAsset).where(MediaAsset.id == payload.media_asset_id, MediaAsset.workspace_id == payload.workspace_id))
    if not asset: raise HTTPException(404, "Asset not found")
    if payload.platform == "pinterest" and asset.media_type != "image": raise HTTPException(422, "Pinterest video publishing is not enabled yet")
    account = db.scalar(select(SocialAccount).where(SocialAccount.workspace_id == payload.workspace_id, SocialAccount.platform == payload.platform, SocialAccount.is_active.is_(True)))
    if not account: raise HTTPException(409, f"Connect {payload.platform.title()} first")
    post = Post(workspace_id=payload.workspace_id, media_asset_id=asset.id, caption=payload.caption, platform=payload.platform, platform_settings={"board_id": payload.board_id, "title": payload.title, "link": payload.link}, status="queued", created_by=user.id)
    db.add(post); db.flush(); attempt = PublishAttempt(post_id=post.id, social_account_id=account.id, idempotency_key=secrets.token_urlsafe(32)); db.add(attempt); db.commit(); db.refresh(attempt)
    try: queue_publish(attempt, payload.platform)
    except Exception as exc:
        attempt.status = "failed"; attempt.error_message = "Publishing queue is unavailable"; post.status = "failed"; db.commit(); raise HTTPException(503, "Publishing queue is unavailable") from exc
    return attempt


@router.get("/posts/{post_id}", response_model=PostOut)
@router.get("/instagram/posts/{post_id}", response_model=PostOut, include_in_schema=False)
def post_status(post_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post: raise HTTPException(404, "Post not found")
    require_workspace_access(db, user, post.workspace_id)
    attempts = list(db.scalars(select(PublishAttempt).where(PublishAttempt.post_id == post.id).order_by(PublishAttempt.created_at.desc())))
    return PostOut(id=post.id, status=post.status, platform=post.platform, caption=post.caption, published_at=post.published_at, attempts=attempts)


@router.get("/workspaces/{workspace_id}/publish-attempts", response_model=list[AttemptOut])
def logs(workspace_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, workspace_id)
    return list(db.scalars(select(PublishAttempt).join(Post).where(Post.workspace_id == workspace_id).order_by(PublishAttempt.created_at.desc()).limit(50)))
