"""Nghiệp vụ POI dùng chung cho public và khu quản trị chủ địa điểm."""

from math import atan2, cos, radians, sin, sqrt

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.repositaries.people_repository import people_repository
from app.repositaries.poi_repository import poi_repository
from app.schemas.poi_schema import PoiCreate, PoiVisibility


class PoiService:
    """Áp dụng quy tắc nghiệp vụ trước khi gọi repository."""

    @staticmethod
    def _raise_not_found() -> None:
        """Không tiết lộ POI không tồn tại hay thuộc một chủ quán khác."""
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy địa điểm",
        )

    @staticmethod
    def _ensure_back_office(current_person: dict) -> None:
        """Chỉ SYSTEM_ADMIN hoặc SHOP_OWNER được quản lý POI."""
        if current_person.get("role") not in {
            "SYSTEM_ADMIN",
            "SHOP_OWNER",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền quản lý địa điểm",
            )

    def _resolve_owner_id_for_create(
        self,
        current_person: dict,
        requested_owner_id: int | None,
    ) -> int:
        """Xác định chủ sở hữu thật khi tạo POI.

        SHOP_OWNER luôn dùng ID trong JWT. SYSTEM_ADMIN phải chọn một
        tài khoản SHOP_OWNER đang hoạt động để POI không bị vô chủ.
        """
        self._ensure_back_office(current_person)

        if current_person["role"] == "SHOP_OWNER":
            if (
                requested_owner_id is not None
                and requested_owner_id != current_person["id"]
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Chủ địa điểm không được tạo POI cho "
                        "tài khoản khác"
                    ),
                )

            return current_person["id"]

        if requested_owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "SYSTEM_ADMIN phải chọn owner_id của SHOP_OWNER "
                    "khi tạo POI"
                ),
            )

        owner = people_repository.get_by_id(requested_owner_id)
        if owner is None or owner["role"] != "SHOP_OWNER":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="owner_id phải thuộc một tài khoản SHOP_OWNER",
            )

        if not bool(owner["is_active"]):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Không thể giao POI cho SHOP_OWNER đang bị khóa",
            )

        return owner["id"]

    def create_poi_for_back_office(
        self,
        data: PoiCreate,
        current_person: dict,
        requested_poi_id: str,
        requested_owner_id: int | None = None,
    ) -> dict:
        """Tạo POI theo vai trò và gắn đúng SHOP_OWNER."""
        owner_id = self._resolve_owner_id_for_create(
            current_person=current_person,
            requested_owner_id=requested_owner_id,
        )

        normalized_poi_id = requested_poi_id.strip()

        if not normalized_poi_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Mã địa điểm không được để trống",
            )

        if (
            poi_repository.get_by_id(normalized_poi_id) is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Mã địa điểm đã tồn tại",
            )

        try:
            return poi_repository.create(
                data=data.model_dump(),
                owner_id=owner_id,
                poi_id=normalized_poi_id,
            )
        except IntegrityError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Mã địa điểm đã tồn tại",
            ) from error

    def get_all_pois_for_back_office(
        self,
        current_person: dict,
    ) -> list[dict]:
        """SYSTEM_ADMIN xem tất cả; SHOP_OWNER chỉ xem POI của mình."""
        self._ensure_back_office(current_person)

        if current_person["role"] == "SYSTEM_ADMIN":
            return poi_repository.get_all_for_system_admin()

        return poi_repository.get_all_for_owner(current_person["id"])

    def update_poi_for_back_office(
        self,
        poi_id: str,
        data: PoiCreate,
        current_person: dict,
    ) -> dict:
        """Cập nhật POI theo phạm vi quyền của người đang đăng nhập."""
        self._ensure_back_office(current_person)

        if current_person["role"] == "SYSTEM_ADMIN":
            updated_poi = poi_repository.update_as_system_admin(
                poi_id=poi_id,
                data=data.model_dump(),
            )
        else:
            updated_poi = poi_repository.update(
                poi_id=poi_id,
                owner_id=current_person["id"],
                data=data.model_dump(),
            )

        if updated_poi is None:
            self._raise_not_found()

        return updated_poi

    def set_poi_visibility_for_back_office(
        self,
        poi_id: str,
        data: PoiVisibility,
        current_person: dict,
    ) -> dict:
        """Ẩn/hiện POI theo phạm vi quyền, tuyệt đối không xóa POI."""
        self._ensure_back_office(current_person)

        if current_person["role"] == "SYSTEM_ADMIN":
            updated_poi = (
                poi_repository.set_visibility_as_system_admin(
                    poi_id=poi_id,
                    is_active=data.is_active,
                )
            )
        else:
            updated_poi = poi_repository.set_visibility(
                poi_id=poi_id,
                owner_id=current_person["id"],
                is_active=data.is_active,
            )

        if updated_poi is None:
            self._raise_not_found()

        return updated_poi

    def create_poi(
        self,
        data: PoiCreate,
        owner_id: int,
        poi_id: str,
    ) -> dict:
        """Tạo POI cho SHOP_OWNER đang đăng nhập."""
        return poi_repository.create(
            data=data.model_dump(),
            owner_id=owner_id,
            poi_id=poi_id.strip(),
        )

    def get_poi_by_id(self, poi_id: str) -> dict:
        """API public chỉ được xem POI đang hoạt động."""
        poi = poi_repository.get_by_id(poi_id)

        if poi is None or not poi["is_active"]:
            self._raise_not_found()

        return poi

    def update_poi(
        self,
        poi_id: str,
        data: PoiCreate,
        owner_id: int,
    ) -> dict:
        """Chỉ cập nhật POI thuộc SHOP_OWNER hiện tại."""
        updated_poi = poi_repository.update(
            poi_id=poi_id,
            owner_id=owner_id,
            data=data.model_dump(),
        )

        if updated_poi is None:
            self._raise_not_found()

        return updated_poi

    def set_poi_visibility(
        self,
        poi_id: str,
        data: PoiVisibility,
        owner_id: int,
    ) -> dict:
        """Ẩn/hiện POI thay vì xóa POI khỏi hệ thống."""
        updated_poi = poi_repository.set_visibility(
            poi_id=poi_id,
            owner_id=owner_id,
            is_active=data.is_active,
        )

        if updated_poi is None:
            self._raise_not_found()

        return updated_poi

    def get_all_pois(self) -> list[dict]:
        """Danh sách public chỉ gồm POI đang hoạt động."""
        return poi_repository.get_active()

    def get_all_pois_for_owner(self, owner_id: int) -> list[dict]:
        """Chủ quán xem toàn bộ POI của mình, kể cả POI đang ẩn."""
        return poi_repository.get_all_for_owner(owner_id)

    # Giữ tên cũ để nơi khác chưa kịp đổi vẫn có thể gọi service.
    def get_all_pois_for_admin(self, owner_id: int) -> list[dict]:
        return self.get_all_pois_for_owner(owner_id)

    @staticmethod
    def calculate_distance(
        user_latitude: float,
        user_longitude: float,
        poi_latitude: float,
        poi_longitude: float,
    ) -> float:
        """Tính khoảng cách hai tọa độ bằng công thức Haversine, đơn vị mét."""
        earth_radius = 6_371_000

        user_lat = radians(user_latitude)
        user_lng = radians(user_longitude)
        poi_lat = radians(poi_latitude)
        poi_lng = radians(poi_longitude)

        difference_lat = poi_lat - user_lat
        difference_lng = poi_lng - user_lng

        a = (
            sin(difference_lat / 2) ** 2
            + cos(user_lat)
            * cos(poi_lat)
            * sin(difference_lng / 2) ** 2
        )
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return earth_radius * c

    def find_nearby_poi(
        self,
        latitude: float,
        longitude: float,
    ) -> dict | None:
        """Trả POI hoạt động gần nhất khi khách nằm trong bán kính kích hoạt."""
        nearest_poi = None

        for poi in poi_repository.get_active():
            distance = self.calculate_distance(
                latitude,
                longitude,
                poi["latitude"],
                poi["longitude"],
            )

            if distance <= poi["trigger_radius_meters"]:
                if (
                    nearest_poi is None
                    or distance < nearest_poi["distance_meters"]
                ):
                    nearest_poi = {
                        **poi,
                        "distance_meters": round(distance, 2),
                    }

        return nearest_poi


poi_service = PoiService()
