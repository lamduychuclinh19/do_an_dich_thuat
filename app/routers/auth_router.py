from fastapi import APIRouter

from app.schemas.auth_schema import AdminLogin, TokenResponse
from app.services.auth_service import auth_service


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/login", response_model=TokenResponse)
def login_admin(login_data: AdminLogin) -> TokenResponse:
    return auth_service.login_admin(login_data)