/* Tạo database */
IF DB_ID(N'MuseumGuideDB') IS NULL
BEGIN
    CREATE DATABASE MuseumGuideDB;
END;
GO

USE MuseumGuideDB;
GO


/* Tài khoản quản trị */
IF OBJECT_ID(N'dbo.admins', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.admins
    (
        id INT IDENTITY(1,1) PRIMARY KEY,
        username NVARCHAR(50) NOT NULL UNIQUE,
        password_hash NVARCHAR(255) NOT NULL,
        is_active BIT NOT NULL
            CONSTRAINT DF_admins_is_active DEFAULT 1,
        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_admins_created_at DEFAULT SYSUTCDATETIME()
    );
END;
GO


/* Địa điểm thuyết minh */
IF OBJECT_ID(N'dbo.pois', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.pois
    (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(200) NOT NULL,
        description NVARCHAR(MAX) NOT NULL,
        address NVARCHAR(500) NOT NULL,

        latitude DECIMAL(10,7) NOT NULL,
        longitude DECIMAL(10,7) NOT NULL,

        trigger_radius_meters DECIMAL(6,2) NOT NULL
            CONSTRAINT DF_pois_radius DEFAULT 2,

        is_active BIT NOT NULL
            CONSTRAINT DF_pois_is_active DEFAULT 1,

        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_pois_created_at DEFAULT SYSUTCDATETIME(),

        updated_at DATETIME2 NULL,

        CONSTRAINT CK_pois_latitude
            CHECK (latitude BETWEEN -90 AND 90),

        CONSTRAINT CK_pois_longitude
            CHECK (longitude BETWEEN -180 AND 180),

        CONSTRAINT CK_pois_radius
            CHECK (
                trigger_radius_meters >= 0.5
                AND trigger_radius_meters <= 100
            )
    );
END;
GO


/* Nội dung thuyết minh theo từng ngôn ngữ */
IF OBJECT_ID(N'dbo.translations', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.translations
    (
        id INT IDENTITY(1,1) PRIMARY KEY,

        poi_id INT NOT NULL,
        language_code NVARCHAR(10) NOT NULL,

        title NVARCHAR(200) NOT NULL,
        narration_text NVARCHAR(MAX) NOT NULL,
        audio_url NVARCHAR(1000) NULL,

        is_active BIT NOT NULL
            CONSTRAINT DF_translations_is_active DEFAULT 1,

        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_translations_created_at DEFAULT SYSUTCDATETIME(),

        updated_at DATETIME2 NULL,

        CONSTRAINT FK_translations_pois
            FOREIGN KEY (poi_id)
            REFERENCES dbo.pois(id),

        CONSTRAINT UQ_translations_poi_language
            UNIQUE (poi_id, language_code),

        CONSTRAINT CK_translations_language
            CHECK (language_code IN ('vi', 'en', 'fr', 'zh', 'ko'))
    );
END;
GO


/* Hỗ trợ tìm nhanh POI theo trạng thái và tọa độ */
IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_pois_active_location'
      AND object_id = OBJECT_ID(N'dbo.pois')
)
BEGIN
    CREATE INDEX IX_pois_active_location
        ON dbo.pois(is_active, latitude, longitude);
END;
GO