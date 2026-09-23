import uuid
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.brand_models import BrandProfile,Persona
from app.database import get_db
from app.main import UserProfile,current_user
router=APIRouter(prefix="/v1",tags=["brand profiles"])
class BrandIn(BaseModel):name:str=Field(min_length=2,max_length=120);tone:str="Confident";visual_dna:dict={};prompt_defaults:dict={};reference_asset_ids:list[str]=[]
class PersonaIn(BaseModel):name:str;role:str="Creator";appearance:dict={};voice_rules:str="";consistency_memory:str=""
class BrandOut(BaseModel):
 id:uuid.UUID;name:str;tone:str;visual_dna:dict;prompt_defaults:dict;reference_asset_ids:list[str]
 class Config:from_attributes=True
@router.post("/workspaces/{workspace_id}/brands",response_model=BrandOut)
def create(workspace_id:uuid.UUID,p:BrandIn,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 b=BrandProfile(workspace_id=workspace_id,**p.model_dump());db.add(b);db.commit();db.refresh(b);return b
@router.get("/workspaces/{workspace_id}/brands",response_model=list[BrandOut])
def list_brands(workspace_id:uuid.UUID,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):return list(db.scalars(select(BrandProfile).where(BrandProfile.workspace_id==workspace_id).order_by(BrandProfile.created_at.desc())))
@router.post("/brands/{brand_id}/personas")
def persona(brand_id:uuid.UUID,p:PersonaIn,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 if not db.get(BrandProfile,brand_id):raise HTTPException(404,"Brand profile not found")
 x=Persona(brand_profile_id=brand_id,**p.model_dump());db.add(x);db.commit();return {"id":str(x.id)}
def creative_context(db:Session,brand_id:uuid.UUID|None)->str:
 if not brand_id:return ""
 b=db.get(BrandProfile,brand_id)
 if not b:raise HTTPException(404,"Brand profile not found")
 dna=", ".join(f"{k}: {v}" for k,v in b.visual_dna.items());rules=", ".join(f"{k}: {v}" for k,v in b.prompt_defaults.items())
 personas=list(db.scalars(select(Persona).where(Persona.brand_profile_id==b.id)))
 cast="; ".join(f"{p.name} ({p.role}): {p.appearance}. {p.consistency_memory}" for p in personas)
 return f"Creative DNA — Brand: {b.name}. Tone: {b.tone}. Visual style: {dna}. Defaults: {rules}. Personas: {cast}. Preserve this identity consistently across every output."
