from pydantic import BaseModel, Field


class PoiCreate(BaseModel):
    """Thông tin nội dung và vị trí của một POI."""

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    address: str = Field(min_length=1)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    trigger_radius_meters: int = Field(
        default=30,
        gt=0,
        le=500,
    )


class BackOfficePoiCreate(PoiCreate):
    """Dữ liệu tạo POI trong khu vực quản trị.

    - SYSTEM_ADMIN phải chọn owner_id của một SHOP_OWNER đang hoạt động.
    - SHOP_OWNER không cần gửi owner_id; backend tự lấy ID từ JWT.
    """

    id: str = Field(
        min_length=1,
        max_length=50,
        description=(
            "Mã địa điểm do người quản lý nhập, ví dụ BNR01"
        ),
    )

    owner_id: int | None = Field(
        default=None,
        gt=0,
        description=(
            "SYSTEM_ADMIN chọn mã SHOP_OWNER; "
            "SHOP_OWNER để trống vì backend lấy từ JWT"
        ),
    )


class PoiVisibility(BaseModel):
    """Trạng thái hiển thị; hệ thống chỉ ẩn POI chứ không xóa."""

    is_active: bool


class PoiResponse(PoiCreate):
    """Dữ liệu POI được phép trả về cho API public."""

    id: str
    is_active: bool


class BackOfficePoiResponse(PoiResponse):
    """Dữ liệu quản trị có thêm ID tài khoản sở hữu POI."""

    owner_id: int


class NearbyPoiResponse(PoiResponse):
    """POI gần khách tham quan kèm khoảng cách tính bằng mét."""

    distance_meters: float
