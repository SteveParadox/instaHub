import uuid,secrets
from fastapi import APIRouter,Depends,HTTPException,status
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.main import UserProfile,current_user
from app.models import MediaAsset,SocialAccount
from app.publish_tasks import publish_instagram
from app.publishing_models import Post,PublishAttempt
router=APIRouter(prefix="/v1",tags=["instagram publishing"])
class PublishIn(BaseModel):workspace_id:uuid.UUID;media_asset_id:uuid.UUID;caption:str=Field(max_length=2200)
class AttemptOut(BaseModel):
 id:uuid.UUID;status:str;external_post_id:str|None;error_message:str|None;response_json:dict
 class Config:from_attributes=True
class PostOut(BaseModel):
 id:uuid.UUID;status:str;caption:str;published_at:object|None;attempts:list[AttemptOut]
@router.post("/instagram/posts",response_model=AttemptOut,status_code=status.HTTP_202_ACCEPTED)
def publish(p:PublishIn,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 asset=db.get(MediaAsset,p.media_asset_id)
 if not asset or asset.workspace_id!=p.workspace_id:raise HTTPException(404,"Asset not found")
 account=db.scalar(select(SocialAccount).where(SocialAccount.workspace_id==p.workspace_id,SocialAccount.platform=="instagram",SocialAccount.is_active.is_(True)))
 if not account:raise HTTPException(409,"Connect an eligible Instagram professional account first")
 post=Post(workspace_id=p.workspace_id,media_asset_id=asset.id,caption=p.caption,status="queued");db.add(post);db.flush();attempt=PublishAttempt(post_id=post.id,social_account_id=account.id,idempotency_key=secrets.token_urlsafe(32));db.add(attempt);db.commit();db.refresh(attempt);publish_instagram.delay(str(attempt.id));return attempt
@router.get("/instagram/posts/{post_id}",response_model=PostOut)
def post_status(post_id:uuid.UUID,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 post=db.get(Post,post_id)
 if not post:raise HTTPException(404,"Post not found")
 attempts=list(db.scalars(select(PublishAttempt).where(PublishAttempt.post_id==post.id).order_by(PublishAttempt.created_at.desc())))
 return PostOut(id=post.id,status=post.status,caption=post.caption,published_at=post.published_at,attempts=attempts)
@router.get("/workspaces/{workspace_id}/publish-attempts",response_model=list[AttemptOut])
def logs(workspace_id:uuid.UUID,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 return list(db.scalars(select(PublishAttempt).join(Post).where(Post.workspace_id==workspace_id).order_by(PublishAttempt.created_at.desc()).limit(50)))
