"""Cấu hình và dữ liệu giả dùng chung cho toàn bộ test."""
import os
from datetime import datetime, timezone

# PHẢI đặt trước khi import bất kỳ module app.* nào: app/database.py kiểm tra
# biến môi trường ngay lúc import. Test không bao giờ kết nối SQL Server thật
# (SQLAlchemy chỉ tạo engine, không mở kết nối).
os.environ.setdefault("DB_SERVER", "localhost")
os.environ.setdefault("DB_NAME", "MuseumGuideDB")
os.environ.setdefault("DB_DRIVER", "ODBC Driver 18 for SQL Server")
os.environ.setdefault("JWT_SECRET_KEY", "pytest-only-secret-key-at-least-32-bytes")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


class FakeBackend:
    """SQL Server + Edge-TTS giả, chạy hoàn toàn trong bộ nhớ."""

    def __init__(self):
        self.pois: dict[int, dict] = {}
        self.translations: dict[int, dict] = {}
        self.admins: dict[int, dict] = {}
        self.audio_files: set[str] = set()  # các file MP3 đang "tồn tại"
        self._poi_seq = 1
        self._translation_seq = 1
        self._audio_seq = 1

    # ------------------------------------------------------------------
    # Helper để test dựng sẵn dữ liệu
    # ------------------------------------------------------------------
    def add_poi(self, **overrides) -> dict:
        data = {
            "name": "Điểm A",
            "description": "Mô tả điểm A",
            "address": "Bảo tàng",
            "latitude": 10.7769,
            "longitude": 106.7009,
            "trigger_radius_meters": 2.0,
        }
        data.update(overrides)
        return self._poi_create(data)

    def add_translation(
        self,
        poi_id: int,
        language_code: str = "vi",
        title: str = "Tiêu đề",
        narration_text: str = "Nội dung thuyết minh",
        is_active: bool = True,
    ) -> dict:
        translation = {
            "id": self._translation_seq,
            "poi_id": poi_id,
            "language_code": language_code,
            "title": title,
            "narration_text": narration_text,
            "audio_url": self._new_audio(),
            "is_active": is_active,
        }
        self.translations[translation["id"]] = translation
        self._translation_seq += 1
        return dict(translation)

    def add_admin(
        self,
        username: str = "admin01",
        password: str = "Secret123",
        role: str = "OWNER",
        is_active: bool = True,
    ) -> dict:
        from app.services.auth_service import password_hash

        admin = {
            "id": len(self.admins) + 1,
            "username": username,
            "password_hash": password_hash.hash(password),
            "full_name": "Quản trị viên",
            "phone": None,
            "email": None,
            "role": role,
            "is_active": is_active,
            "must_change_password": False,
            "last_login_at": None,
            "created_by_admin_id": None,
        }
        self.admins[admin["id"]] = admin
        return dict(admin)

    # ------------------------------------------------------------------
    # Thay thế repository / audio_service bằng bản giả
    # ------------------------------------------------------------------
    def install(self, monkeypatch) -> None:
        from app.repositaries.admin_repository import admin_repository
        from app.repositaries.poi_repository import poi_repository
        from app.repositaries.translation_repository import (
            translation_repository,
        )
        from app.services.audio_service import audio_service

        replacements = [
            (poi_repository, {
                "create": self._poi_create,
                "get_by_id": self._poi_get_by_id,
                "update": self._poi_update,
                "set_visibility": self._poi_set_visibility,
                "get_active": self._poi_get_active,
                "get_all_for_admin": self._poi_get_all,
            }),
            (translation_repository, {
                "create": self._tr_create,
                "get_by_id": self._tr_get_by_id,
                "get_by_poi_and_language": self._tr_get_by_poi_and_language,
                "get_all_by_poi": self._tr_get_all_by_poi,
                "get_all_for_admin_by_poi": self._tr_get_all_for_admin_by_poi,
                "update": self._tr_update,
                "set_visibility": self._tr_set_visibility,
                "get_public_guides": self._tr_get_public_guides,
            }),
            (admin_repository, {
                "get_by_username": self._admin_get_by_username,
                "get_by_id": self._admin_get_by_id,
                "update_last_login": self._admin_update_last_login,
            }),
            (audio_service, {
                "generate_audio": self._audio_generate,
                "delete_audio": self._audio_delete,
            }),
        ]

        for target, methods in replacements:
            for name, replacement in methods.items():
                monkeypatch.setattr(target, name, replacement)

    # ---- POI ----------------------------------------------------------
    def _poi_create(self, data: dict) -> dict:
        poi = {**data, "id": self._poi_seq, "is_active": True}
        self.pois[poi["id"]] = poi
        self._poi_seq += 1
        return dict(poi)

    def _poi_get_by_id(self, poi_id: int):
        poi = self.pois.get(poi_id)
        return dict(poi) if poi else None

    def _poi_update(self, poi_id: int, data: dict):
        poi = self.pois.get(poi_id)
        if poi is None:
            return None
        poi.update(data)
        return dict(poi)

    def _poi_set_visibility(self, poi_id: int, is_active: bool):
        poi = self.pois.get(poi_id)
        if poi is None:
            return None
        poi["is_active"] = is_active
        return dict(poi)

    def _poi_get_active(self) -> list[dict]:
        return [dict(p) for p in self.pois.values() if p["is_active"]]

    def _poi_get_all(self) -> list[dict]:
        return [dict(p) for p in self.pois.values()]

    # ---- Translation --------------------------------------------------
    def _tr_create(self, data: dict) -> dict:
        translation = {**data, "id": self._translation_seq, "is_active": True}
        self.translations[translation["id"]] = translation
        self._translation_seq += 1
        return dict(translation)

    def _tr_get_by_id(self, translation_id: int):
        translation = self.translations.get(translation_id)
        return dict(translation) if translation else None

    def _tr_get_by_poi_and_language(self, poi_id: int, language_code: str):
        # Giống SQL thật: chỉ trả bản dịch đang hiển thị.
        for t in self.translations.values():
            if (
                t["poi_id"] == poi_id
                and t["language_code"] == language_code
                and t["is_active"]
            ):
                return dict(t)
        return None

    def _tr_get_all_by_poi(self, poi_id: int) -> list[dict]:
        items = [
            dict(t) for t in self.translations.values()
            if t["poi_id"] == poi_id and t["is_active"]
        ]
        return sorted(items, key=lambda t: t["language_code"])

    def _tr_get_all_for_admin_by_poi(self, poi_id: int) -> list[dict]:
        items = [
            dict(t) for t in self.translations.values()
            if t["poi_id"] == poi_id
        ]
        return sorted(items, key=lambda t: t["language_code"])

    def _tr_update(self, translation_id: int, data: dict):
        translation = self.translations.get(translation_id)
        if translation is None:
            return None
        translation.update(data)
        return dict(translation)

    def _tr_set_visibility(self, translation_id: int, is_active: bool):
        translation = self.translations.get(translation_id)
        if translation is None:
            return None
        translation["is_active"] = is_active
        return dict(translation)

    def _tr_get_public_guides(self, requested_language_code: str) -> list[dict]:
        # Ưu tiên: ngôn ngữ yêu cầu -> en -> vi (giống truy vấn SQL).
        guides = []
        for poi in sorted(self.pois.values(), key=lambda p: p["id"]):
            if not poi["is_active"]:
                continue
            active = {
                t["language_code"]: t
                for t in self.translations.values()
                if t["poi_id"] == poi["id"] and t["is_active"]
            }
            chosen = next(
                (
                    active[code]
                    for code in (requested_language_code, "en", "vi")
                    if code in active
                ),
                None,
            )
            if chosen is None:
                continue
            guides.append({
                "poi_id": poi["id"],
                "poi_name": poi["name"],
                "address": poi["address"],
                "latitude": poi["latitude"],
                "longitude": poi["longitude"],
                "trigger_radius_meters": poi["trigger_radius_meters"],
                "requested_language_code": requested_language_code,
                "language_code": chosen["language_code"],
                "title": chosen["title"],
                "narration_text": chosen["narration_text"],
                "audio_url": chosen["audio_url"],
                "is_fallback": (
                    chosen["language_code"] != requested_language_code
                ),
            })
        return guides

    # ---- Admin --------------------------------------------------------
    def _admin_get_by_username(self, username: str):
        for admin in self.admins.values():
            if admin["username"] == username:
                return dict(admin)
        return None

    def _admin_get_by_id(self, admin_id: int):
        admin = self.admins.get(admin_id)
        return dict(admin) if admin else None

    def _admin_update_last_login(self, admin_id: int) -> None:
        self.admins[admin_id]["last_login_at"] = datetime.now(timezone.utc)

    # ---- Audio --------------------------------------------------------
    def _new_audio(self) -> str:
        url = f"/audio/fake-{self._audio_seq}.mp3"
        self._audio_seq += 1
        self.audio_files.add(url)
        return url

    async def _audio_generate(self, text: str, language_code: str) -> str:
        return self._new_audio()

    def _audio_delete(self, audio_url) -> bool:
        if audio_url in self.audio_files:
            self.audio_files.remove(audio_url)
            return True
        return False


@pytest.fixture
def backend(monkeypatch):
    """Thay SQL Server và Edge-TTS bằng bản giả trong bộ nhớ."""
    fake = FakeBackend()
    fake.install(monkeypatch)
    return fake


@pytest.fixture
def client(backend):
    """TestClient gọi app thật; backend giả đảm bảo không chạm DB thật."""
    from app.main import app

    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers(client, backend):
    """Đăng nhập thật qua API, trả header Authorization cho các API admin."""
    backend.add_admin(username="admin01", password="Secret123")
    response = client.post(
        "/api/auth/login",
        json={"username": "admin01", "password": "Secret123"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
