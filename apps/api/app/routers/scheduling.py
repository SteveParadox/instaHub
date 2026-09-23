import uuid
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.main import UserProfile,current_user
from app.publishing_models import Post
router=APIRouter(prefix="/v1",tags=["scheduling"])
class ScheduleIn(BaseModel):workspace_id:uuid.UUID;media_asset_id:uuid.UUID;caption:str=Field(max_length=2200);platform:str="instagram";scheduled_at:datetime
class Out(BaseModel):
 id:uuid.UUID;status:str;scheduled_at:datetime|None;caption:str;platform:str
 class Config:from_attributes=True
@router.post("/scheduled-posts",response_model=Out)
def create(p:ScheduleIn,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 if p.scheduled_at.tzinfo is None or p.scheduled_at<=datetime.now(timezone.utc):raise HTTPException(422,"Choose a future timezone-aware time")
 post=Post(workspace_id=p.workspace_id,media_asset_id=p.media_asset_id,caption=p.caption,platform=p.platform,status="scheduled",scheduled_at=p.scheduled_at);db.add(post);db.commit();db.refresh(post);return post
@router.get("/workspaces/{workspace_id}/scheduled-posts",response_model=list[Out])
def list_posts(workspace_id:uuid.UUID,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 return list(db.scalars(select(Post).where(Post.workspace_id==workspace_id,Post.status=="scheduled").order_by(Post.scheduled_at)))
@router.patch("/scheduled-posts/{post_id}",response_model=Out)
def edit(post_id:uuid.UUID,p:ScheduleIn,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 post=db.get(Post,post_id)
 if not post or post.status!="scheduled":raise HTTPException(404,"Scheduled post not found")
 post.caption=p.caption;post.scheduled_at=p.scheduled_at;db.commit();return post
@router.delete("/scheduled-posts/{post_id}",status_code=204)
def cancel(post_id:uuid.UUID,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 post=db.get(Post,post_id)
 if not post or post.status!="scheduled":raise HTTPException(404,"Scheduled post not found")
 post.status="cancelled";db.commit()
