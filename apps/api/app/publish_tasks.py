import uuid
from datetime import datetime,timezone
import httpx
from app.connectors import decrypt
from app.database import SessionLocal
from app.models import MediaAsset,SocialAccount
from app.publishing_models import Post,PublishAttempt
from app.settings import settings
from app.tasks import celery
@celery.task(name="instahub.publish_instagram",autoretry_for=(httpx.HTTPError,),retry_backoff=True,retry_kwargs={"max_retries":3})
def publish_instagram(attempt_id:str):
 db=SessionLocal();attempt=None
 try:
  attempt=db.get(PublishAttempt,uuid.UUID(attempt_id));post=db.get(Post,attempt.post_id);asset=db.get(MediaAsset,post.media_asset_id);account=db.get(SocialAccount,attempt.social_account_id)
  if attempt.status=="published":return
  if not asset.delivery_url.startswith("https://"):raise RuntimeError("Asset must have a public HTTPS delivery URL")
  attempt.status="publishing";post.status="publishing";db.commit();token=decrypt(account.encrypted_access_token)
  with httpx.Client(timeout=30) as client:
   container=client.post(f"https://graph.instagram.com/{settings.meta_graph_version}/{account.external_account_id}/media",data={"image_url":asset.delivery_url,"caption":post.caption,"access_token":token});container.raise_for_status();container_id=container.json()["id"]
   published=client.post(f"https://graph.instagram.com/{settings.meta_graph_version}/{account.external_account_id}/media_publish",data={"creation_id":container_id,"access_token":token});published.raise_for_status();data=published.json()
  attempt.status="published";attempt.external_post_id=data["id"];attempt.response_json={"container_id":container_id,**data};post.status="published";post.published_at=datetime.now(timezone.utc);db.commit()
 except Exception as exc:
  if attempt:attempt.status="failed";attempt.error_message=str(exc)[:2000];post.status="failed";db.commit()
  raise
 finally:db.close()
