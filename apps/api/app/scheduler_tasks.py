from datetime import datetime,timezone
from sqlalchemy import select
from app.database import SessionLocal
from app.models import SocialAccount
from app.publishing_models import Post,PublishAttempt
from app.publish_tasks import publish_instagram
from app.tasks import celery
import secrets
@celery.task(name="instahub.dispatch_due_posts")
def dispatch_due_posts():
 db=SessionLocal()
 try:
  posts=list(db.scalars(select(Post).where(Post.status=="scheduled",Post.scheduled_at<=datetime.now(timezone.utc))))
  for post in posts:
   account=db.scalar(select(SocialAccount).where(SocialAccount.workspace_id==post.workspace_id,SocialAccount.platform==post.platform,SocialAccount.is_active.is_(True)))
   if not account:post.status="failed";continue
   attempt=PublishAttempt(post_id=post.id,social_account_id=account.id,idempotency_key=secrets.token_urlsafe(32));db.add(attempt);post.status="queued";db.flush()
   if post.platform=="instagram":publish_instagram.delay(str(attempt.id))
  db.commit()
 finally:db.close()
celery.conf.beat_schedule={"dispatch-due-posts":{"task":"instahub.dispatch_due_posts","schedule":60.0}}
