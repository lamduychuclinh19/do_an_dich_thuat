from fastapi import FastAPI

app = FastAPI(
    title="Hệ thống thuyết minh đa ngôn ngữ",
    version="1.0.0"
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Backend đang hoạt động"
    }