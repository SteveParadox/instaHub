import uuid
from fastapi import APIRouter,Depends,HTTPException,status
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session,selectinload
from app.database import get_db
from app.main import UserProfile,current_user
from app.models import GenerationJob,MediaAsset
from app.routers.brands import creative_context
from app.settings import settings
from app.tasks import generate_images
router=APIRouter(prefix="/v1",tags=["generation"]);RATIOS={"1:1","4:5","16:9"};STYLES={"Photorealistic","Editorial","3D render","Anime","Minimal product"}
class Create(BaseModel): workspace_id:uuid.UUID;prompt:str=Field(min_length=3,max_length=4000);brand_profile_id:uuid.UUID|None=None;style_preset:str="Photorealistic";aspect_ratio:str="1:1";output_count:int=Field(default=1,ge=1,le=4)
class AssetOut(BaseModel):
 id:uuid.UUID;delivery_url:str;width:int|None;height:int|None;mime_type:str
 class Config:from_attributes=True
class JobOut(BaseModel):
 id:uuid.UUID;status:str;error_message:str|None;prompt:str;settings_json:dict;assets:list[AssetOut]
 class Config:from_attributes=True
@router.post("/generation-jobs",response_model=JobOut,status_code=status.HTTP_202_ACCEPTED)
def create_generation(p:Create,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 if p.aspect_ratio not in RATIOS or p.style_preset not in STYLES:raise HTTPException(422,"Unsupported generation setting")
 prompt="\n\n".join(x for x in [creative_context(db,p.brand_profile_id),p.prompt] if x)
 job=GenerationJob(workspace_id=p.workspace_id,provider_name="openai",model_name=settings.openai_image_model,prompt=prompt,created_by=user.id,settings_json={"brand_profile_id":str(p.brand_profile_id) if p.brand_profile_id else None,"style_preset":p.style_preset,"aspect_ratio":p.aspect_ratio,"output_count":p.output_count});db.add(job);db.commit();db.refresh(job);generate_images.delay(str(job.id));return job
@router.get("/generation-jobs/{job_id}",response_model=JobOut)
def get_job(job_id:uuid.UUID,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 job=db.scalar(select(GenerationJob).options(selectinload(GenerationJob.assets)).where(GenerationJob.id==job_id))
 if not job:raise HTTPException(404,"Generation job not found")
 return job
@router.get("/workspaces/{workspace_id}/assets",response_model=list[AssetOut])
def assets(workspace_id:uuid.UUID,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):return list(db.scalars(select(MediaAsset).where(MediaAsset.workspace_id==workspace_id).order_by(MediaAsset.created_at.desc()).limit(48)))
