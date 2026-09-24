from app.settings import settings
from app.storage import ObjectStorage


class FakeS3:
    def __init__(self): self.calls = []
    def put_object(self, **kwargs): self.calls.append(kwargs)


def test_generated_asset_and_variant_use_distinct_prefixes(monkeypatch):
    monkeypatch.setattr(settings, "s3_bucket", "bucket")
    monkeypatch.setattr(settings, "s3_public_base_url", "https://cdn.example.test")
    storage = object.__new__(ObjectStorage); storage.client = FakeS3()
    asset_key, _ = storage.put_image("workspace", b"png", "image/png")
    variant_key, _ = storage.put_variant("workspace", b"png", "image/png")
    assert "/assets/" in asset_key
    assert "/variants/" in variant_key
    assert asset_key.endswith(".png") and variant_key.endswith(".png")
