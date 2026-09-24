import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import UserProfile, current_user, require_workspace_access
from app.connectors import provider_key
from app.database import get_db
from app.models import CaptionDraft, Workspace
from app.settings import settings
from app.usage_models import UsageEvent

router = APIRouter(prefix="/v1", tags=["caption assistant"])
TONES = {"Professional", "Playful", "Bold", "Educational", "Luxury"}
CTAS = {"Ask a question", "Visit link in bio", "Save this post", "Shop now", "No CTA"}


class Create(BaseModel):
    workspace_id: uuid.UUID
    source_text: str = Field(min_length=3, max_length=4000)
    tone: str = "Playful"
    cta: str = "Ask a question"
    length: str = "short"
    emojis: bool = True


class Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    caption: str
    hashtags: list[str]
    settings_json: dict


@router.post("/captions", response_model=Out)
def create(payload: Create, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, payload.workspace_id)
    if payload.tone not in TONES or payload.cta not in CTAS or payload.length not in {"short", "long"}:
        raise HTTPException(422, "Unsupported caption option")
    workspace = db.get(Workspace, payload.workspace_id)
    if workspace.default_provider != "openai":
        raise HTTPException(409, "The selected provider does not support captions yet")
    try:
        key = provider_key(db, payload.workspace_id, "openai")
        instruction = f"Write an Instagram {payload.length} caption in a {payload.tone} tone. CTA: {payload.cta}. Emojis: {'allowed' if payload.emojis else 'do not use any'}. Return strict JSON with caption and hashtags where hashtags is an array of 8 to 15 strings, each beginning #."
        response = OpenAI(api_key=key).chat.completions.create(model=settings.openai_text_model, response_format={"type": "json_object"}, messages=[{"role": "system", "content": instruction}, {"role": "user", "content": payload.source_text}])
        data = json.loads(response.choices[0].message.content or "{}")
        caption = str(data["caption"]).strip()
        hashtags = [str(tag).strip() for tag in data["hashtags"] if str(tag).strip()]
        hashtags = [tag if tag.startswith("#") else f"#{tag}" for tag in hashtags][:15]
        if not caption or not hashtags: raise ValueError("empty provider response")
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(502, "Caption provider returned invalid content") from exc
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc
    draft = CaptionDraft(workspace_id=payload.workspace_id, source_text=payload.source_text, caption=caption, hashtags=hashtags, settings_json={"tone": payload.tone, "cta": payload.cta, "length": payload.length, "emojis": payload.emojis}, created_by=user.id)
    db.add(draft); db.add(UsageEvent(workspace_id=payload.workspace_id, user_id=user.id, event_type="caption_generation", provider_name="openai", credits_used=1, metadata_json={"model": settings.openai_text_model})); db.commit(); db.refresh(draft); return draft


@router.get("/workspaces/{workspace_id}/captions", response_model=list[Out])
def history(workspace_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, workspace_id)
    return list(db.scalars(select(CaptionDraft).where(CaptionDraft.workspace_id == workspace_id).order_by(CaptionDraft.created_at.desc()).limit(50)))
