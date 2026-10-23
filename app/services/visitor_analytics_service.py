"""Nghiệp vụ thống kê khách đang xem visitor guide và thiết bị của họ."""

from uuid import UUID

from app.repositaries.visitor_session_repository import (
    visitor_session_repository,
)


def _device_details(user_agent: str) -> tuple[str, str, str]:
    """Rút gọn User-Agent thành loại máy, hệ điều hành và trình duyệt."""
    value = user_agent.lower()

    if any(token in value for token in ("ipad", "tablet", "kindle")):
        device_type = "Máy tính bảng"
    elif any(token in value for token in ("mobile", "iphone", "ipod", "android")):
        device_type = "Điện thoại"
    else:
        device_type = "Máy tính"

    if "windows" in value:
        operating_system = "Windows"
    elif "iphone" in value or "ipad" in value or "ipod" in value:
        operating_system = "iOS/iPadOS"
    elif "android" in value:
        operating_system = "Android"
    elif "mac os" in value or "macintosh" in value:
        operating_system = "macOS"
    elif "cros" in value:
        operating_system = "ChromeOS"
    elif "linux" in value:
        operating_system = "Linux"
    else:
        operating_system = "Khác/không xác định"

    if "edg/" in value or "edga/" in value or "edgios/" in value:
        browser = "Microsoft Edge"
    elif "opr/" in value or "opera" in value:
        browser = "Opera"
    elif "firefox/" in value or "fxios/" in value:
        browser = "Firefox"
    elif "crios/" in value or "chrome/" in value:
        browser = "Google Chrome"
    elif "safari/" in value:
        browser = "Safari"
    else:
        browser = "Khác/không xác định"

    return device_type, operating_system, browser


class VisitorAnalyticsService:
    def record_heartbeat(
        self,
        guest_session_id: UUID,
        user_agent: str,
        language_code: str,
    ) -> None:
        device_type, operating_system, browser = _device_details(user_agent[:1000])
        visitor_session_repository.heartbeat(
            guest_session_id=guest_session_id,
            device_type=device_type,
            operating_system=operating_system,
            browser=browser,
            language_code=language_code,
        )

    def get_active_summary(self) -> dict:
        return visitor_session_repository.get_active_summary()


visitor_analytics_service = VisitorAnalyticsService()
