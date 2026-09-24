import base64

from openai import OpenAI

from app.providers.base import BaseMediaProvider, GeneratedImage, ImageRequest
from app.settings import settings

SIZES={"1:1":("1024x1024",1024,1024),"4:5":("1024x1536",1024,1536),"16:9":("1536x1024",1536,1024)}
class OpenAIImageProvider(BaseMediaProvider):
 name="openai"
 def __init__(self,api_key:str):
  self.client=OpenAI(api_key=api_key)
 def generate_image(self,r:ImageRequest)->list[GeneratedImage]:
  size,w,h=SIZES[r.aspect_ratio];response=self.client.images.generate(model=settings.openai_image_model,prompt=f"{r.prompt}\nVisual direction: {r.style_preset}.",size=size,n=r.output_count)
  return [GeneratedImage(base64.b64decode(x.b64_json),"image/png",w,h,{"revised_prompt":getattr(x,"revised_prompt",None)}) for x in response.data]
 def edit_image(self,*args):raise NotImplementedError
 def upscale_image(self,*args):raise NotImplementedError
 def generate_video(self,*args):raise NotImplementedError
