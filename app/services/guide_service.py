from fastapi import HTTPException, status

from app.services.poi_service import poi_service
from app.services.translation_service import translation_service


class GuideService:
    def get_nearby_guide(
        self,
        latitude: float,
        longitude: float,
        language_code: str,
    ) -> dict | None:
        # 1. Tìm POI đang hoạt động trong phạm vi 1–2 mét
        nearby_poi = poi_service.find_nearby_poi(
            latitude,
            longitude,
        )

        # Khách chưa đứng gần địa điểm nào
        if nearby_poi is None:
            return None

        # 2. Lấy bản dịch theo ngôn ngữ khách đã chọn
        translation = translation_service.get_translation(
            nearby_poi["id"],
            language_code,
        )

        # Không trả bản dịch đã bị ẩn
        if translation.get("is_active") is False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Translation not available",
            )

        # 3. Ghép dữ liệu POI, bản dịch và audio
        return {
            "poi_id": nearby_poi["id"],
            "poi_name": nearby_poi["name"],
            "address": nearby_poi["address"],
            "latitude": nearby_poi["latitude"],
            "longitude": nearby_poi["longitude"],
            "distance_meters": nearby_poi["distance_meters"],
            "language_code": translation["language_code"],
            "title": translation["title"],
            "narration_text": translation["narration_text"],
            "audio_url": translation["audio_url"],
        }


guide_service = GuideService()