import uuid
from fastapi import APIRouter,Depends,HTTPException,status
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.main import UserProfile,current_user
from app.provider_registry import resolve
from app.video_models import VideoGenerationJob
router=APIRouter(prefix="/v1",tags=["video generation"])
class Create(BaseModel):
 workspace_id:uuid.UUID;prompt:str=Field(min_length=3,max_length=4000);provider_name:str="fal";model_name:str="";duration_seconds:int=Field(default=5,ge=2,le=20);fps:int=Field(default=24,ge=12,le=60);aspect_ratio:str="9:16";motion_strength:float=Field(default=.5,ge=0,le=1);reference_asset_ids:list[str]=[]
class Out(BaseModel):
 id:uuid.UUID;status:str;progress_percent:int;provider_name:str;model_name:str;error_message:str|None
 class Config:from_attributes=True
@router.post("/video-generation-jobs",response_model=Out,status_code=status.HTTP_202_ACCEPTED)
def create(p:Create,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 provider=resolve(p.provider_name)
 if "video_generation" not in provider.capabilities:raise HTTPException(422,"Selected provider does not support video generation")
 job=VideoGenerationJob(workspace_id=p.workspace_id,provider_name=provider.name,model_name=p.model_name or "provider-default",prompt=p.prompt,created_by=user.id,settings_json=p.model_dump(exclude={"workspace_id","prompt","provider_name","model_name"}));db.add(job);db.commit();db.refresh(job);return job
@router.get("/video-generation-jobs/{job_id}",response_model=Out)
def get(job_id:uuid.UUID,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 job=db.get(VideoGenerationJob,job_id)
 if not job:raise HTTPException(404,"Video job not found")
 return job
