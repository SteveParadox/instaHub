import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import UserProfile, current_user, require_workspace_access, require_workspace_owner
from app.connectors import provider_key
from app.database import get_db
from app.provider_registry import providers, resolve
from app.usage_models import UsageEvent

router = APIRouter(prefix="/v1", tags=["AI providers"])


class ProviderOut(BaseModel):
    name: str
    label: str
    models: list[str]
    capabilities: list[str]
    enabled: bool


class DefaultIn(BaseModel): provider_name: str


@router.get("/providers", response_model=list[ProviderOut])
def registry():
    return [ProviderOut(name=p.name, label=p.label, models=list(p.models), capabilities=list(p.capabilities), enabled=p.enabled) for p in providers()]


@router.put("/workspaces/{workspace_id}/default-provider")
def select_default(workspace_id: uuid.UUID, payload: DefaultIn, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    workspace = require_workspace_owner(db, user, workspace_id); selected = resolve(payload.provider_name)
    try: provider_key(db, workspace_id, selected.name)
    except RuntimeError as exc: raise HTTPException(409, str(exc)) from exc
    workspace.default_provider = selected.name; db.commit(); return {"default_provider": selected.name}


@router.get("/workspaces/{workspace_id}/provider-usage")
def usage(workspace_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, workspace_id)
    return list(db.scalars(select(UsageEvent).where(UsageEvent.workspace_id == workspace_id).order_by(UsageEvent.created_at.desc()).limit(100)))
