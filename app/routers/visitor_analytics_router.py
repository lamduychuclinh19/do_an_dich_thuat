"""API heartbeat công khai và thống kê dành cho SYSTEM_ADMIN."""

from fastapi import APIRouter, Depends, Request

from app.dependencies.auth_dependency import require_system_admin
from app.schemas.visitor_analytics_schema import (
    VisitorAnalyticsResponse,
    VisitorHeartbeatRequest,
)
from app.services.visitor_analytics_service import visitor_analytics_service


router = APIRouter(tags=["Visitor analytics"])


@router.post(
    "/api/public/visitor-sessions/heartbeat",
)
def record_visitor_heartbeat(
    data: VisitorHeartbeatRequest,
    request: Request,
) -> dict[str, bool]:
    """Ghi nhận visitor đang mở trang hướng dẫn sau khi đã thanh toán."""
    visitor_analytics_service.record_heartbeat(
        guest_session_id=data.guest_session_id,
        user_agent=request.headers.get("user-agent", ""),
        language_code=data.language_code,
    )
    return {"ok": True}


@router.get(
    "/api/admin/visitor-analytics/active",
    response_model=VisitorAnalyticsResponse,
)
def get_active_visitors(
    _current_admin: dict = Depends(require_system_admin),
) -> dict:
    """Trả số visitor còn heartbeat và thống kê loại thiết bị."""
    return visitor_analytics_service.get_active_summary()
