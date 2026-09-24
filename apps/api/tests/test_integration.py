from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.auth import UserProfile, require_workspace_access
from app.main import app
from app.models import MediaAsset, SocialAccount
from app.routers.edits import EditIn
from app.routers.scheduling import ScheduleIn
from app.routers.scheduling import create as create_schedule
from app.routers.videos import Create as VideoIn
from app.routers.videos import create as create_video
from app.routers.workspaces import WorkspaceIn, create_workspace

USER_ONE = UserProfile(id="user-one", email="one@example.com")
USER_TWO = UserProfile(id="user-two", email="two@example.com")


def workspace(db):
    return create_workspace(WorkspaceIn(name="Creator Studio"), USER_ONE, db)


def add_asset(db, workspace_id):
    asset = MediaAsset(workspace_id=workspace_id, media_type="image", storage_key=f"assets/{workspace_id}.png", delivery_url="https://cdn.example.test/image.png", width=1024, height=1024, mime_type="image/png", file_size=100)
    db.add(asset); db.commit(); return asset


def test_workspace_creation_and_tenant_isolation(db):
    item = workspace(db)
    assert require_workspace_access(db, USER_ONE, item.id).role == "owner"
    with pytest.raises(HTTPException) as exc:
        require_workspace_access(db, USER_TWO, item.id)
    assert exc.value.status_code == 404


def test_pinterest_schedule_requires_board_and_can_be_created(db):
    item = workspace(db); asset = add_asset(db, item.id)
    db.add(SocialAccount(workspace_id=item.id, platform="pinterest", account_name="studio", external_account_id="p-1", encrypted_access_token="encrypted")); db.commit()
    base = {"workspace_id": item.id, "media_asset_id": asset.id, "caption": "Launch day", "platform": "pinterest", "scheduled_at": datetime.now(UTC) + timedelta(hours=1)}
    with pytest.raises(HTTPException) as exc:
        create_schedule(ScheduleIn(**base), USER_ONE, db)
    assert exc.value.status_code == 422
    post = create_schedule(ScheduleIn(**base, board_id="board-1", title="Launch"), USER_ONE, db)
    assert post.platform_settings["board_id"] == "board-1"


def test_video_placeholder_accepts_future_provider_job(db):
    item = workspace(db)
    job = create_video(VideoIn(workspace_id=item.id, prompt="A silk ribbon moving in studio light", provider_name="fal"), USER_ONE, db)
    assert job.status == "awaiting_provider"


def test_edit_validation_rejects_missing_prompt_and_crop_ratio():
    with pytest.raises(ValidationError): EditIn(operation="edit")
    with pytest.raises(ValidationError): EditIn(operation="crop")


def test_caption_route_is_not_registered_twice():
    schema = app.openapi()
    assert list(schema["paths"]["/v1/captions"]) == ["post"]
