from dataclasses import dataclass

from fastapi import Header, HTTPException
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, Workspace, WorkspaceMember
from app.settings import settings


@dataclass(frozen=True)
class UserProfile:
    id: str
    email: str | None = None


def current_user(authorization: str | None = Header(default=None)) -> UserProfile:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    if not settings.supabase_jwt_secret:
        raise HTTPException(503, "Auth is not configured")
    try:
        payload = jwt.decode(authorization.removeprefix("Bearer "), settings.supabase_jwt_secret, algorithms=["HS256"], audience=settings.supabase_jwt_audience, issuer=settings.supabase_jwt_issuer or None)
        return UserProfile(id=payload["sub"], email=payload.get("email"))
    except (JWTError, KeyError) as exc:
        raise HTTPException(401, "Invalid token") from exc


def sync_user(db: Session, user: UserProfile) -> User:
    record = db.get(User, user.id)
    if record is None:
        record = User(id=user.id, email=user.email)
        db.add(record)
        db.flush()
    elif user.email and record.email != user.email:
        record.email = user.email
        db.flush()
    return record


def require_workspace_access(db: Session, user: UserProfile, workspace_id, *, roles: set[str] | None = None) -> WorkspaceMember:
    sync_user(db, user)
    membership = db.scalar(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user.id))
    if membership is None:
        raise HTTPException(404, "Workspace not found")
    if roles and membership.role not in roles:
        raise HTTPException(403, "You do not have permission for this workspace action")
    return membership


def require_workspace_owner(db: Session, user: UserProfile, workspace_id) -> Workspace:
    require_workspace_access(db, user, workspace_id, roles={"owner"})
    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(404, "Workspace not found")
    return workspace
