"""Repository ghi nhận phiên khách ẩn danh đang dùng thuyết minh."""

from uuid import UUID

from sqlalchemy import text

from app.database import engine


class VisitorSessionRepository:
    ACTIVE_WINDOW_SECONDS = 90

    def heartbeat(
        self,
        guest_session_id: UUID,
        device_type: str,
        operating_system: str,
        browser: str,
        language_code: str,
    ) -> None:
        """Gia hạn phiên hiện tại và đánh dấu các phiên hết heartbeat là offline."""
        with engine.begin() as connection:
            connection.execute(
                text("""
                    UPDATE dbo.visitor_sessions
                    SET is_active = 0
                    WHERE is_active = 1
                      AND last_seen_at < DATEADD(
                          SECOND, -:active_window, SYSUTCDATETIME()
                      );
                """),
                {"active_window": self.ACTIVE_WINDOW_SECONDS},
            )
            connection.execute(
                text("""
                    MERGE dbo.visitor_sessions WITH (HOLDLOCK) AS target
                    USING (SELECT :guest_session_id AS guest_session_id) AS source
                      ON target.guest_session_id = source.guest_session_id
                    WHEN MATCHED THEN UPDATE SET
                        device_type = :device_type,
                        operating_system = :operating_system,
                        browser = :browser,
                        language_code = :language_code,
                        is_active = 1,
                        last_seen_at = SYSUTCDATETIME()
                    WHEN NOT MATCHED THEN INSERT
                        (guest_session_id, device_type, operating_system,
                         browser, language_code, is_active, first_seen_at,
                         last_seen_at)
                    VALUES
                        (:guest_session_id, :device_type, :operating_system,
                         :browser, :language_code, 1, SYSUTCDATETIME(),
                         SYSUTCDATETIME());
                """),
                {
                    "guest_session_id": str(guest_session_id),
                    "device_type": device_type,
                    "operating_system": operating_system,
                    "browser": browser,
                    "language_code": language_code,
                },
            )

    def get_active_summary(self) -> dict:
        """Expire quiet sessions and return the active count and device breakdown."""
        with engine.begin() as connection:
            connection.execute(
                text("""
                    UPDATE dbo.visitor_sessions
                    SET is_active = 0
                    WHERE is_active = 1
                      AND last_seen_at < DATEADD(
                          SECOND, -:active_window, SYSUTCDATETIME()
                      );
                """),
                {"active_window": self.ACTIVE_WINDOW_SECONDS},
            )
            active_visitors = connection.execute(
                text("""
                    SELECT COUNT_BIG(*)
                    FROM dbo.visitor_sessions
                    WHERE is_active = 1
                """)
            ).scalar_one()
            rows = connection.execute(
                text("""
                    SELECT device_type, operating_system, browser,
                           COUNT_BIG(*) AS visitor_count
                    FROM dbo.visitor_sessions
                    WHERE is_active = 1
                    GROUP BY device_type, operating_system, browser
                    ORDER BY visitor_count DESC, device_type,
                             operating_system, browser
                """)
            ).mappings().all()

        return {
            "active_visitors": int(active_visitors),
            "devices": [dict(row) for row in rows],
        }


visitor_session_repository = VisitorSessionRepository()
