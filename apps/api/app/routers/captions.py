import uuid,json
from fastapi import APIRouter,Depends,HTTPException
from openai import OpenAI
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.connectors import provider_key
from app.database import get_db
from app.main import UserProfile,current_user
from app.models import CaptionDraft
from app.settings import settings
router=APIRouter(prefix="/v1",tags=["caption assistant"]);TONES={"Professional","Playful","Bold","Educational","Luxury"};CTAS={"Ask a question","Visit link in bio","Save this post","Shop now","No CTA"}
class Create(BaseModel):
 workspace_id:uuid.UUID;source_text:str=Field(min_length=3,max_length=4000);tone:str="Playful";cta:str="Ask a question";length:str="short";emojis:bool=True
class Out(BaseModel):
 id:uuid.UUID;caption:str;hashtags:list[str];settings_json:dict
 class Config:from_attributes=True
@router.post("/captions",response_model=Out)
def create(p:Create,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 if p.tone not in TONES or p.cta not in CTAS or p.length not in {"short","long"}:raise HTTPException(422,"Unsupported caption option")
 key=provider_key(db,p.workspace_id,"openai");instruction=f"Write an Instagram {p.length} caption in a {p.tone} tone. CTA: {p.cta}. Emojis: {'allowed' if p.emojis else 'do not use any'}. Return strict JSON with caption and hashtags where hashtags is an array of 8 to 15 strings, each beginning #."
 r=OpenAI(api_key=key).chat.completions.create(model=settings.openai_text_model,response_format={"type":"json_object"},messages=[{"role":"system","content":instruction},{"role":"user","content":p.source_text}])
 try:data=json.loads(r.choices[0].message.content or "{}");caption=data["caption"];hashtags=data["hashtags"]
 except (ValueError,KeyError,TypeError) as exc:raise HTTPException(502,"Caption provider returned invalid content") from exc
 draft=CaptionDraft(workspace_id=p.workspace_id,source_text=p.source_text,caption=caption,hashtags=hashtags,settings_json={"tone":p.tone,"cta":p.cta,"length":p.length,"emojis":p.emojis},created_by=user.id);db.add(draft);db.commit();db.refresh(draft);return draft
@router.get("/workspaces/{workspace_id}/captions",response_model=list[Out])
def history(workspace_id:uuid.UUID,user:UserProfile=Depends(current_user),db:Session=Depends(get_db)):
 return list(db.scalars(select(CaptionDraft).where(CaptionDraft.workspace_id==workspace_id).order_by(CaptionDraft.created_at.desc()).limit(50)))
