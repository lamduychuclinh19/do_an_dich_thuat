/* Track when each account last changed its password. */
USE MuseumGuideDB_V2;
GO

IF COL_LENGTH(N'dbo.people', N'password_changed_at') IS NULL
BEGIN
    ALTER TABLE dbo.people
        ADD password_changed_at DATETIME2 NOT NULL
            CONSTRAINT DF_people_password_changed_at DEFAULT (SYSUTCDATETIME())
            WITH VALUES;
END;
GO
