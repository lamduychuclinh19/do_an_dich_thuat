from fastapi import FastAPI
from app.routers.auth_router import router as auth_router
from app.routers.poi_router import router as poi_router
from app.routers.translation_router import (
    router as translation_router
)
from fastapi.staticfiles import StaticFiles

from app.services.audio_service import AUDIO_DIRECTORY

app = FastAPI(
    title="Hệ thống thuyết minh đa ngôn ngữ",
    version="1.0.0"
)
app.mount(
    "/audio",
    StaticFiles(directory=AUDIO_DIRECTORY),
    name="audio",
)
app.include_router(poi_router)
app.include_router(translation_router)
app.include_router(auth_router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Backend đang hoạt động"
    }