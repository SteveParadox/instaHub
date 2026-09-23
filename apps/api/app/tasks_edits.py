import io,uuid,base64
from datetime import datetime,timezone
from celery import Celery
from PIL import Image
from openai import OpenAI
from app.connectors import provider_key
from app.database import SessionLocal
from app.models import AssetOperation,AssetVariant,MediaAsset
from app.settings import settings
from app.storage import ObjectStorage
from app.tasks import celery
def transform(image,operation,settings_json):
 if operation=="upscale":
  factor=settings_json.get("factor",2);return image.resize((image.width*factor,image.height*factor),Image.Resampling.LANCZOS)
 if operation=="crop":
  target=settings_json.get("aspect_ratio","4:5");w,h=map(int,target.split(":"));source=image.width/image.height;wanted=w/h
  if source>wanted: new_w=int(image.height*wanted);left=(image.width-new_w)//2;return image.crop((left,0,left+new_w,image.height))
  new_h=int(image.width/wanted);top=(image.height-new_h)//2;return image.crop((0,top,image.width,top+new_h))
 return image
@celery.task(name="instahub.edit_asset",autoretry_for=(Exception,),retry_backoff=True,retry_kwargs={"max_retries":2})
def edit_asset(operation_id):
 db=SessionLocal();op=None
 try:
  op=db.get(AssetOperation,uuid.UUID(operation_id));asset=db.get(MediaAsset,op.asset_id);op.status="processing";db.commit();store=ObjectStorage();source=store.get(asset.storage_key)
  if op.operation in {"upscale","crop"}:
   image=transform(Image.open(io.BytesIO(source)).convert("RGBA"),op.operation,op.settings_json);out=io.BytesIO();image.save(out,"PNG");content=out.getvalue();width,height=image.size;meta=op.settings_json
  else:
   prompt=op.settings_json.get("prompt") or ("Create a distinct creative variation of this image." if op.operation=="variation" else "Remove the background and preserve the main subject.")
   raw=io.BytesIO(source);raw.name="source.png";result=OpenAI(api_key=provider_key(db,asset.workspace_id,"openai")).images.edit(model=settings.openai_image_model,image=raw,prompt=prompt,size="auto");content=base64.b64decode(result.data[0].b64_json);width=asset.width;height=asset.height;meta={"prompt":prompt,"revised_prompt":getattr(result.data[0],"revised_prompt",None)}
  key,url=store.put_variant(str(asset.workspace_id),content,"image/png");variant=AssetVariant(parent_asset_id=asset.id,operation=op.operation,storage_key=key,delivery_url=url,width=width,height=height,metadata_json=meta);db.add(variant);db.flush();op.variant_id=variant.id;op.status="completed";db.commit()
 except Exception as exc:
  if op:op.status="failed";op.error_message=str(exc)[:2000];db.commit()
  raise
 finally:db.close()
