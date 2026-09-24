"""Phase 10 integration baseline.

Revision ID: 20260923_0001
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

from app import brand_models, publishing_models, usage_models, video_models  # noqa: F401
from app.models import Base

revision = "20260923_0001"
down_revision = None
branch_labels = None
depends_on = None


def _add_missing(table: str, columns: list[sa.Column]) -> None:
    inspector = inspect(op.get_bind())
    existing = {column["name"] for column in inspector.get_columns(table)}
    for column in columns:
        if column.name not in existing:
            op.add_column(table, column)


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())
    _add_missing("generation_jobs", [sa.Column("negative_prompt", sa.Text(), nullable=True), sa.Column("external_job_id", sa.String(255), nullable=True)])
    _add_missing("media_assets", [sa.Column("thumbnail_url", sa.String(2048), nullable=True), sa.Column("preview_url", sa.String(2048), nullable=True), sa.Column("duration_seconds", sa.Float(), nullable=True), sa.Column("fps", sa.Integer(), nullable=True), sa.Column("aspect_ratio", sa.String(20), nullable=True), sa.Column("processing_status", sa.String(30), nullable=False, server_default="ready"), sa.Column("transcode_status", sa.String(30), nullable=False, server_default="not_required")])
    _add_missing("asset_operations", [sa.Column("created_by", sa.String(255), nullable=False, server_default="system")])
    _add_missing("posts", [sa.Column("platform_settings", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")), sa.Column("created_by", sa.String(255), nullable=False, server_default="system")])
    _add_missing("publish_attempts", [sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0")])


def downgrade() -> None:
    # This baseline intentionally preserves application data on downgrade.
    pass
