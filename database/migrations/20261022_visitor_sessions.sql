/*
   Add anonymous visitor activity and coarse device statistics.
   Run once against an existing MuseumGuideDB_V2 database.
*/
USE MuseumGuideDB_V2;
GO

IF OBJECT_ID(N'dbo.visitor_sessions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.visitor_sessions
    (
        guest_session_id UNIQUEIDENTIFIER NOT NULL,
        device_type NVARCHAR(30) NOT NULL,
        operating_system NVARCHAR(80) NOT NULL,
        browser NVARCHAR(80) NOT NULL,
        language_code NVARCHAR(5) NOT NULL,
        is_active BIT NOT NULL CONSTRAINT DF_visitor_sessions_is_active DEFAULT (1),
        first_seen_at DATETIME2 NOT NULL CONSTRAINT DF_visitor_sessions_first_seen DEFAULT (SYSUTCDATETIME()),
        last_seen_at DATETIME2 NOT NULL CONSTRAINT DF_visitor_sessions_last_seen DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT PK_visitor_sessions PRIMARY KEY (guest_session_id),
        CONSTRAINT CK_visitor_sessions_language CHECK (language_code IN ('vi', 'en', 'fr', 'zh', 'ko'))
    );

    CREATE INDEX IX_visitor_sessions_active_last_seen
        ON dbo.visitor_sessions(is_active, last_seen_at DESC)
        INCLUDE (device_type, operating_system, browser);
END;
GO
