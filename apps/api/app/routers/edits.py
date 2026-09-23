import uuid
from fastapi import APIRouter,Depends,HTTPException,status
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.main import UserProfile,current_user
from app.models import AssetOperation,AssetVariant,MediaAsset
from app.tasks_edits import edit_asset
router=APIRouter(prefix="/v1",tags=["image editing"]);OPS={"variation","upscale","edit","crop","background_remove"}
class EditIn(BaseModel):operation:str;prompt:str|None=Field(default=None,max_length=4000);aspect_ratio:str|None=None;factor:int=Field(default=2,ge=2,le=4)
class VariantOut(BaseModel):
 id:uuid.UUID;operation:str;delivery_url:str;width:int|None;height:int|None;metadata_json:dict
 class Config:from_attributes=True
class OperationOut(BaseModel):
 id:uuid.UUID;status:str;error_message:str|None;variant_id:uuid.UUID|None
 class Config:from_attributes=True
@router.post("/assets/{asset_id}/operations",response_model=OperationOut,status_code=status.HTTP_202_ACCEPTED)
def create(asset_id:uuid.UUID,p:EditIn,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 if p.operation not in OPS:raise HTTPException(422,"Unsupported edit operation")
 if not db.get(MediaAsset,asset_id):raise HTTPException(404,"Asset not found")
 op=AssetOperation(asset_id=asset_id,operation=p.operation,settings_json={"prompt":p.prompt,"aspect_ratio":p.aspect_ratio,"factor":p.factor});db.add(op);db.commit();db.refresh(op);edit_asset.delay(str(op.id));return op
@router.get("/asset-operations/{operation_id}",response_model=OperationOut)
def operation(operation_id:uuid.UUID,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 op=db.get(AssetOperation,operation_id)
 if not op:raise HTTPException(404,"Operation not found")
 return op
@router.get("/assets/{asset_id}/variants",response_model=list[VariantOut])
def variants(asset_id:uuid.UUID,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 return list(db.scalars(select(AssetVariant).where(AssetVariant.parent_asset_id==asset_id).order_by(AssetVariant.created_at.desc())))
