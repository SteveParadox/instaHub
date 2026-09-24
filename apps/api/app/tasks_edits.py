import base64
import io
import uuid

from openai import OpenAI
from PIL import Image

from app.connectors import provider_key
from app.database import SessionLocal
from app.models import AssetOperation, AssetVariant, MediaAsset
from app.settings import settings
from app.storage import ObjectStorage
from app.tasks import celery
from app.usage_models import UsageEvent


def transform(image: Image.Image, operation: str, values: dict) -> Image.Image:
    if operation == "upscale":
        factor = values.get("factor", 2)
        return image.resize((image.width * factor, image.height * factor), Image.Resampling.LANCZOS)
    if operation == "crop":
        width_ratio, height_ratio = map(int, values.get("aspect_ratio", "4:5").split(":"))
        wanted = width_ratio / height_ratio
        if image.width / image.height > wanted:
            new_width = int(image.height * wanted); left = (image.width - new_width) // 2
            return image.crop((left, 0, left + new_width, image.height))
        new_height = int(image.width / wanted); top = (image.height - new_height) // 2
        return image.crop((0, top, image.width, top + new_height))
    return image


@celery.task(bind=True, name="instahub.edit_asset", max_retries=2)
def edit_asset(self, operation_id: str):
    db = SessionLocal(); operation = None
    try:
        operation = db.get(AssetOperation, uuid.UUID(operation_id))
        if not operation or operation.status == "completed": return
        asset = db.get(MediaAsset, operation.asset_id)
        if not asset: raise RuntimeError("Source asset no longer exists")
        operation.status = "processing"; operation.error_message = None; db.commit()
        store = ObjectStorage(); source = store.get(asset.storage_key)
        if operation.operation in {"upscale", "crop"}:
            image = transform(Image.open(io.BytesIO(source)).convert("RGBA"), operation.operation, operation.settings_json)
            output = io.BytesIO(); image.save(output, "PNG"); content = output.getvalue(); width, height = image.size; metadata = operation.settings_json
        else:
            prompts = {"variation": "Create a distinct creative variation while preserving the subject and brand identity.", "background_remove": "Remove the background. Return the main subject isolated on a transparent background."}
            prompt = operation.settings_json.get("prompt") or prompts[operation.operation]
            raw = io.BytesIO(source); raw.name = "source.png"
            result = OpenAI(api_key=provider_key(db, asset.workspace_id, "openai")).images.edit(model=settings.openai_image_model, image=raw, prompt=prompt, size="auto")
            content = base64.b64decode(result.data[0].b64_json); width = asset.width; height = asset.height
            metadata = {"prompt": prompt, "revised_prompt": getattr(result.data[0], "revised_prompt", None)}
        key, url = store.put_variant(str(asset.workspace_id), content, "image/png")
        variant = AssetVariant(parent_asset_id=asset.id, operation=operation.operation, storage_key=key, delivery_url=url, width=width, height=height, metadata_json=metadata)
        db.add(variant); db.flush(); operation.variant_id = variant.id; operation.status = "completed"
        db.add(UsageEvent(workspace_id=asset.workspace_id, user_id=operation.created_by, event_type=f"image_{operation.operation}", provider_name="openai" if operation.operation not in {"upscale", "crop"} else "local", credits_used=1, metadata_json={"operation_id": str(operation.id)})); db.commit()
    except Exception as exc:
        db.rollback()
        if operation:
            operation.status = "retrying" if self.request.retries < self.max_retries else "failed"
            operation.error_message = "The edit could not be completed"
            db.commit()
        if self.request.retries < self.max_retries: raise self.retry(exc=exc, countdown=2 ** (self.request.retries + 1))
        raise
    finally:
        db.close()
