import uuid
from sqlalchemy import JSON,ForeignKey,String
from sqlalchemy.orm import Mapped,mapped_column
from app.models import Base,Timestamped
class UsageEvent(Base,Timestamped):
 __tablename__="usage_events"
 id:Mapped[uuid.UUID]=mapped_column(primary_key=True,default=uuid.uuid4);workspace_id:Mapped[uuid.UUID]=mapped_column(index=True);user_id:Mapped[str]=mapped_column(String(255));event_type:Mapped[str]=mapped_column(String(80));provider_name:Mapped[str]=mapped_column(String(50));credits_used:Mapped[float]=mapped_column(default=0);cost_estimate:Mapped[float]=mapped_column(default=0);metadata_json:Mapped[dict]=mapped_column(JSON,default=dict)
