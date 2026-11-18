from fastapi import FastAPI
from app.routers.auth_router import router as auth_router
from fastapi.staticfiles import StaticFiles
from app.routers.public_translation_router import (
    router as public_translation_router,
)
from app.routers.admin_translation_router import (
    router as admin_translation_router,
)
from app.services.audio_service import AUDIO_DIRECTORY
from app.routers.guide_router import router as guide_router
from app.routers.public_poi_router import router as public_poi_router
from app.routers.admin_poi_router import router as admin_poi_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Hệ thống thuyết minh đa ngôn ngữ",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount(
    "/audio",
    StaticFiles(directory=AUDIO_DIRECTORY),
    name="audio",
)
app.include_router(public_poi_router)
app.include_router(public_translation_router)
app.include_router(admin_poi_router)
app.include_router(admin_translation_router)
app.include_router(auth_router)
app.include_router(guide_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Backend đang hoạt động"
    }