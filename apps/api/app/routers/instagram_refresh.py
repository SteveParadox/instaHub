from datetime import datetime,timezone,timedelta
import httpx
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.connectors import decrypt,encrypt
from app.database import get_db
from app.main import UserProfile,current_user
from app.models import SocialAccount
from app.settings import settings
router=APIRouter(prefix="/v1/instagram",tags=["instagram"])
@router.post("/refresh")
def refresh(workspace_id:str,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 a=db.scalar(select(SocialAccount).where(SocialAccount.workspace_id==workspace_id,SocialAccount.platform=="instagram",SocialAccount.is_active.is_(True)))
 if not a:raise HTTPException(404,"Instagram account not connected")
 r=httpx.get(f"https://graph.instagram.com/{settings.meta_graph_version}/refresh_access_token",params={"grant_type":"ig_refresh_token","access_token":decrypt(a.encrypted_access_token)},timeout=20)
 if r.is_error:raise HTTPException(502,"Instagram token refresh failed")
 data=r.json();a.encrypted_access_token=encrypt(data["access_token"]);a.token_expires_at=datetime.now(timezone.utc)+timedelta(seconds=data.get("expires_in",5184000));db.commit();return {"status":"refreshed","expires_at":a.token_expires_at}
