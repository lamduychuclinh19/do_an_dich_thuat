/* Remove retired translation-approval and owner-notification tables.
   Run this against an existing MuseumGuideDB_V2 database after backing it up. */
SET XACT_ABORT ON;
BEGIN TRANSACTION;

/* Drop triggers before their target tables. */
IF OBJECT_ID(N'dbo.TR_translation_submission_roles', N'TR') IS NOT NULL
    DROP TRIGGER dbo.TR_translation_submission_roles;
IF OBJECT_ID(N'dbo.TR_owner_notifications_role', N'TR') IS NOT NULL
    DROP TRIGGER dbo.TR_owner_notifications_role;

/* Remove old translation review requests and their details. */
IF OBJECT_ID(N'dbo.translation_change_request_details', N'U') IS NOT NULL
    DROP TABLE dbo.translation_change_request_details;
IF OBJECT_ID(N'dbo.audit_log', N'U') IS NOT NULL
    DROP TABLE dbo.audit_log;
IF OBJECT_ID(N'dbo.translation_submission', N'U') IS NOT NULL
    DROP TABLE dbo.translation_submission;
IF OBJECT_ID(N'dbo.owner_notifications', N'U') IS NOT NULL
    DROP TABLE dbo.owner_notifications;

/* Generic review requests now apply only to POI changes. */
IF OBJECT_ID(N'dbo.content_change_requests', N'U') IS NOT NULL
BEGIN
    DELETE FROM dbo.content_change_requests WHERE request_type = N'TRANSLATION';

    IF EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_content_change_requests_type')
        ALTER TABLE dbo.content_change_requests DROP CONSTRAINT CK_content_change_requests_type;

    ALTER TABLE dbo.content_change_requests
        ADD CONSTRAINT CK_content_change_requests_type CHECK (request_type = N'POI');
END;

COMMIT TRANSACTION;
GO
