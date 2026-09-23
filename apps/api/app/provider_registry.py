from dataclasses import dataclass
@dataclass(frozen=True)
class ProviderDefinition: name:str;models:list[str];capabilities:list[str];enabled:bool=True
REGISTRY={"openai":ProviderDefinition("openai",["gpt-image-1","gpt-4.1-mini"],["image_generation","caption_generation","hashtag_generation"]),"fal":ProviderDefinition("fal",[],["image_generation","video_generation"],False),"replicate":ProviderDefinition("replicate",[],["image_generation","upscaling"],False),"stability":ProviderDefinition("stability",[],["image_generation"],False)}
def providers():return list(REGISTRY.values())
def resolve(preferred:str|None,fallback:str="openai"):
 p=REGISTRY.get(preferred or fallback)
 return p if p and p.enabled else REGISTRY[fallback]
