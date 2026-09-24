import mimetypes
import uuid
from urllib.parse import quote

import boto3
from botocore.config import Config

from app.settings import settings


class ObjectStorage:
    def __init__(self):
        if not all((settings.s3_bucket, settings.s3_access_key_id, settings.s3_secret_access_key)):
            raise RuntimeError("S3/R2 credentials and bucket are required")
        if not settings.s3_public_base_url:
            raise RuntimeError("S3_PUBLIC_BASE_URL is required")
        self.client = boto3.client("s3", endpoint_url=settings.s3_endpoint_url or None, region_name=settings.s3_region, aws_access_key_id=settings.s3_access_key_id, aws_secret_access_key=settings.s3_secret_access_key, config=Config(signature_version="s3v4"))

    def get(self, key: str) -> bytes:
        return self.client.get_object(Bucket=settings.s3_bucket, Key=key)["Body"].read()

    def _put(self, workspace_id: str, folder: str, content: bytes, mime_type: str):
        extension = mimetypes.guess_extension(mime_type) or ".bin"
        if extension == ".jpe": extension = ".jpg"
        key = f"workspaces/{workspace_id}/{folder}/{uuid.uuid4()}{extension}"
        self.client.put_object(Bucket=settings.s3_bucket, Key=key, Body=content, ContentType=mime_type, CacheControl="public, max-age=31536000, immutable")
        return key, f"{settings.s3_public_base_url.rstrip('/')}/{quote(key, safe='/')}"

    def put_variant(self, workspace_id: str, content: bytes, mime_type: str):
        return self._put(workspace_id, "variants", content, mime_type)

    def put_image(self, workspace_id: str, content: bytes, mime_type: str):
        return self._put(workspace_id, "assets", content, mime_type)
