from fastapi import HTTPException, status

from app.repositaries.translation_repository import (
    translation_repository,
)
from app.services.poi_service import poi_service
from app.services.translation_service import translation_service


# Những ngôn ngữ backend hiện hỗ trợ.
SUPPORTED_LANGUAGE_CODES = {
    "vi",
    "en",
    "fr",
    "zh",
    "ko",
}


class GuideService:
    def get_nearby_guide(
        self,
        latitude: float,
        longitude: float,
        language_code: str,
    ) -> dict | None:
        """
        Tìm một địa điểm đang hoạt động ở gần khách
        và trả nội dung thuyết minh đúng ngôn ngữ.

        Đây là API nearby cũ. Hiện tại API này vẫn yêu cầu
        POI phải có đúng ngôn ngữ khách chọn.
        """

        # Tìm POI nằm trong bán kính kích hoạt.
        nearby_poi = poi_service.find_nearby_poi(
            latitude,
            longitude,
        )

        # Khách chưa đứng trong phạm vi của địa điểm nào.
        if nearby_poi is None:
            return None

        # Tìm đúng bản dịch mà khách đã chọn.
        translation = translation_service.get_translation(
            nearby_poi["id"],
            language_code,
        )

        # Không trả bản dịch đã bị admin ẩn.
        if translation.get("is_active") is False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Translation not available",
            )

        # Ghép dữ liệu địa điểm và bản dịch thành guide.
        return {
            "poi_id": nearby_poi["id"],
            "poi_name": nearby_poi["name"],
            "address": nearby_poi["address"],
            "latitude": nearby_poi["latitude"],
            "longitude": nearby_poi["longitude"],
            "distance_meters":
                nearby_poi["distance_meters"],
            "language_code":
                translation["language_code"],
            "title": translation["title"],
            "narration_text":
                translation["narration_text"],
            "audio_url": translation["audio_url"],
        }

    def get_all_guides(
        self,
        language_code: str,
    ) -> list[dict]:
        """
        Lấy toàn bộ POI công khai cùng nội dung thuyết minh.

        Repository sẽ tự áp dụng thứ tự fallback:
        ngôn ngữ yêu cầu -> tiếng Anh -> tiếng Việt.

        Nếu không có POI phù hợp, hàm trả danh sách rỗng []
        thay vì báo lỗi 404.
        """

        # Chuẩn hóa dữ liệu, ví dụ " KO " thành "ko".
        normalized_language_code = (
            language_code.strip().lower()
        )

        # Không cho gửi mã ngôn ngữ ngoài hệ thống hỗ trợ.
        if (
            normalized_language_code
            not in SUPPORTED_LANGUAGE_CODES
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Unsupported language code. "
                    "Supported values: vi, en, fr, zh, ko"
                ),
            )

        # Gọi Repository để truy vấn POI và bản dịch từ SQL.
        guides = translation_repository.get_public_guides(
            normalized_language_code,
        )

        return guides


guide_service = GuideService()