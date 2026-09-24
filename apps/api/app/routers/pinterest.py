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
from app.connectors import decrypt, encrypt
from app.database import get_db
from app.models import SocialAccount, WorkspaceMember
from app.settings import settings

router = APIRouter(prefix="/v1/pinterest", tags=["pinterest"])


def serializer():
    if not settings.state_secret: raise HTTPException(503, "OAuth state signing is not configured")
    return URLSafeTimedSerializer(settings.state_secret, salt="pinterest-oauth")


@router.get("/connect")
def connect(workspace_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, workspace_id)
    if not all((settings.pinterest_app_id, settings.pinterest_app_secret, settings.pinterest_redirect_uri)): raise HTTPException(503, "Pinterest OAuth is not configured")
    state = serializer().dumps({"workspace_id": str(workspace_id), "user_id": user.id})
    query = urlencode({"client_id": settings.pinterest_app_id, "redirect_uri": settings.pinterest_redirect_uri, "response_type": "code", "scope": "pins:read,pins:write,boards:read,user_accounts:read", "state": state})
    return {"authorization_url": "https://www.pinterest.com/oauth/?" + query}


@router.get("/callback")
async def callback(code: str, state: str, db: Session = Depends(get_db)):
    try:
        payload = serializer().loads(state, max_age=600); workspace_id = uuid.UUID(payload["workspace_id"]); user_id = payload["user_id"]
    except (BadData, KeyError, ValueError) as exc: raise HTTPException(400, "Invalid OAuth state") from exc
    if not db.scalar(select(WorkspaceMember.id).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id)): raise HTTPException(400, "Workspace access no longer exists")
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            token = await client.post("https://api.pinterest.com/v5/oauth/token", data={"grant_type": "authorization_code", "code": code, "redirect_uri": settings.pinterest_redirect_uri}, auth=(settings.pinterest_app_id, settings.pinterest_app_secret)); token.raise_for_status(); data = token.json()
            me = await client.get("https://api.pinterest.com/v5/user_account", headers={"Authorization": "Bearer " + data["access_token"]}); me.raise_for_status(); profile = me.json()
    except (httpx.HTTPError, KeyError) as exc: raise HTTPException(502, "Pinterest authorization could not be completed") from exc
    external_id = profile.get("id") or profile["username"]
    account = db.scalar(select(SocialAccount).where(SocialAccount.workspace_id == workspace_id, SocialAccount.platform == "pinterest", SocialAccount.external_account_id == external_id))
    expires = datetime.now(UTC) + timedelta(seconds=data.get("expires_in", 2592000))
    values = {"encrypted_access_token": encrypt(data["access_token"]), "encrypted_refresh_token": encrypt(data["refresh_token"]) if data.get("refresh_token") else None, "token_expires_at": expires, "account_name": profile.get("username", "Pinterest"), "metadata_json": profile, "is_active": True}
    if account:
        for key, value in values.items(): setattr(account, key, value)
    else: db.add(SocialAccount(workspace_id=workspace_id, platform="pinterest", external_account_id=external_id, **values))
    db.commit(); return RedirectResponse(settings.web_origin + "/pinterest?connected=1")


class PinterestStatus(BaseModel): account_name: str; expires_at: datetime | None


@router.get("/status", response_model=PinterestStatus | None)
def account_status(workspace_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, workspace_id)
    account = db.scalar(select(SocialAccount).where(SocialAccount.workspace_id == workspace_id, SocialAccount.platform == "pinterest", SocialAccount.is_active.is_(True)))
    return None if not account else PinterestStatus(account_name=account.account_name, expires_at=account.token_expires_at)


@router.get("/boards")
def boards(workspace_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, workspace_id)
    account = db.scalar(select(SocialAccount).where(SocialAccount.workspace_id == workspace_id, SocialAccount.platform == "pinterest", SocialAccount.is_active.is_(True)))
    if not account: raise HTTPException(404, "Pinterest account not connected")
    try:
        response = httpx.get("https://api.pinterest.com/v5/boards", headers={"Authorization": "Bearer " + decrypt(account.encrypted_access_token)}, params={"page_size": 100}, timeout=20); response.raise_for_status(); return response.json().get("items", [])
    except (httpx.HTTPError, RuntimeError) as exc: raise HTTPException(502, "Pinterest boards could not be loaded") from exc
