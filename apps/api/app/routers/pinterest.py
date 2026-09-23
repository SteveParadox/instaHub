import uuid,secrets
from datetime import datetime,timezone,timedelta
from urllib.parse import urlencode
import httpx
from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeTimedSerializer,BadData
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.connectors import decrypt,encrypt
from app.database import get_db
from app.main import UserProfile,current_user
from app.models import MediaAsset,SocialAccount
from app.publishing_models import Post,PublishAttempt
from app.settings import settings
from app.tasks import celery
router=APIRouter(prefix="/v1/pinterest",tags=["pinterest"])
def state():return URLSafeTimedSerializer(settings.credential_encryption_key,salt="pinterest-oauth")
@router.get("/connect")
def connect(workspace_id:uuid.UUID,user:UserProfile=Depends(current_user)):
 if not settings.pinterest_app_id:raise HTTPException(503,"Pinterest OAuth is not configured")
 s=state().dumps({"workspace_id":str(workspace_id),"user_id":user.id})
 q=urlencode({"client_id":settings.pinterest_app_id,"redirect_uri":settings.pinterest_redirect_uri,"response_type":"code","scope":"pins:read,pins:write,boards:read,user_accounts:read","state":s});return {"authorization_url":"https://www.pinterest.com/oauth/?"+q}
@router.get("/callback")
async def callback(code:str,state:str,db:Session=Depends(get_db)):
 try:p=state().loads(state,max_age=600);workspace=uuid.UUID(p["workspace_id"])
 except (BadData,KeyError,ValueError):raise HTTPException(400,"Invalid OAuth state")
 async with httpx.AsyncClient(timeout=20) as c:
  token=await c.post("https://api.pinterest.com/v5/oauth/token",data={"grant_type":"authorization_code","code":code,"redirect_uri":settings.pinterest_redirect_uri},auth=(settings.pinterest_app_id,settings.pinterest_app_secret));token.raise_for_status();t=token.json()
  me=await c.get("https://api.pinterest.com/v5/user_account",headers={"Authorization":"Bearer "+t["access_token"]});me.raise_for_status();profile=me.json()
 a=db.scalar(select(SocialAccount).where(SocialAccount.workspace_id==workspace,SocialAccount.platform=="pinterest",SocialAccount.external_account_id==profile["username"]))
 expires=datetime.now(timezone.utc)+timedelta(seconds=t.get("expires_in",2592000))
 if a:a.encrypted_access_token=encrypt(t["access_token"]);a.encrypted_refresh_token=encrypt(t["refresh_token"]) if t.get("refresh_token") else None;a.token_expires_at=expires;a.account_name=profile["username"]
 else:db.add(SocialAccount(workspace_id=workspace,platform="pinterest",account_name=profile["username"],external_account_id=profile["username"],encrypted_access_token=encrypt(t["access_token"]),encrypted_refresh_token=encrypt(t["refresh_token"]) if t.get("refresh_token") else None,token_expires_at=expires,metadata_json=profile))
 db.commit();return RedirectResponse(settings.web_origin+"/pinterest?connected=1")
class PinIn(BaseModel):workspace_id:uuid.UUID;media_asset_id:uuid.UUID;board_id:str;title:str=Field(max_length=100);description:str=Field(max_length=800);link:str|None=None
@celery.task(name="instahub.publish_pinterest",autoretry_for=(httpx.HTTPError,),retry_backoff=True,retry_kwargs={"max_retries":3})
def publish(attempt_id:str):
 db=SessionLocal()
@router.post("/pins")
def pin(p:PinIn,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 asset=db.get(MediaAsset,p.media_asset_id);a=db.scalar(select(SocialAccount).where(SocialAccount.workspace_id==p.workspace_id,SocialAccount.platform=="pinterest"))
 if not asset or not a:raise HTTPException(409,"Asset or Pinterest connection unavailable")
 r=httpx.post("https://api.pinterest.com/v5/pins",headers={"Authorization":"Bearer "+decrypt(a.encrypted_access_token)},json={"board_id":p.board_id,"title":p.title,"description":p.description,"link":p.link,"media_source":{"source_type":"image_url","url":asset.delivery_url}},timeout=30)
 if r.is_error:raise HTTPException(502,r.text)
 return {"status":"published","pin":r.json()}
