"""Persistence for moderated SHOP_OWNER content changes."""

from sqlalchemy import text

from app.database import engine


class ContentRequestRepository:
    def has_pending(self, request_type: str, key: str) -> bool:
        if request_type == "POI":
            query = text("""
                SELECT CASE WHEN EXISTS (
                    SELECT 1 FROM dbo.content_change_requests r
                    JOIN dbo.poi_change_request_details d ON d.request_id=r.id
                    WHERE r.request_type=N'POI' AND r.status IN (N'PENDING',N'PROCESSING')
                      AND d.requested_poi_id=:key
                ) THEN 1 ELSE 0 END
            """)
        else:
            query = text("""
                SELECT CASE WHEN EXISTS (
                    SELECT 1 FROM dbo.content_change_requests r
                    JOIN dbo.translation_change_request_details d ON d.request_id=r.id
                    WHERE r.request_type=N'TRANSLATION' AND r.status IN (N'PENDING',N'PROCESSING')
                      AND d.poi_id=:key
                ) THEN 1 ELSE 0 END
            """)
        with engine.connect() as connection:
            return bool(connection.execute(query, {"key": key}).scalar_one())

    def create(self, *, request_type: str, action: str, submitter_id: int,
               details: dict, previous_details: dict | None = None) -> dict:
        previous_details = previous_details or {}
        with engine.begin() as connection:
            request_id = connection.execute(text("""
                INSERT INTO dbo.content_change_requests
                    (request_type, action, submitted_by_person_id)
                OUTPUT INSERTED.id
                VALUES (:request_type, :action, :submitter_id)
            """), {
                "request_type": request_type, "action": action,
                "submitter_id": submitter_id,
            }).scalar_one()
            if request_type == "POI":
                poi_details = {key: details[key] for key in (
                    "requested_poi_id", "name", "description", "address",
                    "latitude", "longitude", "trigger_radius_meters",
                )}
                previous_columns = {
                    f"previous_{key}": previous_details.get(key)
                    for key in (
                        "name", "description", "address", "latitude",
                        "longitude", "trigger_radius_meters",
                    )
                }
                connection.execute(text("""
                    INSERT INTO dbo.poi_change_request_details
                        (request_id, requested_poi_id, name, description, address,
                         latitude, longitude, trigger_radius_meters, previous_name,
                         previous_description, previous_address, previous_latitude,
                         previous_longitude, previous_trigger_radius_meters)
                    VALUES (:request_id, :requested_poi_id, :name, :description,
                            :address, :latitude, :longitude, :trigger_radius_meters,
                            :previous_name, :previous_description, :previous_address,
                            :previous_latitude, :previous_longitude,
                            :previous_trigger_radius_meters)
                """), {**poi_details, **previous_columns, "request_id": request_id})
            else:
                translation_details = {key: details[key] for key in (
                    "poi_id", "title", "narration_text",
                )}
                previous_columns = {
                    "previous_title": previous_details.get("title"),
                    "previous_narration_text": previous_details.get("narration_text"),
                }
                connection.execute(text("""
                    INSERT INTO dbo.translation_change_request_details
                        (request_id, poi_id, title, narration_text, previous_title,
                         previous_narration_text)
                    VALUES (:request_id, :poi_id, :title, :narration_text,
                            :previous_title, :previous_narration_text)
                """), {**translation_details, **previous_columns, "request_id": request_id})
        return self.get(request_id)

    @staticmethod
    def _base_select() -> str:
        return """
            SELECT r.id, r.request_type, r.action, r.submitted_by_person_id,
                   p.username AS submitted_by_username, p.full_name AS submitter_name,
                   p.phone AS submitter_phone, p.email AS submitter_email,
                   r.status, r.created_at, r.reviewed_at,
                   r.admin_note
            FROM dbo.content_change_requests r
            JOIN dbo.people p ON p.id = r.submitted_by_person_id
        """

    def get(self, request_id: int) -> dict | None:
        with engine.connect() as connection:
            row = connection.execute(text(self._base_select() + " WHERE r.id=:id"), {"id": request_id}).mappings().first()
            if not row:
                return None
            item = dict(row)
            if item["request_type"] == "POI":
                details = connection.execute(text("""
                    SELECT requested_poi_id, name, description, address, latitude,
                           longitude, trigger_radius_meters, previous_name,
                           previous_description, previous_address, previous_latitude,
                           previous_longitude, previous_trigger_radius_meters
                    FROM dbo.poi_change_request_details WHERE request_id=:id
                """), {"id": request_id}).mappings().one()
                item["previous_details"] = self._previous_details(
                    details,
                    ("name", "description", "address", "latitude", "longitude", "trigger_radius_meters"),
                )
            else:
                details = connection.execute(text("""
                    SELECT poi_id, title, narration_text, previous_title,
                           previous_narration_text
                    FROM dbo.translation_change_request_details WHERE request_id=:id
                """), {"id": request_id}).mappings().one()
                item["previous_details"] = self._previous_details(
                    details, ("title", "narration_text")
                )
            item["details"] = dict(details)
            for key in tuple(item["details"]):
                if key.startswith("previous_"):
                    item["details"].pop(key)
            return item

    @staticmethod
    def _previous_details(row, keys: tuple[str, ...]) -> dict | None:
        previous = {key: row.get(f"previous_{key}") for key in keys}
        return previous if any(value is not None for value in previous.values()) else None

    def list_for_admin(self, request_type: str) -> list[dict]:
        if request_type == "POI":
            query = self._base_select() + """
                LEFT JOIN dbo.poi_change_request_details d ON d.request_id=r.id
                WHERE r.request_type=:kind
                ORDER BY CASE WHEN r.status='PENDING' THEN 0 ELSE 1 END,
                         r.created_at DESC, r.id DESC
            """
            target_columns = "d.requested_poi_id AS target_id, d.name AS target_name, d.address AS target_context"
        else:
            query = self._base_select() + """
                LEFT JOIN dbo.translation_change_request_details d ON d.request_id=r.id
                WHERE r.request_type=:kind
                ORDER BY CASE WHEN r.status='PENDING' THEN 0 ELSE 1 END,
                         r.created_at DESC, r.id DESC
            """
            target_columns = "d.poi_id AS target_id, d.title AS target_name, CAST(NULL AS NVARCHAR(500)) AS target_context"

        query = query.replace(
            "r.admin_note\n            FROM",
            f"r.admin_note, {target_columns}\n            FROM",
            1,
        )
        with engine.connect() as connection:
            ids = connection.execute(text(query), {"kind": request_type}).mappings().all()
        return [dict(row) for row in ids]

    def list_for_owner(self, owner_id: int) -> list[dict]:
        with engine.connect() as connection:
            rows = connection.execute(text("""
                SELECT r.id, r.request_type, r.action, r.submitted_by_person_id,
                       p.username AS submitted_by_username, p.full_name AS submitter_name,
                       p.phone AS submitter_phone, p.email AS submitter_email,
                       r.status, r.created_at, r.reviewed_at, r.admin_note,
                       pd.requested_poi_id AS poi_requested_poi_id,
                       pd.name AS poi_name, pd.description AS poi_description,
                       pd.address AS poi_address, pd.latitude AS poi_latitude,
                       pd.longitude AS poi_longitude,
                       pd.trigger_radius_meters AS poi_trigger_radius_meters,
                       pd.previous_name AS poi_previous_name,
                       pd.previous_description AS poi_previous_description,
                       pd.previous_address AS poi_previous_address,
                       pd.previous_latitude AS poi_previous_latitude,
                       pd.previous_longitude AS poi_previous_longitude,
                       pd.previous_trigger_radius_meters AS poi_previous_trigger_radius_meters,
                       td.poi_id AS translation_poi_id, td.title AS translation_title,
                       td.narration_text AS translation_narration_text,
                       td.previous_title AS translation_previous_title,
                       td.previous_narration_text AS translation_previous_narration_text
                FROM dbo.content_change_requests r
                JOIN dbo.people p ON p.id=r.submitted_by_person_id
                LEFT JOIN dbo.poi_change_request_details pd ON pd.request_id=r.id
                LEFT JOIN dbo.translation_change_request_details td ON td.request_id=r.id
                WHERE r.submitted_by_person_id=:owner_id
                ORDER BY r.created_at DESC, r.id DESC
            """), {"owner_id": owner_id}).mappings().all()
        items = []
        for row in rows:
            item = dict(row)
            if item["request_type"] == "POI":
                fields = ("name", "description", "address", "latitude", "longitude", "trigger_radius_meters")
                item["details"] = {
                    "requested_poi_id": row["poi_requested_poi_id"],
                    **{field: row[f"poi_{field}"] for field in fields},
                }
                item["previous_details"] = self._previous_details(
                    {f"previous_{field}": row[f"poi_previous_{field}"] for field in fields},
                    fields,
                )
            else:
                fields = ("title", "narration_text")
                item["details"] = {
                    "poi_id": row["translation_poi_id"],
                    "title": row["translation_title"],
                    "narration_text": row["translation_narration_text"],
                }
                item["previous_details"] = self._previous_details(
                    {
                        "previous_title": row["translation_previous_title"],
                        "previous_narration_text": row["translation_previous_narration_text"],
                    },
                    fields,
                )
            for key in tuple(item):
                if key.startswith("poi_") or key.startswith("translation_"):
                    item.pop(key)
            items.append(item)
        return items

    def claim(self, request_id: int) -> dict | None:
        with engine.begin() as connection:
            row = connection.execute(text("""
                UPDATE dbo.content_change_requests WITH (ROWLOCK)
                SET status=N'PROCESSING', processing_at=SYSUTCDATETIME()
                OUTPUT INSERTED.id
                WHERE id=:id AND (status=N'PENDING' OR
                    (status=N'PROCESSING' AND processing_at < DATEADD(MINUTE,-10,SYSUTCDATETIME())))
            """), {"id": request_id}).first()
        return self.get(request_id) if row else None

    def release(self, request_id: int) -> None:
        with engine.begin() as connection:
            connection.execute(text("""
                UPDATE dbo.content_change_requests
                SET status=N'PENDING', processing_at=NULL WHERE id=:id AND status=N'PROCESSING'
            """), {"id": request_id})

    def finalize(self, request: dict, admin_id: int, approved: bool, note: str) -> None:
        status_value = "APPROVED" if approved else "REJECTED"
        action = "tạo mới" if request["action"] == "CREATE" else "cập nhật"
        subject = "địa điểm" if request["request_type"] == "POI" else "bản dịch"
        content_key = "requested_poi_id" if request["request_type"] == "POI" else "poi_id"
        target = request["details"].get(content_key, "")
        message = (
            f"Yêu cầu {action} {subject} {target} (#{request['id']}) "
            f"đã được {'chấp thuận' if approved else 'từ chối'}. "
            f"Ghi chú của admin: {note}"
        )
        with engine.begin() as connection:
            result = connection.execute(text("""
                UPDATE dbo.content_change_requests
                SET status=:status, processing_at=NULL, reviewed_at=SYSUTCDATETIME(),
                    reviewed_by_person_id=:admin_id, admin_note=:note
                WHERE id=:id AND status IN (N'PENDING', N'PROCESSING')
            """), {"status": status_value, "admin_id": admin_id,
                  "note": note, "id": request["id"]})
            if result.rowcount != 1:
                raise ValueError("Yêu cầu đã được xử lý bởi quản trị viên khác")
            connection.execute(text("""
                INSERT INTO dbo.owner_notifications
                    (owner_person_id, notification_type, message)
                VALUES (:owner_id, :kind, :message)
            """), {"owner_id": request["submitted_by_person_id"],
                  "kind": "POI_REVIEW" if request["request_type"] == "POI" else "TRANSLATION_REVIEW",
                  "message": message})

    def notifications(self, owner_id: int) -> list[dict]:
        with engine.connect() as connection:
            rows = connection.execute(text("""
                SELECT id, notification_type, message, created_at, is_read
                FROM dbo.owner_notifications
                WHERE owner_person_id=:owner_id
                ORDER BY created_at DESC, id DESC
            """), {"owner_id": owner_id}).mappings().all()
        return [dict(row) for row in rows]

    def mark_notification_read(self, owner_id: int, notification_id: int) -> bool:
        with engine.begin() as connection:
            result = connection.execute(text("""
                UPDATE dbo.owner_notifications SET is_read=1
                WHERE id=:id AND owner_person_id=:owner_id
            """), {"id": notification_id, "owner_id": owner_id})
        return result.rowcount == 1


content_request_repository = ContentRequestRepository()
