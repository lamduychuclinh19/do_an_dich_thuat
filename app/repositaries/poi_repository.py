class PoiRepository:
    def __init__(self):
        self._pois = []
        self._next_id = 1

    def create(self, data: dict) -> dict:
        poi = {
            "id": self._next_id,
            **data
        }

        self._pois.append(poi)
        self._next_id += 1

        return poi

    def get_all(self) -> list:
        return self._pois


poi_repository = PoiRepository()