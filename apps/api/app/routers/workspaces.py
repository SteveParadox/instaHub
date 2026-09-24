import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import UserProfile, current_user, sync_user
from app.database import get_db
from app.models import Workspace, WorkspaceMember

router = APIRouter(prefix="/v1", tags=["users and workspaces"])


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str | None
    name: str | None


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=160)


class WorkspaceIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class WorkspaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    owner_id: str
    default_provider: str
    role: str | None = None


@router.get("/me", response_model=ProfileOut)
def me(user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    record = sync_user(db, user); db.commit(); db.refresh(record); return record


@router.patch("/me", response_model=ProfileOut)
def update_me(payload: ProfileUpdate, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    record = sync_user(db, user); record.name = payload.name; db.commit(); db.refresh(record); return record


@router.get("/workspaces", response_model=list[WorkspaceOut])
def list_workspaces(user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    sync_user(db, user)
    rows = db.execute(select(Workspace, WorkspaceMember.role).join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id).where(WorkspaceMember.user_id == user.id).order_by(Workspace.created_at)).all()
    db.commit()
    return [WorkspaceOut(id=w.id, name=w.name, owner_id=w.owner_id, default_provider=w.default_provider, role=role) for w, role in rows]


@router.post("/workspaces", response_model=WorkspaceOut, status_code=status.HTTP_201_CREATED)
def create_workspace(payload: WorkspaceIn, user: UserProfile = Depends(current_user), db: Session = Depends(get_db)):
    sync_user(db, user)
    workspace = Workspace(name=payload.name, owner_id=user.id); db.add(workspace); db.flush()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner")); db.commit(); db.refresh(workspace)
    return WorkspaceOut(id=workspace.id, name=workspace.name, owner_id=workspace.owner_id, default_provider=workspace.default_provider, role="owner")
