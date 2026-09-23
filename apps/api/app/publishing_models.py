import uuid
from datetime import datetime
from sqlalchemy import JSON,DateTime,ForeignKey,String,Text,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from app.models import Base,Timestamped
class Post(Base,Timestamped):
 __tablename__="posts"
 id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4);workspace_id:Mapped[uuid.UUID]=mapped_column(index=True);media_asset_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("media_assets.id"));caption:Mapped[str]=mapped_column(Text);platform:Mapped[str]=mapped_column(String(30),default="instagram");status:Mapped[str]=mapped_column(String(30),default="draft");scheduled_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True,index=True);published_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
class PublishAttempt(Base,Timestamped):
 __tablename__="publish_attempts";__table_args__=(UniqueConstraint("idempotency_key"),)
 id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4);post_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("posts.id"),index=True);social_account_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("social_accounts.id"));idempotency_key:Mapped[str]=mapped_column(String(128));status:Mapped[str]=mapped_column(String(30),default="queued");external_post_id:Mapped[str|None]=mapped_column(String(255),nullable=True);response_json:Mapped[dict]=mapped_column(JSON,default=dict);error_message:Mapped[str|None]=mapped_column(Text,nullable=True)
