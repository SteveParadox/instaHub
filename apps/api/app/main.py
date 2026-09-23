from contextlib import asynccontextmanager
from fastapi import Depends,FastAPI,Header,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError,jwt
from pydantic import BaseModel
from app.database import engine
from app.models import Base
from app.settings import settings
@asynccontextmanager
async def lifespan(app:FastAPI):
 Base.metadata.create_all(bind=engine);yield
app=FastAPI(title="instaHub API",version="0.2.0",lifespan=lifespan);app.add_middleware(CORSMiddleware,allow_origins=[settings.web_origin],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
class UserProfile(BaseModel):id:str;email:str|None=None
def current_user(authorization:str|None=Header(default=None)):
 if not authorization or not authorization.startswith("Bearer "):raise HTTPException(401,"Authentication required")
 if not settings.supabase_jwt_secret:raise HTTPException(503,"Auth is not configured")
 try:
  p=jwt.decode(authorization.removeprefix("Bearer "),settings.supabase_jwt_secret,algorithms=["HS256"],audience="authenticated");return UserProfile(id=p["sub"],email=p.get("email"))
 except (JWTError,KeyError) as exc:raise HTTPException(401,"Invalid token") from exc
@app.get("/health")
def health():return {"status":"ok","service":"instahub-api"}
from app.routers.generations import router as generation_router
app.include_router(generation_router)
