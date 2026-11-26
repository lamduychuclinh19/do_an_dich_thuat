/* Khách đang dùng thuyết minh trong 90 giây gần nhất. */
USE MuseumGuideDB_V2;
GO

SELECT COUNT_BIG(*) AS active_tourists
FROM dbo.visitor_sessions
WHERE is_active = 1
  AND last_seen_at >= DATEADD(SECOND, -90, SYSUTCDATETIME());
GO

/* Phân nhóm khách đang hoạt động theo thiết bị, hệ điều hành và trình duyệt. */
SELECT
    device_type,
    operating_system,
    browser,
    COUNT_BIG(*) AS visitor_count
FROM dbo.visitor_sessions
WHERE is_active = 1
  AND last_seen_at >= DATEADD(SECOND, -90, SYSUTCDATETIME())
GROUP BY device_type, operating_system, browser
ORDER BY visitor_count DESC, device_type, operating_system, browser;
GO
