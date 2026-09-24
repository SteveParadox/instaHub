import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import UserProfile, current_user, require_workspace_access
from app.brand_models import BrandProfile, Persona
from app.database import get_db
from app.models import MediaAsset

router = APIRouter(prefix="/v1", tags=["brand profiles"])


class BrandIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    tone: str = "Confident"
    visual_dna: dict = Field(default_factory=dict)
    prompt_defaults: dict = Field(default_factory=dict)
    reference_asset_ids: list[uuid.UUID] = Field(default_factory=list, max_length=12)


class PersonaIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    role: str = Field(default="Creator", max_length=120)
    appearance: dict = Field(default_factory=dict)
    voice_rules: str = Field(default="", max_length=4000)
    consistency_memory: str = Field(default="", max_length=4000)


class BrandOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    tone: str
    visual_dna: dict
    prompt_defaults: dict
    reference_asset_ids: list[uuid.UUID]


@router.post("/workspaces/{workspace_id}/brands", response_model=BrandOut)
def create(workspace_id: uuid.UUID, payload: BrandIn, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, workspace_id)
    refs = list(db.scalars(select(MediaAsset.id).where(MediaAsset.id.in_(payload.reference_asset_ids), MediaAsset.workspace_id == workspace_id))) if payload.reference_asset_ids else []
    if len(refs) != len(set(payload.reference_asset_ids)): raise HTTPException(422, "One or more reference assets are invalid")
    brand = BrandProfile(workspace_id=workspace_id, **payload.model_dump(mode="json")); db.add(brand); db.commit(); db.refresh(brand); return brand


@router.get("/workspaces/{workspace_id}/brands", response_model=list[BrandOut])
def list_brands(workspace_id: uuid.UUID, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    require_workspace_access(db, user, workspace_id)
    return list(db.scalars(select(BrandProfile).where(BrandProfile.workspace_id == workspace_id).order_by(BrandProfile.created_at.desc())))


@router.post("/brands/{brand_id}/personas")
def persona(brand_id: uuid.UUID, payload: PersonaIn, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    brand = db.get(BrandProfile, brand_id)
    if not brand: raise HTTPException(404, "Brand profile not found")
    require_workspace_access(db, user, brand.workspace_id)
    item = Persona(brand_profile_id=brand_id, **payload.model_dump()); db.add(item); db.commit(); return {"id": str(item.id)}


def creative_context(db: Session, workspace_id: uuid.UUID, brand_id: uuid.UUID | None) -> str:
    if not brand_id: return ""
    brand = db.scalar(select(BrandProfile).where(BrandProfile.id == brand_id, BrandProfile.workspace_id == workspace_id))
    if not brand: raise HTTPException(404, "Brand profile not found")
    personas = list(db.scalars(select(Persona).where(Persona.brand_profile_id == brand.id)))
    cast = "; ".join(f"{p.name} ({p.role}): {p.appearance}. {p.consistency_memory}" for p in personas)
    return f"Creative DNA — Brand: {brand.name}. Tone: {brand.tone}. Visual style: {brand.visual_dna}. Defaults: {brand.prompt_defaults}. Personas: {cast}. Preserve this identity consistently."
