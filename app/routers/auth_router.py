from fastapi import APIRouter

from app.schemas.auth_schema import AdminLogin, TokenResponse
from app.schemas.owner_registration_schema import OwnerRegistrationCreate
from app.services.auth_service import auth_service
from app.services.owner_registration_service import owner_registration_service


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/login", response_model=TokenResponse)
def login_admin(login_data: AdminLogin) -> TokenResponse:
    return auth_service.login_admin(login_data)


@router.post("/shop-owner-registration", status_code=201)
def register_shop_owner(data: OwnerRegistrationCreate) -> dict:
    """Public endpoint: submit a request, without creating a login account."""
    return owner_registration_service.submit(data)
