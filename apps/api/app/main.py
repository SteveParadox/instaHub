from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from pydantic import BaseModel
from app.settings import settings

app = FastAPI(title="instaHub API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.web_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class UserProfile(BaseModel):
    id: str
    email: str | None = None

def current_user(authorization: str | None = None) -> UserProfile:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    if not settings.supabase_jwt_secret:
        raise HTTPException(status_code=503, detail="Auth is not configured")
    try:
        payload = jwt.decode(authorization.removeprefix("Bearer "), settings.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated")
        return UserProfile(id=payload["sub"], email=payload.get("email"))
    except (JWTError, KeyError) as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "instahub-api"}

@app.get("/v1/me", response_model=UserProfile)
def me(user: UserProfile = Depends(current_user)) -> UserProfile:
    return user
