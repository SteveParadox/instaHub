import uuid
from datetime import datetime
from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass
class Timestamped(Base):
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
class Workspace(Base, Timestamped):
    __tablename__="workspaces"; id: Mapped[uuid.UUID]=mapped_column(primary_key=True, default=uuid.uuid4); name: Mapped[str]=mapped_column(String(120)); owner_id: Mapped[uuid.UUID]=mapped_column()
class MediaAsset(Base, Timestamped):
    __tablename__="media_assets"; id: Mapped[uuid.UUID]=mapped_column(primary_key=True, default=uuid.uuid4); workspace_id: Mapped[uuid.UUID]=mapped_column(ForeignKey("workspaces.id")); media_type: Mapped[str]=mapped_column(String(20)); storage_key: Mapped[str]=mapped_column(String(512), unique=True); delivery_url: Mapped[str|None]=mapped_column(String(2048)); thumbnail_url: Mapped[str|None]=mapped_column(String(2048)); metadata_json: Mapped[dict]=mapped_column(JSON, default=dict)
class Post(Base, Timestamped):
    __tablename__="posts"; id: Mapped[uuid.UUID]=mapped_column(primary_key=True, default=uuid.uuid4); workspace_id: Mapped[uuid.UUID]=mapped_column(ForeignKey("workspaces.id")); media_asset_id: Mapped[uuid.UUID]=mapped_column(ForeignKey("media_assets.id")); caption: Mapped[str]=mapped_column(Text); platform: Mapped[str]=mapped_column(String(30), default="instagram"); status: Mapped[str]=mapped_column(String(30), default="draft")
class PublishAttempt(Base, Timestamped):
    __tablename__="publish_attempts"; __table_args__=(UniqueConstraint("idempotency_key"),); id: Mapped[uuid.UUID]=mapped_column(primary_key=True, default=uuid.uuid4); post_id: Mapped[uuid.UUID]=mapped_column(ForeignKey("posts.id")); idempotency_key: Mapped[str]=mapped_column(String(128)); status: Mapped[str]=mapped_column(String(30)); response_json: Mapped[dict]=mapped_column(JSON, default=dict); error_message: Mapped[str|None]=mapped_column(Text)
