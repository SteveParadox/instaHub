import uuid
from sqlalchemy import JSON,Boolean,ForeignKey,Integer,String,Text
from sqlalchemy.orm import Mapped,mapped_column
from app.models import Base,Timestamped
class VideoGenerationJob(Base,Timestamped):
 __tablename__="video_generation_jobs"
 id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4);workspace_id:Mapped[uuid.UUID]=mapped_column(index=True);provider_name:Mapped[str]=mapped_column(String(50));model_name:Mapped[str]=mapped_column(String(120));prompt:Mapped[str]=mapped_column(Text);settings_json:Mapped[dict]=mapped_column(JSON,default=dict);status:Mapped[str]=mapped_column(String(30),default="queued",index=True);progress_percent:Mapped[int]=mapped_column(Integer,default=0);external_job_id:Mapped[str|None]=mapped_column(String(255),nullable=True);error_message:Mapped[str|None]=mapped_column(Text,nullable=True);created_by:Mapped[str]=mapped_column(String(255));media_asset_id:Mapped[uuid.UUID|None]=mapped_column(ForeignKey("media_assets.id"),nullable=True)
class VideoProcessingMetadata(Base,Timestamped):
 __tablename__="video_processing_metadata"
 id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4);media_asset_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("media_assets.id"),unique=True);duration_seconds:Mapped[float|None]=mapped_column(nullable=True);fps:Mapped[int|None]=mapped_column(nullable=True);aspect_ratio:Mapped[str|None]=mapped_column(String(20),nullable=True);thumbnail_url:Mapped[str|None]=mapped_column(String(2048),nullable=True);preview_url:Mapped[str|None]=mapped_column(String(2048),nullable=True);processing_status:Mapped[str]=mapped_column(String(30),default="queued");transcode_status:Mapped[str]=mapped_column(String(30),default="pending")
