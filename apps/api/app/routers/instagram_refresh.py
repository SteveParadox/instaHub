import uuid
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import UserProfile, current_user, require_workspace_access
from app.connectors import decrypt, encrypt
from app.database import get_db
from app.models import SocialAccount
from app.settings import settings

router = APIRouter(prefix="/v1/instagram", tags=["instagram"])


@router.post("/refresh")
def refresh(workspace_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, workspace_id)
    account = db.scalar(select(SocialAccount).where(SocialAccount.workspace_id == workspace_id, SocialAccount.platform == "instagram", SocialAccount.is_active.is_(True)))
    if not account: raise HTTPException(404, "Instagram account not connected")
    try:
        response = httpx.get(f"https://graph.instagram.com/{settings.meta_graph_version}/refresh_access_token", params={"grant_type": "ig_refresh_token", "access_token": decrypt(account.encrypted_access_token)}, timeout=20); response.raise_for_status(); data = response.json()
        account.encrypted_access_token = encrypt(data["access_token"])
    except (httpx.HTTPError, KeyError, RuntimeError) as exc: raise HTTPException(502, "Instagram token refresh failed") from exc
    account.token_expires_at = datetime.now(UTC) + timedelta(seconds=data.get("expires_in", 5184000)); db.commit(); return {"status": "refreshed", "expires_at": account.token_expires_at}
