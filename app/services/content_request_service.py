from fastapi import HTTPException

from app.repositaries.content_request_repository import content_request_repository
from app.repositaries.poi_repository import poi_repository
from app.schemas.content_request_schema import ContentRequestCreate
from app.schemas.poi_schema import PoiCreate
from app.schemas.translation_schema import TranslationSourceCreate, TranslationSourceUpdate
from app.services.poi_service import poi_service
from app.services.translation_service import translation_service


class ContentRequestService:
    def submit(self, data: ContentRequestCreate, owner: dict) -> dict:
        if owner.get("role") != "SHOP_OWNER":
            raise HTTPException(status_code=403, detail="Chỉ Chủ địa điểm mới được gửi yêu cầu thay đổi nội dung")
        details = dict(data.details)
        previous_details = None
        target_id = str(data.target_poi_id or details.get("poi_id") or "").strip()

        if data.request_type == "POI":
            if data.action == "CREATE":
                details["requested_poi_id"] = str(details.get("id", "")).strip().upper()
                if not details["requested_poi_id"]:
                    raise HTTPException(status_code=422, detail="Mã địa điểm không được để trống")
                if len(details["requested_poi_id"]) > 10:
                    raise HTTPException(status_code=422, detail="Mã địa điểm không được dài quá 10 ký tự")
                payload = PoiCreate(**details).model_dump()
                target_id = None
            else:
                target_id = str(data.target_poi_id or "").strip()
                current = poi_repository.get_by_id_for_owner(target_id, owner["id"])
                if not current:
                    raise HTTPException(status_code=404, detail="Không tìm thấy địa điểm của Chủ địa điểm")
                previous_details = {
                    key: current[key]
                    for key in (
                        "name", "description", "address", "latitude", "longitude",
                        "trigger_radius_meters",
                    )
                }
                payload = PoiCreate(**details).model_dump()
                details["requested_poi_id"] = target_id
            if data.action == "CREATE" and poi_repository.get_by_id(details["requested_poi_id"]):
                raise HTTPException(status_code=409, detail="Mã địa điểm đã tồn tại")
            details.update(payload)
            if content_request_repository.has_pending("POI", details["requested_poi_id"]):
                raise HTTPException(status_code=409, detail="Địa điểm này đang có yêu cầu chờ quản trị viên xử lý")
        else:
            target_id = str(target_id).strip()
            poi = poi_repository.get_by_id_for_owner(target_id, owner["id"])
            if not poi:
                raise HTTPException(status_code=404, detail="Không tìm thấy địa điểm của Chủ địa điểm")
            existing = translation_service.get_all_translations_for_back_office(
                target_id, {"id": owner["id"], "role": "SHOP_OWNER"}
            )
            current_source = next(
                (item for item in existing if item.get("language_code") == "vi"),
                None,
            )
            if data.action == "CREATE" and existing:
                raise HTTPException(status_code=409, detail="Địa điểm đã có bản dịch; hãy gửi yêu cầu cập nhật")
            if data.action == "UPDATE" and not existing:
                raise HTTPException(status_code=409, detail="Địa điểm chưa có bản dịch; hãy gửi yêu cầu tạo")
            if data.action == "UPDATE" and not current_source:
                raise HTTPException(status_code=409, detail="Không tìm thấy nội dung nguồn tiếng Việt hiện tại")
            if data.action == "UPDATE" and current_source:
                previous_details = {
                    "title": current_source["title"],
                    "narration_text": current_source["narration_text"],
                }
            details = {
                "poi_id": target_id,
                "title": str(details.get("title", "")).strip(),
                "narration_text": str(details.get("narration_text", "")).strip(),
            }
            TranslationSourceCreate(**details)
            if content_request_repository.has_pending("TRANSLATION", target_id):
                raise HTTPException(status_code=409, detail="Địa điểm này đang có yêu cầu bản dịch chờ quản trị viên xử lý")

        return content_request_repository.create(
            request_type=data.request_type,
            action=data.action,
            submitter_id=owner["id"],
            details=details,
            previous_details=previous_details,
        )

    def list_admin(self, request_type: str, admin: dict) -> list[dict]:
        self._require_admin(admin)
        if request_type not in {"POI", "TRANSLATION"}:
            raise HTTPException(status_code=422, detail="Loại yêu cầu không hợp lệ")
        return content_request_repository.list_for_admin(request_type)

    def get_admin(self, request_id: int, admin: dict) -> dict:
        self._require_admin(admin)
        item = content_request_repository.get(request_id)
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
        self._restore_legacy_pending_snapshot(item)
        return item

    async def decide(self, request_id: int, approved: bool, note: str, admin: dict) -> dict:
        self._require_admin(admin)
        normalized_note = note.strip()
        if not normalized_note:
            raise HTTPException(status_code=422, detail="Admin phải nhập ghi chú trước khi xử lý")
        request = content_request_repository.claim(request_id)
        if not request:
            raise HTTPException(status_code=409, detail="Yêu cầu đã được xử lý hoặc đang được admin khác xem xét")
        try:
            if approved:
                data = request["details"]
                owner = {"id": request["submitted_by_person_id"], "role": "SHOP_OWNER"}
                if request["request_type"] == "POI":
                    poi_data = PoiCreate(**{key: data[key] for key in (
                        "name", "description", "address", "latitude", "longitude", "trigger_radius_meters"
                    )})
                    if request["action"] == "CREATE":
                        poi_service.create_poi(poi_data, owner["id"], data["requested_poi_id"])
                    else:
                        poi_service.update_poi(data["requested_poi_id"], poi_data, owner["id"])
                elif request["action"] == "CREATE":
                    await translation_service.create_from_vietnamese_for_back_office(
                        TranslationSourceCreate(**data), admin
                    )
                else:
                    await translation_service.update_vietnamese_source_for_back_office(
                        data["poi_id"], TranslationSourceUpdate(
                            title=data["title"], narration_text=data["narration_text"]
                        ), admin
                    )
            content_request_repository.finalize(request, admin["id"], approved, normalized_note)
        except HTTPException:
            content_request_repository.release(request_id)
            raise
        except Exception as error:
            content_request_repository.release(request_id)
            raise HTTPException(status_code=500, detail="Không thể hoàn tất yêu cầu; dữ liệu chưa được duyệt") from error
        return {"message": "Đã lưu kết quả kiểm duyệt", "status": "APPROVED" if approved else "REJECTED"}

    @staticmethod
    def _require_admin(person: dict) -> None:
        if person.get("role") != "SYSTEM_ADMIN":
            raise HTTPException(status_code=403, detail="Chỉ SYSTEM_ADMIN được xử lý yêu cầu")

    def owner_requests(self, owner: dict) -> list[dict]:
        if owner.get("role") != "SHOP_OWNER":
            raise HTTPException(status_code=403, detail="Chức năng chỉ dành cho Chủ địa điểm")
        items = content_request_repository.list_for_owner(owner["id"])
        for item in items:
            self._restore_legacy_pending_snapshot(item)
        return items

    @staticmethod
    def _restore_legacy_pending_snapshot(request: dict) -> None:
        """Use the still-current DB row as the old version for legacy pending updates."""
        if (
            request.get("action") != "UPDATE"
            or request.get("status") not in {"PENDING", "PROCESSING"}
            or request.get("previous_details")
        ):
            return

        owner_id = request["submitted_by_person_id"]
        details = request.get("details") or {}
        if request.get("request_type") == "POI":
            current = poi_repository.get_by_id_for_owner(
                details.get("requested_poi_id"), owner_id
            )
            if current:
                request["previous_details"] = {
                    key: current.get(key)
                    for key in (
                        "name", "description", "address", "latitude", "longitude",
                        "trigger_radius_meters",
                    )
                }
            return

        translations = translation_service.get_all_translations_for_back_office(
            details.get("poi_id"), {"id": owner_id, "role": "SHOP_OWNER"}
        )
        source = next(
            (item for item in translations if item.get("language_code") == "vi"),
            None,
        )
        if source:
            request["previous_details"] = {
                "title": source.get("title"),
                "narration_text": source.get("narration_text"),
            }

    def owner_notifications(self, owner: dict) -> list[dict]:
        if owner.get("role") != "SHOP_OWNER":
            raise HTTPException(status_code=403, detail="Chức năng chỉ dành cho Chủ địa điểm")
        return content_request_repository.notifications(owner["id"])

    def mark_notification_read(self, notification_id: int, owner: dict) -> None:
        if owner.get("role") != "SHOP_OWNER":
            raise HTTPException(status_code=403, detail="Chức năng chỉ dành cho Chủ địa điểm")
        if not content_request_repository.mark_notification_read(owner["id"], notification_id):
            raise HTTPException(status_code=404, detail="Không tìm thấy thông báo")


content_request_service = ContentRequestService()
