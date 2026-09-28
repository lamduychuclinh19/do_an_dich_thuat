from fastapi import APIRouter, Query

from app.schemas.guide_schema import (
    GuideItemResponse,
    LanguageCode,
    NearbyGuideResponse,
)
from app.services.guide_service import guide_service


# Đây là router công khai dành cho khách tham quan.
# Các API trong router này không yêu cầu đăng nhập admin.
router = APIRouter(
    prefix="/api/public/guide",
    tags=["PUBLIC - Visitor Guide"],
)


@router.get(
    "/load-all",
    response_model=list[GuideItemResponse],
)
def load_all_guides(
    language_code: LanguageCode = Query(
        ...,
        description=(
            "Ngôn ngữ khách lựa chọn: "
            "vi, en, fr, zh hoặc ko"
        ),
    ),
):
    """
    Trả toàn bộ POI đang hoạt động cùng nội dung thuyết minh.

    Frontend gọi API này sau khi khách chọn ngôn ngữ.
    Sau đó frontend lưu danh sách POI và tự dùng GPS để
    kiểm tra khách đã đi vào bán kính địa điểm hay chưa.
    """

    return guide_service.get_all_guides(
        language_code=language_code,
    )


@router.get(
    "/nearby",
    response_model=NearbyGuideResponse | None,
)
def get_nearby_guide(
    latitude: float = Query(
        ...,
        ge=-90,
        le=90,
        description="Vĩ độ hiện tại của khách",
    ),
    longitude: float = Query(
        ...,
        ge=-180,
        le=180,
        description="Kinh độ hiện tại của khách",
    ),
    language_code: LanguageCode = Query(
        ...,
        description=(
            "Ngôn ngữ khách lựa chọn: "
            "Vietnamese, English, French, Chinese hoặc Korean"
        ),
    ),
):
    """
    Tìm một POI gần vị trí hiện tại của khách.

    API này vẫn được giữ để kiểm tra chức năng nearby
    hoặc dùng khi frontend muốn backend tính khoảng cách.
    """

    return guide_service.get_nearby_guide(
        latitude=latitude,
        longitude=longitude,
        language_code=language_code,
    )