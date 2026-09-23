import uuid
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.main import UserProfile,current_user
from app.models import AIProviderAccount
from app.provider_registry import providers,resolve
from app.usage_models import UsageEvent
router=APIRouter(prefix="/v1",tags=["AI providers"])
class ProviderOut(BaseModel):name:str;models:list[str];capabilities:list[str];enabled:bool;selected:bool=False
class DefaultIn(BaseModel):provider_name:str
@router.get("/providers",response_model=list[ProviderOut])
def registry():return [ProviderOut(name=p.name,models=p.models,capabilities=p.capabilities,enabled=p.enabled) for p in providers()]
@router.put("/workspaces/{workspace_id}/default-provider")
def select_default(workspace_id:uuid.UUID,p:DefaultIn,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 selected=resolve(p.provider_name)
 account=db.scalar(select(AIProviderAccount).where(AIProviderAccount.workspace_id==workspace_id,AIProviderAccount.provider_name==selected.name))
 if not account:raise HTTPException(409,"Connect this provider before selecting it")
 account.settings_json={**account.settings_json,"default":True};db.commit();return {"default_provider":selected.name,"fallback":"openai"}
@router.get("/workspaces/{workspace_id}/provider-usage")
def usage(workspace_id:uuid.UUID,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 return list(db.scalars(select(UsageEvent).where(UsageEvent.workspace_id==workspace_id).order_by(UsageEvent.created_at.desc()).limit(100)))
