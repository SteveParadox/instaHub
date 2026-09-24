import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class User(Base, Timestamped):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(String(160), nullable=True)


class Workspace(Base, Timestamped):
    __tablename__ = "workspaces"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    default_provider: Mapped[str] = mapped_column(String(50), default="openai")


class WorkspaceMember(Base, Timestamped):
    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(30), default="member")


class AIProviderAccount(Base, Timestamped):
    __tablename__ = "ai_provider_accounts"
    __table_args__ = (UniqueConstraint("workspace_id", "provider_name"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    provider_name: Mapped[str] = mapped_column(String(50))
    encrypted_api_key: Mapped[str] = mapped_column(Text)
    settings_json: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SocialAccount(Base, Timestamped):
    __tablename__ = "social_accounts"
    __table_args__ = (UniqueConstraint("workspace_id", "platform", "external_account_id"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(30), default="instagram")
    account_name: Mapped[str] = mapped_column(String(255))
    external_account_id: Mapped[str] = mapped_column(String(255))
    encrypted_access_token: Mapped[str] = mapped_column(Text)
    encrypted_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class GenerationJob(Base, Timestamped):
    __tablename__ = "generation_jobs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    provider_name: Mapped[str] = mapped_column(String(50), default="openai")
    model_name: Mapped[str] = mapped_column(String(100))
    media_type: Mapped[str] = mapped_column(String(20), default="image")
    prompt: Mapped[str] = mapped_column(Text)
    negative_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    external_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(255))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assets: Mapped[list["MediaAsset"]] = relationship(back_populates="generation_job", cascade="all, delete-orphan")


class MediaAsset(Base, Timestamped):
    __tablename__ = "media_assets"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    generation_job_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("generation_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    media_type: Mapped[str] = mapped_column(String(20), default="image")
    storage_key: Mapped[str] = mapped_column(String(512), unique=True)
    delivery_url: Mapped[str] = mapped_column(String(2048))
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    preview_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    width: Mapped[int | None] = mapped_column(nullable=True)
    height: Mapped[int | None] = mapped_column(nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    fps: Mapped[int | None] = mapped_column(nullable=True)
    aspect_ratio: Mapped[str | None] = mapped_column(String(20), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(30), default="ready")
    transcode_status: Mapped[str] = mapped_column(String(30), default="not_required")
    mime_type: Mapped[str] = mapped_column(String(100), default="image/png")
    file_size: Mapped[int] = mapped_column()
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    generation_job: Mapped[GenerationJob | None] = relationship(back_populates="assets")
    variants: Mapped[list["AssetVariant"]] = relationship(back_populates="parent_asset", cascade="all, delete-orphan")


class AssetVariant(Base, Timestamped):
    __tablename__ = "asset_variants"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    parent_asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media_assets.id", ondelete="CASCADE"), index=True)
    operation: Mapped[str] = mapped_column(String(40))
    storage_key: Mapped[str] = mapped_column(String(512), unique=True)
    delivery_url: Mapped[str] = mapped_column(String(2048))
    width: Mapped[int | None] = mapped_column(nullable=True)
    height: Mapped[int | None] = mapped_column(nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    parent_asset: Mapped[MediaAsset] = relationship(back_populates="variants")


class AssetOperation(Base, Timestamped):
    __tablename__ = "asset_operations"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media_assets.id", ondelete="CASCADE"), index=True)
    operation: Mapped[str] = mapped_column(String(40))
    created_by: Mapped[str] = mapped_column(String(255))
    settings_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("asset_variants.id", ondelete="SET NULL"), nullable=True)


class CaptionDraft(Base, Timestamped):
    __tablename__ = "caption_drafts"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    source_text: Mapped[str] = mapped_column(Text)
    caption: Mapped[str] = mapped_column(Text)
    hashtags: Mapped[list] = mapped_column(JSON, default=list)
    settings_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255))
