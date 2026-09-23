from contextlib import asynccontextmanager
from fastapi import FastAPI,Header,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError,jwt
from pydantic import BaseModel
from app.database import engine
from app.models import Base
from app.settings import settings
@asynccontextmanager
async def lifespan(app:FastAPI):Base.metadata.create_all(bind=engine);yield
app=FastAPI(title="instaHub API",version="0.10.0",lifespan=lifespan);app.add_middleware(CORSMiddleware,allow_origins=[settings.web_origin],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
class UserProfile(BaseModel):id:str;email:str|None=None
def current_user(authorization:str|None=Header(default=None)):
 if not authorization or not authorization.startswith("Bearer "):raise HTTPException(401,"Authentication required")
 if not settings.supabase_jwt_secret:raise HTTPException(503,"Auth is not configured")
 try:p=jwt.decode(authorization.removeprefix("Bearer "),settings.supabase_jwt_secret,algorithms=["HS256"],audience="authenticated");return UserProfile(id=p["sub"],email=p.get("email"))
 except (JWTError,KeyError) as exc:raise HTTPException(401,"Invalid token") from exc
@app.get("/health")
def health():return {"status":"ok","service":"instahub-api"}
from app.routers.generations import router as generation_router
from app.routers.connectors import router as connector_router
from app.routers.edits import router as edit_router
from app.routers.captions import router as caption_router
from app.routers.instagram import router as instagram_router
from app.routers.instagram_refresh import router as instagram_refresh_router
from app.routers.publishing import router as publishing_router
from app.routers.pinterest import router as pinterest_router
from app.routers.scheduling import router as scheduling_router
from app.routers.providers import router as providers_router
from app.routers.brands import router as brands_router
from app.routers.videos import router as videos_router
app.include_router(generation_router);app.include_router(connector_router);app.include_router(edit_router);app.include_router(caption_router);app.include_router(instagram_router);app.include_router(instagram_refresh_router);app.include_router(publishing_router);app.include_router(pinterest_router);app.include_router(scheduling_router);app.include_router(providers_router);app.include_router(brands_router);app.include_router(videos_router)
