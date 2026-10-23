"""Các endpoint admin dùng để xem và xét duyệt phiếu đăng ký chủ quán."""

from fastapi import APIRouter, Depends

from app.dependencies.auth_dependency import require_system_admin
from app.schemas.owner_registration_schema import OwnerRegistrationDecision
from app.services.owner_registration_service import owner_registration_service


router = APIRouter(prefix="/api/admin/owner-registrations", tags=["SYSTEM ADMIN - Owner registrations"])


@router.get("")
def list_registrations(admin: dict = Depends(require_system_admin)):
    """Trả danh sách phiếu đăng ký cho admin đã xác thực."""
    return owner_registration_service.list_for_admin(admin)


@router.get("/pending-count")
def get_pending_count(admin: dict = Depends(require_system_admin)):
    """Trả số phiếu đăng ký đang chờ để hiển thị trên giao diện."""
    return owner_registration_service.pending_count(admin)


@router.get("/{registration_id}")
def get_registration(registration_id: int, admin: dict = Depends(require_system_admin)):
    """Trả chi tiết một phiếu đăng ký theo mã phiếu."""
    return owner_registration_service.get_for_admin(registration_id, admin)


@router.post("/{registration_id}/decision")
def decide_registration(
    registration_id: int,
    decision: OwnerRegistrationDecision,
    admin: dict = Depends(require_system_admin),
):
    """Nhận quyết định đồng ý hoặc từ chối một phiếu đăng ký."""
    return owner_registration_service.decide(
        registration_id, decision.status, decision.admin_note, admin
    )


@router.post("/{registration_id}/resend-email")
def resend_decision_email(registration_id: int, admin: dict = Depends(require_system_admin)):
    """Gửi lại email kết quả cho một phiếu đã được xét duyệt."""
    return owner_registration_service.resend_decision_email(registration_id, admin)
