import uuid

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base, Timestamped


class BrandProfile(Base, Timestamped):
    __tablename__ = "brand_profiles"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    tone: Mapped[str] = mapped_column(String(120), default="Confident")
    visual_dna: Mapped[dict] = mapped_column(JSON, default=dict)
    prompt_defaults: Mapped[dict] = mapped_column(JSON, default=dict)
    reference_asset_ids: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Persona(Base, Timestamped):
    __tablename__ = "personas"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    brand_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brand_profiles.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(120))
    appearance: Mapped[dict] = mapped_column(JSON, default=dict)
    voice_rules: Mapped[str] = mapped_column(Text, default="")
    consistency_memory: Mapped[str] = mapped_column(Text, default="")
