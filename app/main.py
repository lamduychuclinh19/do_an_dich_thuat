from fastapi import FastAPI

from app.routers.poi_router import router as poi_router


app = FastAPI(
    title="Hệ thống thuyết minh đa ngôn ngữ",
    version="1.0.0"
)

app.include_router(poi_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Backend đang hoạt động"
    }