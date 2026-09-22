class PoiRepository:
    def __init__(self):
        self._pois = []
        self._next_id = 1

    def create(self, data: dict) -> dict:
        poi = {
            "id": self._next_id,
            "is_active": True,
            **data
        }

        self._pois.append(poi)
        self._next_id += 1

        return poi
    """
    Duyệt qua các địa điểm đang lưu.
    Nếu tìm thấy id giống poi_id, trả về địa điểm đó.
    Nếu duyệt hết vẫn không thấy, trả về None.
    """
    def get_by_id(self, poi_id: int) -> dict | None:
        for poi in self._pois:
            if poi["id"] == poi_id:
                return poi

        return None
    """
    Tìm địa điểm bằng id.
    Không tìm thấy → trả về None.
    Tìm thấy → poi.update(data) thay dữ liệu cũ bằng dữ liệu mới.
    id vẫn được giữ nguyên vì dữ liệu gửi vào không chứa id.
    """
    def update(self, poi_id: int, data: dict) -> dict | None:
        poi = self.get_by_id(poi_id)

        if poi is None:
            return None

        poi.update(data)
        return poi

    def set_visibility(self,poi_id: int,is_active: bool) -> dict | None:
        poi = self.get_by_id(poi_id)

        if poi is None:
            return None

        poi["is_active"] = is_active
        return poi

    # dành cho người dùng, chỉ thấy địa điểm đang hiển thị.
    def get_active(self) -> list:
        return [
            poi
            for poi in self._pois
            if poi["is_active"] is True
        ]
    #giữ lại để sau này trang quản trị xem được cả địa điểm đang ẩn.
    def get_all(self) -> list:
        return self._pois


poi_repository = PoiRepository()