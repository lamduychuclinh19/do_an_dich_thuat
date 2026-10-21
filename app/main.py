from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers.admin_management_router import (
    router as admin_management_router,
)
from app.routers.admin_poi_router import router as admin_poi_router
from app.routers.admin_translation_router import (
    router as admin_translation_router,
)
from app.routers.auth_router import router as auth_router
from app.routers.guide_router import router as guide_router
from app.routers.profile_router import router as profile_router
from app.routers.public_poi_router import router as public_poi_router
from app.routers.public_translation_router import (
    router as public_translation_router,
)
from app.services.audio_service import AUDIO_DIRECTORY


app = FastAPI(
    title="Hệ thống thuyết minh đa ngôn ngữ",
    version="2.0.0",
)

# Cho phép giao diện React admin gọi API trong môi trường phát triển.
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

# Các file audio đã tạo được truy cập qua đường dẫn /audio/...
app.mount(
    "/audio",
    StaticFiles(directory=AUDIO_DIRECTORY),
    name="audio",
)

# API công khai dành cho khách tham quan.
app.include_router(public_poi_router)
app.include_router(public_translation_router)
app.include_router(guide_router)

# API xác thực dùng chung cho các loại tài khoản.
app.include_router(auth_router)

# API quản trị nội dung dành cho SYSTEM_ADMIN và SHOP_OWNER.
app.include_router(admin_poi_router)
app.include_router(admin_translation_router)

# API hồ sơ cá nhân chỉ dành cho SHOP_OWNER.
app.include_router(profile_router)

# API quản lý tài khoản SHOP_OWNER, chỉ SYSTEM_ADMIN được phép dùng.
app.include_router(admin_management_router)


@app.get("/health")
def health_check():
    """Kiểm tra nhanh backend có đang hoạt động hay không."""
    return {
        "status": "ok",
        "message": "Backend đang hoạt động",
    }
