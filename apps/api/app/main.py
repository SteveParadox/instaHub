import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.settings import settings

logger = logging.getLogger("instahub.api")
app = FastAPI(title="instaHub API", version="0.10.1")
app.add_middleware(CORSMiddleware, allow_origins=[settings.web_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request error", extra={"request_id": request_id})
        return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred", "request_id": request_id})
    response.headers["x-request-id"] = request_id
    return response


@app.get("/health")
def health():
    return {"status": "ok", "service": "instahub-api"}


from app.routers.brands import router as brands_router
from app.routers.captions import router as caption_router
from app.routers.connectors import router as connector_router
from app.routers.edits import router as edit_router
from app.routers.generations import router as generation_router
from app.routers.instagram import router as instagram_router
from app.routers.instagram_refresh import router as instagram_refresh_router
from app.routers.pinterest import router as pinterest_router
from app.routers.providers import router as providers_router
from app.routers.publishing import router as publishing_router
from app.routers.scheduling import router as scheduling_router
from app.routers.videos import router as videos_router
from app.routers.workspaces import router as workspaces_router

for router in (workspaces_router, generation_router, connector_router, edit_router, caption_router, instagram_router, instagram_refresh_router, publishing_router, pinterest_router, scheduling_router, providers_router, brands_router, videos_router):
    app.include_router(router)
