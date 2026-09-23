import uuid,boto3
from botocore.config import Config
from app.settings import settings
class ObjectStorage:
 def __init__(self):
  if not all([settings.s3_bucket,settings.s3_access_key_id,settings.s3_secret_access_key]): raise RuntimeError("S3/R2 credentials and bucket are required")
  self.client=boto3.client("s3",endpoint_url=settings.s3_endpoint_url or None,region_name=settings.s3_region,aws_access_key_id=settings.s3_access_key_id,aws_secret_access_key=settings.s3_secret_access_key,config=Config(signature_version="s3v4"))
 def put_image(self,workspace_id:str,content:bytes,mime_type:str)->tuple[str,str]:
  key=f"workspaces/{workspace_id}/generated/{uuid.uuid4()}.png";self.client.put_object(Bucket=settings.s3_bucket,Key=key,Body=content,ContentType=mime_type)
  if not settings.s3_public_base_url: raise RuntimeError("S3_PUBLIC_BASE_URL is required")
  return key,f"{settings.s3_public_base_url.rstrip('/')}/{key}"
