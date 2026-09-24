from dataclasses import dataclass

from fastapi import HTTPException


@dataclass(frozen=True)
class ProviderDefinition:
    name: str
    label: str
    models: tuple[str, ...]
    capabilities: tuple[str, ...]
    enabled: bool


REGISTRY = {
    "openai": ProviderDefinition("openai", "OpenAI / ChatGPT", ("gpt-image-1", "gpt-4.1-mini"), ("image_generation", "image_editing", "caption_generation", "hashtag_generation"), True),
    "fal": ProviderDefinition("fal", "fal.ai", (), ("image_generation", "video_generation"), False),
    "replicate": ProviderDefinition("replicate", "Replicate", (), ("image_generation", "upscaling", "video_generation"), False),
    "stability": ProviderDefinition("stability", "Stability AI", (), ("image_generation", "image_editing"), False),
}


def providers() -> list[ProviderDefinition]:
    return list(REGISTRY.values())


def resolve(name: str) -> ProviderDefinition:
    provider = REGISTRY.get(name)
    if provider is None:
        raise HTTPException(422, "Unknown AI provider")
    if not provider.enabled:
        raise HTTPException(409, f"{provider.label} is not enabled on this deployment")
    return provider
