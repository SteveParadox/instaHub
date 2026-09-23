import uuid
from datetime import datetime,timezone
from celery import Celery
from app.connectors import provider_key
from app.database import SessionLocal
from app.models import GenerationJob,MediaAsset
from app.providers.base import ImageRequest
from app.providers.openai_images import OpenAIImageProvider
from app.settings import settings
from app.storage import ObjectStorage
celery=Celery("instahub",broker=settings.redis_url,backend=settings.redis_url);celery.conf.update(task_track_started=True)
@celery.task(name="instahub.generate_images",autoretry_for=(Exception,),retry_backoff=True,retry_kwargs={"max_retries":2})
def generate_images(job_id:str):
 db=SessionLocal();job=None
 try:
  job=db.get(GenerationJob,uuid.UUID(job_id))
  if not job:return
  job.status="generating";db.commit();s=job.settings_json
  images=OpenAIImageProvider(provider_key(db,job.workspace_id,job.provider_name)).generate_image(ImageRequest(job.prompt,s["style_preset"],s["aspect_ratio"],s["output_count"]));store=ObjectStorage()
  for image in images:
   key,url=store.put_image(str(job.workspace_id),image.content,image.mime_type);db.add(MediaAsset(workspace_id=job.workspace_id,generation_job_id=job.id,storage_key=key,delivery_url=url,width=image.width,height=image.height,mime_type=image.mime_type,file_size=len(image.content),metadata_json=image.provider_metadata))
  job.status="completed";job.completed_at=datetime.now(timezone.utc);db.commit()
 except Exception as exc:
  if job:job.status="failed";job.error_message=str(exc)[:2000];db.commit()
  raise
 finally:db.close()
