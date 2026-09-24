import uuid
from datetime import UTC, datetime

from celery import Celery

from app.connectors import provider_key
from app.database import SessionLocal
from app.models import GenerationJob, MediaAsset
from app.providers.base import ImageRequest
from app.providers.openai_images import OpenAIImageProvider
from app.settings import settings
from app.storage import ObjectStorage
from app.usage_models import UsageEvent

celery = Celery("instahub", broker=settings.redis_url, backend=settings.redis_url)
celery.conf.update(
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    imports=("app.tasks_edits", "app.publish_tasks", "app.scheduler_tasks"),
    beat_schedule={"dispatch-due-posts": {"task": "instahub.dispatch_due_posts", "schedule": 30.0}},
)


@celery.task(bind=True, name="instahub.generate_images", max_retries=2)
def generate_images(self, job_id: str):
    db = SessionLocal(); job = None
    try:
        job = db.get(GenerationJob, uuid.UUID(job_id))
        if not job or job.status == "completed": return
        job.status = "generating"; job.error_message = None; db.commit()
        if job.provider_name != "openai": raise RuntimeError(f"No runtime adapter for {job.provider_name}")
        values = job.settings_json
        images = OpenAIImageProvider(provider_key(db, job.workspace_id, job.provider_name)).generate_image(ImageRequest(job.prompt, values["style_preset"], values["aspect_ratio"], values["output_count"]))
        store = ObjectStorage()
        for image in images:
            key, url = store.put_image(str(job.workspace_id), image.content, image.mime_type)
            db.add(MediaAsset(workspace_id=job.workspace_id, generation_job_id=job.id, media_type="image", storage_key=key, delivery_url=url, width=image.width, height=image.height, aspect_ratio=values["aspect_ratio"], mime_type=image.mime_type, file_size=len(image.content), metadata_json=image.provider_metadata))
        db.add(UsageEvent(workspace_id=job.workspace_id, user_id=job.created_by, event_type="image_generation", provider_name=job.provider_name, credits_used=len(images), metadata_json={"model": job.model_name, "job_id": str(job.id)}))
        job.status = "completed"; job.completed_at = datetime.now(UTC); db.commit()
    except Exception as exc:
        db.rollback()
        if job:
            job.status = "retrying" if self.request.retries < self.max_retries else "failed"
            job.error_message = "The provider or storage service did not complete this generation"
            db.commit()
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=2 ** (self.request.retries + 1))
        raise
    finally:
        db.close()
