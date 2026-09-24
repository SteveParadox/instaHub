import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from itsdangerous import BadData, URLSafeTimedSerializer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import UserProfile, current_user, require_workspace_access
from app.connectors import encrypt
from app.database import get_db
from app.models import SocialAccount, WorkspaceMember
from app.settings import settings

router = APIRouter(prefix="/v1/instagram", tags=["instagram"])


def serializer():
    if not settings.state_secret: raise HTTPException(503, "OAuth state signing is not configured")
    return URLSafeTimedSerializer(settings.state_secret, salt="instagram-oauth")


@router.get("/connect")
def connect(workspace_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, workspace_id)
    if not all((settings.meta_app_id, settings.meta_app_secret, settings.meta_redirect_uri)): raise HTTPException(503, "Meta OAuth is not configured")
    state = serializer().dumps({"workspace_id": str(workspace_id), "user_id": user.id})
    query = urlencode({"client_id": settings.meta_app_id, "redirect_uri": settings.meta_redirect_uri, "response_type": "code", "scope": "instagram_business_basic,instagram_business_content_publish", "state": state})
    return {"authorization_url": "https://www.instagram.com/oauth/authorize?" + query}


@router.get("/callback")
async def callback(code: str, state: str, db: Session = Depends(get_db)):
    try:
        payload = serializer().loads(state, max_age=600); workspace_id = uuid.UUID(payload["workspace_id"]); user_id = payload["user_id"]
    except (BadData, ValueError, KeyError) as exc: raise HTTPException(400, "Invalid OAuth state") from exc
    if not db.scalar(select(WorkspaceMember.id).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id)): raise HTTPException(400, "Workspace access no longer exists")
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            token = await client.post("https://api.instagram.com/oauth/access_token", data={"client_id": settings.meta_app_id, "client_secret": settings.meta_app_secret, "grant_type": "authorization_code", "redirect_uri": settings.meta_redirect_uri, "code": code}); token.raise_for_status(); short = token.json()
            exchange = await client.get(f"https://graph.instagram.com/{settings.meta_graph_version}/access_token", params={"grant_type": "ig_exchange_token", "client_secret": settings.meta_app_secret, "access_token": short["access_token"]}); exchange.raise_for_status(); data = exchange.json(); access = data["access_token"]
            profile = await client.get(f"https://graph.instagram.com/{settings.meta_graph_version}/me", params={"fields": "id,username,account_type,media_count", "access_token": access}); profile.raise_for_status(); info = profile.json()
    except (httpx.HTTPError, KeyError) as exc: raise HTTPException(502, "Instagram authorization could not be completed") from exc
    if info.get("account_type") not in {"BUSINESS", "CREATOR"}: return RedirectResponse(settings.web_origin + "/instagram?error=ineligible")
    account = db.scalar(select(SocialAccount).where(SocialAccount.workspace_id == workspace_id, SocialAccount.platform == "instagram", SocialAccount.external_account_id == info["id"]))
    expires = datetime.now(UTC) + timedelta(seconds=data.get("expires_in", 5184000))
    if account:
        account.encrypted_access_token = encrypt(access); account.token_expires_at = expires; account.account_name = info.get("username", "Instagram"); account.metadata_json = info; account.is_active = True
    else:
        db.add(SocialAccount(workspace_id=workspace_id, platform="instagram", account_name=info.get("username", "Instagram"), external_account_id=info["id"], encrypted_access_token=encrypt(access), token_expires_at=expires, metadata_json=info))
    db.commit(); return RedirectResponse(settings.web_origin + "/instagram?connected=1")


class Status(BaseModel):
    account_name: str
    account_type: str | None
    expires_at: datetime | None


@router.get("/status", response_model=Status | None)
def account_status(workspace_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, workspace_id)
    account = db.scalar(select(SocialAccount).where(SocialAccount.workspace_id == workspace_id, SocialAccount.platform == "instagram", SocialAccount.is_active.is_(True)))
    return None if not account else Status(account_name=account.account_name, account_type=account.metadata_json.get("account_type"), expires_at=account.token_expires_at)
