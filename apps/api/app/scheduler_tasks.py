import secrets
from datetime import UTC, datetime

from sqlalchemy import select

from app.database import SessionLocal
from app.models import SocialAccount
from app.publish_tasks import queue_publish
from app.publishing_models import Post, PublishAttempt
from app.tasks import celery


@celery.task(name="instahub.dispatch_due_posts")
def dispatch_due_posts():
    db = SessionLocal(); queued = []
    try:
        posts = list(db.scalars(select(Post).where(Post.status == "scheduled", Post.scheduled_at <= datetime.now(UTC)).with_for_update(skip_locked=True).limit(100)))
        for post in posts:
            account = db.scalar(select(SocialAccount).where(SocialAccount.workspace_id == post.workspace_id, SocialAccount.platform == post.platform, SocialAccount.is_active.is_(True)))
            if not account: post.status = "failed"; continue
            attempt = PublishAttempt(post_id=post.id, social_account_id=account.id, idempotency_key=secrets.token_urlsafe(32)); db.add(attempt); post.status = "queued"; db.flush(); queued.append((attempt, post, post.platform))
        db.commit()
        for attempt, post, platform in queued:
            try: queue_publish(attempt, platform)
            except Exception:
                attempt.status = "failed"; attempt.error_message = "Publishing queue is unavailable"; post.status = "failed"; db.commit()
    finally: db.close()
