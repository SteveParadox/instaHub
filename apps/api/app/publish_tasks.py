import time
import uuid
from datetime import UTC, datetime

import httpx

from app.connectors import decrypt
from app.database import SessionLocal
from app.models import MediaAsset, SocialAccount
from app.publishing_models import Post, PublishAttempt
from app.settings import settings
from app.tasks import celery


def _load(db, attempt_id: str):
    attempt = db.get(PublishAttempt, uuid.UUID(attempt_id))
    if not attempt: return None, None, None, None
    post = db.get(Post, attempt.post_id); asset = db.get(MediaAsset, post.media_asset_id); account = db.get(SocialAccount, attempt.social_account_id)
    return attempt, post, asset, account


def _mark_error(db, attempt, post, message: str, retrying: bool):
    attempt.status = "retrying" if retrying else "failed"; attempt.retry_count += 1; attempt.error_message = message[:500]
    post.status = "queued" if retrying else "failed"; db.commit()


@celery.task(bind=True, name="instahub.publish_instagram", max_retries=3)
def publish_instagram(self, attempt_id: str):
    db = SessionLocal(); attempt = post = None
    try:
        attempt, post, asset, account = _load(db, attempt_id)
        if not attempt or attempt.status == "published": return
        if not asset or not account or not asset.delivery_url.startswith("https://"): raise RuntimeError("Publishing prerequisites are unavailable")
        attempt.status = "publishing"; post.status = "publishing"; attempt.error_message = None; db.commit()
        token = decrypt(account.encrypted_access_token); response_state = dict(attempt.response_json)
        with httpx.Client(timeout=30) as client:
            container_id = response_state.get("container_id")
            if not container_id:
                field = "video_url" if asset.media_type == "video" else "image_url"
                body = {field: asset.delivery_url, "caption": post.caption, "access_token": token}
                if asset.media_type == "video": body["media_type"] = "REELS"
                response = client.post(f"https://graph.instagram.com/{settings.meta_graph_version}/{account.external_account_id}/media", data=body); response.raise_for_status(); container_id = response.json()["id"]
                attempt.response_json = {"container_id": container_id}; db.commit()
            for _ in range(10):
                check = client.get(f"https://graph.instagram.com/{settings.meta_graph_version}/{container_id}", params={"fields": "status_code", "access_token": token}); check.raise_for_status(); code = check.json().get("status_code")
                if code == "FINISHED": break
                if code in {"ERROR", "EXPIRED"}: raise RuntimeError("Instagram rejected media processing")
                time.sleep(2)
            else: raise RuntimeError("Instagram media is still processing")
            published = client.post(f"https://graph.instagram.com/{settings.meta_graph_version}/{account.external_account_id}/media_publish", data={"creation_id": container_id, "access_token": token}); published.raise_for_status(); data = published.json()
        attempt.status = "published"; attempt.external_post_id = data["id"]; attempt.response_json = {"container_id": container_id, "post_id": data["id"]}; post.status = "published"; post.published_at = datetime.now(UTC); db.commit()
    except Exception as exc:
        db.rollback(); retrying = self.request.retries < self.max_retries
        if attempt and post: _mark_error(db, attempt, post, "Instagram publishing failed; retry scheduled" if retrying else "Instagram publishing failed after retries", retrying)
        if retrying: raise self.retry(exc=exc, countdown=min(60, 2 ** (self.request.retries + 2)))
        raise
    finally: db.close()


@celery.task(bind=True, name="instahub.publish_pinterest", max_retries=3)
def publish_pinterest(self, attempt_id: str):
    db = SessionLocal(); attempt = post = None
    try:
        attempt, post, asset, account = _load(db, attempt_id)
        if not attempt or attempt.status == "published": return
        if not asset or not account or not asset.delivery_url.startswith("https://"): raise RuntimeError("Publishing prerequisites are unavailable")
        values = post.platform_settings
        if not values.get("board_id"): raise RuntimeError("A Pinterest board is required")
        attempt.status = "publishing"; post.status = "publishing"; db.commit()
        response = httpx.post("https://api.pinterest.com/v5/pins", headers={"Authorization": "Bearer " + decrypt(account.encrypted_access_token)}, json={"board_id": values["board_id"], "title": values.get("title", "")[:100], "description": post.caption[:800], "link": values.get("link"), "media_source": {"source_type": "image_url", "url": asset.delivery_url}}, timeout=30); response.raise_for_status(); data = response.json()
        attempt.status = "published"; attempt.external_post_id = data["id"]; attempt.response_json = {"pin_id": data["id"]}; post.status = "published"; post.published_at = datetime.now(UTC); db.commit()
    except Exception as exc:
        db.rollback(); retrying = self.request.retries < self.max_retries
        if attempt and post: _mark_error(db, attempt, post, "Pinterest publishing failed; retry scheduled" if retrying else "Pinterest publishing failed after retries", retrying)
        if retrying: raise self.retry(exc=exc, countdown=min(60, 2 ** (self.request.retries + 2)))
        raise
    finally: db.close()


def queue_publish(attempt: PublishAttempt, platform: str):
    task = {"instagram": publish_instagram, "pinterest": publish_pinterest}.get(platform)
    if not task: raise RuntimeError("Unsupported publishing platform")
    task.delay(str(attempt.id))
