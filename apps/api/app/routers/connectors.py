import uuid
from fastapi import APIRouter,Depends,HTTPException,status
from openai import OpenAI
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.connectors import encrypt,provider_key
from app.database import get_db
from app.main import UserProfile,current_user
from app.models import AIProviderAccount
from app.settings import settings
router=APIRouter(prefix="/v1",tags=["AI connectors"])
class ProviderOut(BaseModel):
 provider_name:str;is_connected:bool;capabilities:list[str]
class ConnectOpenAI(BaseModel):api_key:str=Field(min_length=20,max_length=500)
class CaptionRequest(BaseModel):workspace_id:uuid.UUID;prompt:str=Field(min_length=3,max_length=4000);tone:str="engaging"
@router.get("/workspaces/{workspace_id}/ai-providers",response_model=list[ProviderOut])
def providers(workspace_id:uuid.UUID,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 active={x.provider_name for x in db.scalars(select(AIProviderAccount).where(AIProviderAccount.workspace_id==workspace_id,AIProviderAccount.is_active.is_(True)))}
 return [ProviderOut(provider_name="openai",is_connected="openai" in active or bool(settings.openai_api_key),capabilities=["image_generation","caption_generation","hashtag_generation"]),ProviderOut(provider_name="fal",is_connected=False,capabilities=["image_generation","video_generation"]),ProviderOut(provider_name="replicate",is_connected=False,capabilities=["image_generation","upscaling"])]
@router.put("/workspaces/{workspace_id}/ai-providers/openai",response_model=ProviderOut)
def connect_openai(workspace_id:uuid.UUID,p:ConnectOpenAI,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 try:OpenAI(api_key=p.api_key).models.list()
 except Exception as exc:raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,"OpenAI could not validate this API key") from exc
 account=db.scalar(select(AIProviderAccount).where(AIProviderAccount.workspace_id==workspace_id,AIProviderAccount.provider_name=="openai"))
 if account:account.encrypted_api_key=encrypt(p.api_key);account.is_active=True
 else:db.add(AIProviderAccount(workspace_id=workspace_id,provider_name="openai",encrypted_api_key=encrypt(p.api_key)))
 db.commit();return ProviderOut(provider_name="openai",is_connected=True,capabilities=["image_generation","caption_generation","hashtag_generation"])
@router.delete("/workspaces/{workspace_id}/ai-providers/openai",status_code=204)
def disconnect_openai(workspace_id:uuid.UUID,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 account=db.scalar(select(AIProviderAccount).where(AIProviderAccount.workspace_id==workspace_id,AIProviderAccount.provider_name=="openai"))
 if account:db.delete(account);db.commit()
@router.post("/captions")
def caption(p:CaptionRequest,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 try:key=provider_key(db,p.workspace_id,"openai")
 except RuntimeError as exc:raise HTTPException(409,str(exc)) from exc
 response=OpenAI(api_key=key).chat.completions.create(model=settings.openai_text_model,messages=[{"role":"system","content":"Create a concise Instagram caption and 8 relevant hashtags. Keep it brand-safe and do not use markdown."},{"role":"user","content":f"Tone: {p.tone}. Content: {p.prompt}"}])
 return {"caption":response.choices[0].message.content}
