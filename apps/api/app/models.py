import uuid
from datetime import datetime,timezone
from sqlalchemy import JSON,DateTime,ForeignKey,String,Text
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship
def utcnow(): return datetime.now(timezone.utc)
class Base(DeclarativeBase): pass
class Timestamped:
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
 updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow,onupdate=utcnow)
class GenerationJob(Base,Timestamped):
 __tablename__="generation_jobs"
 id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4);workspace_id:Mapped[uuid.UUID]=mapped_column(index=True);provider_name:Mapped[str]=mapped_column(String(50),default="openai");model_name:Mapped[str]=mapped_column(String(100));media_type:Mapped[str]=mapped_column(String(20),default="image");prompt:Mapped[str]=mapped_column(Text);settings_json:Mapped[dict]=mapped_column(JSON,default=dict);status:Mapped[str]=mapped_column(String(30),default="queued",index=True);error_message:Mapped[str|None]=mapped_column(Text,nullable=True);created_by:Mapped[str]=mapped_column(String(255));completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True);assets:Mapped[list["MediaAsset"]]=relationship(back_populates="generation_job",cascade="all,delete-orphan")
class MediaAsset(Base,Timestamped):
 __tablename__="media_assets"
 id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4);workspace_id:Mapped[uuid.UUID]=mapped_column(index=True);generation_job_id:Mapped[uuid.UUID|None]=mapped_column(ForeignKey("generation_jobs.id"),nullable=True,index=True);media_type:Mapped[str]=mapped_column(String(20),default="image");storage_key:Mapped[str]=mapped_column(String(512),unique=True);delivery_url:Mapped[str]=mapped_column(String(2048));width:Mapped[int|None]=mapped_column(nullable=True);height:Mapped[int|None]=mapped_column(nullable=True);mime_type:Mapped[str]=mapped_column(String(100),default="image/png");file_size:Mapped[int]=mapped_column();metadata_json:Mapped[dict]=mapped_column(JSON,default=dict);generation_job:Mapped[GenerationJob|None]=relationship(back_populates="assets")
