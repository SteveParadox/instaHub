import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAI
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import UserProfile, current_user, require_workspace_access, require_workspace_owner
from app.connectors import encrypt
from app.database import get_db
from app.models import AIProviderAccount
from app.provider_registry import REGISTRY
from app.settings import settings

router = APIRouter(prefix="/v1", tags=["AI connectors"])


class ProviderOut(BaseModel):
    provider_name: str
    label: str
    is_connected: bool
    capabilities: list[str]
    enabled: bool


class ConnectOpenAI(BaseModel):
    api_key: str = Field(min_length=20, max_length=500)


@router.get("/workspaces/{workspace_id}/ai-providers", response_model=list[ProviderOut])
def list_connections(workspace_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, workspace_id)
    active = {x.provider_name for x in db.scalars(select(AIProviderAccount).where(AIProviderAccount.workspace_id == workspace_id, AIProviderAccount.is_active.is_(True)))}
    return [ProviderOut(provider_name=p.name, label=p.label, is_connected=p.name in active or (p.name == "openai" and bool(settings.openai_api_key)), capabilities=list(p.capabilities), enabled=p.enabled) for p in REGISTRY.values()]


@router.put("/workspaces/{workspace_id}/ai-providers/openai", response_model=ProviderOut)
def connect_openai(workspace_id: uuid.UUID, payload: ConnectOpenAI, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_owner(db, user, workspace_id)
    try:
        OpenAI(api_key=payload.api_key).models.list()
    except Exception as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "OpenAI could not validate this API key") from exc
    account = db.scalar(select(AIProviderAccount).where(AIProviderAccount.workspace_id == workspace_id, AIProviderAccount.provider_name == "openai"))
    if account:
        account.encrypted_api_key = encrypt(payload.api_key); account.is_active = True
    else:
        db.add(AIProviderAccount(workspace_id=workspace_id, provider_name="openai", encrypted_api_key=encrypt(payload.api_key)))
    db.commit(); provider = REGISTRY["openai"]
    return ProviderOut(provider_name=provider.name, label=provider.label, is_connected=True, capabilities=list(provider.capabilities), enabled=True)


@router.delete("/workspaces/{workspace_id}/ai-providers/openai", status_code=204)
def disconnect_openai(workspace_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_owner(db, user, workspace_id)
    account = db.scalar(select(AIProviderAccount).where(AIProviderAccount.workspace_id == workspace_id, AIProviderAccount.provider_name == "openai"))
    if account:
        account.is_active = False; db.commit()
