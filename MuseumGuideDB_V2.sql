

USE master;
GO

IF DB_ID(N'MuseumGuideDB_V2') IS NULL
BEGIN
    EXEC(N'CREATE DATABASE MuseumGuideDB_V2;');
END;
GO

USE MuseumGuideDB_V2;
GO
SET XACT_ABORT ON;
GO

/* ================================================================
   1. ACCOUNTS (ERD owner/admin)
   Shared account entity: role distinguishes SYSTEM_ADMIN and SHOP_OWNER.
   ================================================================ */
IF OBJECT_ID(N'dbo.people', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.people
    (
        id INT IDENTITY(1,1) NOT NULL,
        username NVARCHAR(50) NOT NULL,
        password_hash NVARCHAR(255) NOT NULL,
        full_name NVARCHAR(150) NOT NULL,
        phone NVARCHAR(10) NOT NULL,
        email NVARCHAR(255) NOT NULL,
        role NVARCHAR(30) NOT NULL,
        is_active BIT NOT NULL CONSTRAINT DF_people_is_active DEFAULT (1),
        must_change_password BIT NOT NULL CONSTRAINT DF_people_must_change_password DEFAULT (0),
        last_login_at DATETIME2 NULL,
        created_by_person_id INT NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_people_created_at DEFAULT (SYSUTCDATETIME()),
        updated_at DATETIME2 NULL,

        CONSTRAINT PK_people PRIMARY KEY (id),
        CONSTRAINT UQ_people_username UNIQUE (username),
        CONSTRAINT UQ_people_email UNIQUE (email),
        CONSTRAINT CK_people_role CHECK (role IN (N'SYSTEM_ADMIN', N'SHOP_OWNER')),
        CONSTRAINT CK_people_username CHECK
            (LEN(username) BETWEEN 4 AND 50 AND username NOT LIKE N'%[^A-Za-z0-9_.-]%'),
        CONSTRAINT CK_people_phone CHECK
            (LEN(phone) = 10 AND phone LIKE N'0%' AND phone NOT LIKE N'%[^0-9]%'),
        CONSTRAINT CK_people_email CHECK (email LIKE N'%_@gmail.com'),
        CONSTRAINT FK_people_created_by FOREIGN KEY (created_by_person_id)
            REFERENCES dbo.people(id)
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.people') AND name = N'UX_people_phone')
    CREATE UNIQUE INDEX UX_people_phone ON dbo.people(phone);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.people') AND name = N'IX_people_role_active')
    CREATE INDEX IX_people_role_active ON dbo.people(role, is_active);
GO

/* ================================================================
   2. OWNER REGISTRATION REQUESTS (ERD poi_owner_registrations)
   A pending request is not yet an account and cannot log in.
   ================================================================ */
IF OBJECT_ID(N'dbo.poi_owner_registrations', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.poi_owner_registrations
    (
        id INT IDENTITY(1,1) NOT NULL,
        username NVARCHAR(50) NOT NULL,
        password_hash NVARCHAR(255) NOT NULL,
        full_name NVARCHAR(150) NOT NULL,
        phone NVARCHAR(10) NOT NULL,
        email NVARCHAR(255) NOT NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_poi_owner_registrations_created_at DEFAULT (SYSUTCDATETIME()),
        reviewed_at DATETIME2 NULL,
        status TINYINT NULL,
        admin_note NVARCHAR(2000) NULL,
        reviewed_by_username NVARCHAR(50) NULL,

        CONSTRAINT PK_poi_owner_registrations PRIMARY KEY (id),
        CONSTRAINT CK_poi_owner_registrations_status CHECK (status IS NULL OR status IN (0, 1)),
        CONSTRAINT CK_poi_owner_registrations_review_state CHECK
        (
            (reviewed_at IS NULL AND status IS NULL AND reviewed_by_username IS NULL)
            OR
            (reviewed_at IS NOT NULL AND status IS NOT NULL AND reviewed_by_username IS NOT NULL)
        ),
        CONSTRAINT CK_poi_owner_registrations_username CHECK
            (LEN(username) BETWEEN 4 AND 50 AND username NOT LIKE N'%[^A-Za-z0-9_.-]%'),
        CONSTRAINT CK_poi_owner_registrations_phone CHECK
            (LEN(phone) = 10 AND phone LIKE N'0%' AND phone NOT LIKE N'%[^0-9]%'),
        CONSTRAINT CK_poi_owner_registrations_email CHECK (email LIKE N'%_@gmail.com'),
        CONSTRAINT FK_poi_owner_registrations_reviewer FOREIGN KEY (reviewed_by_username)
            REFERENCES dbo.people(username)
    );

    CREATE UNIQUE INDEX UX_poi_owner_registrations_pending_username
        ON dbo.poi_owner_registrations(username) WHERE reviewed_at IS NULL;
    CREATE UNIQUE INDEX UX_poi_owner_registrations_pending_email
        ON dbo.poi_owner_registrations(email) WHERE reviewed_at IS NULL;
    CREATE UNIQUE INDEX UX_poi_owner_registrations_pending_phone
        ON dbo.poi_owner_registrations(phone) WHERE reviewed_at IS NULL;
    CREATE INDEX IX_poi_owner_registrations_status_created
        ON dbo.poi_owner_registrations(reviewed_at, created_at DESC);
END;
GO

/* ================================================================
   3. POINTS OF INTEREST (ERD pois)
   ================================================================ */
IF OBJECT_ID(N'dbo.pois', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.pois
    (
        id NVARCHAR(10) NOT NULL,
        owner_id INT NOT NULL,
        name NVARCHAR(200) NOT NULL,
        description NVARCHAR(MAX) NOT NULL,
        address NVARCHAR(500) NOT NULL,
        latitude DECIMAL(10,7) NOT NULL,
        longitude DECIMAL(10,7) NOT NULL,
        trigger_radius_meters DECIMAL(6,2) NOT NULL CONSTRAINT DF_pois_radius DEFAULT (2),
        is_active BIT NOT NULL CONSTRAINT DF_pois_is_active DEFAULT (1),
        created_at DATETIME2 NOT NULL CONSTRAINT DF_pois_created_at DEFAULT (SYSUTCDATETIME()),
        updated_at DATETIME2 NULL,

        CONSTRAINT PK_pois PRIMARY KEY (id),
        CONSTRAINT CK_pois_id_not_blank CHECK (LEN(LTRIM(RTRIM(id))) > 0),
        CONSTRAINT CK_pois_latitude CHECK (latitude BETWEEN -90 AND 90),
        CONSTRAINT CK_pois_longitude CHECK (longitude BETWEEN -180 AND 180),
        CONSTRAINT CK_pois_radius CHECK (trigger_radius_meters BETWEEN 0.5 AND 100),
        CONSTRAINT FK_pois_owner FOREIGN KEY (owner_id) REFERENCES dbo.people(id)
    );
END;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.pois') AND name = N'IX_pois_owner_active')
    CREATE INDEX IX_pois_owner_active ON dbo.pois(owner_id, is_active);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.pois') AND name = N'IX_pois_active_location')
    CREATE INDEX IX_pois_active_location ON dbo.pois(is_active, latitude, longitude);
GO

/* A foreign key cannot enforce the account role, so retain a DB safeguard. */
CREATE OR ALTER TRIGGER dbo.TR_pois_owner_must_be_shop_owner
ON dbo.pois
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS
    (
        SELECT 1
        FROM inserted AS i
        INNER JOIN dbo.people AS p ON p.id = i.owner_id
        WHERE p.role <> N'SHOP_OWNER'
    )
    BEGIN
        ;THROW 51001, N'owner_id của POI phải thuộc tài khoản SHOP_OWNER.', 1;
    END;
END;
GO

CREATE OR ALTER TRIGGER dbo.TR_shop_owner_creator_must_be_system_admin
ON dbo.people
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS
    (
        SELECT 1
        FROM inserted AS owner_account
        LEFT JOIN dbo.people AS creator ON creator.id = owner_account.created_by_person_id
        WHERE owner_account.role = N'SHOP_OWNER'
          AND (owner_account.created_by_person_id IS NULL OR creator.role <> N'SYSTEM_ADMIN')
    )
    BEGIN
        ;THROW 51002, N'Tài khoản SHOP_OWNER phải được tạo bởi SYSTEM_ADMIN.', 1;
    END;
END;
GO

/* ================================================================
   4. LANGUAGES AND TRANSLATIONS (ERD translations)
   ================================================================ */
IF OBJECT_ID(N'dbo.languages', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.languages
    (
        language_code NVARCHAR(10) NOT NULL,
        language_name NVARCHAR(100) NOT NULL,
        is_active BIT NOT NULL CONSTRAINT DF_languages_is_active DEFAULT (1),
        CONSTRAINT PK_languages PRIMARY KEY (language_code),
        CONSTRAINT UQ_languages_name UNIQUE (language_name)
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.languages WHERE language_code = N'vi')
    INSERT dbo.languages(language_code, language_name) VALUES (N'vi', N'Tiếng Việt');
IF NOT EXISTS (SELECT 1 FROM dbo.languages WHERE language_code = N'en')
    INSERT dbo.languages(language_code, language_name) VALUES (N'en', N'English');
IF NOT EXISTS (SELECT 1 FROM dbo.languages WHERE language_code = N'fr')
    INSERT dbo.languages(language_code, language_name) VALUES (N'fr', N'Français');
IF NOT EXISTS (SELECT 1 FROM dbo.languages WHERE language_code = N'zh')
    INSERT dbo.languages(language_code, language_name) VALUES (N'zh', N'中文');
IF NOT EXISTS (SELECT 1 FROM dbo.languages WHERE language_code = N'ko')
    INSERT dbo.languages(language_code, language_name) VALUES (N'ko', N'한국어');
GO

IF OBJECT_ID(N'dbo.translations', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.translations
    (
        id INT IDENTITY(1,1) NOT NULL,
        poi_id NVARCHAR(10) NOT NULL,
        language_code NVARCHAR(10) NOT NULL,
        title NVARCHAR(200) NOT NULL,
        narration_text NVARCHAR(MAX) NOT NULL,
        audio_url NVARCHAR(1000) NULL,
        is_machine_generated BIT NOT NULL CONSTRAINT DF_translations_machine_generated DEFAULT (1),
        is_active BIT NOT NULL CONSTRAINT DF_translations_is_active DEFAULT (1),
        created_at DATETIME2 NOT NULL CONSTRAINT DF_translations_created_at DEFAULT (SYSUTCDATETIME()),
        updated_at DATETIME2 NULL,

        CONSTRAINT PK_translations PRIMARY KEY (id),
        CONSTRAINT UQ_translations_poi_language UNIQUE (poi_id, language_code),
        CONSTRAINT FK_translations_poi FOREIGN KEY (poi_id) REFERENCES dbo.pois(id),
        CONSTRAINT FK_translations_language FOREIGN KEY (language_code) REFERENCES dbo.languages(language_code)
    );
END;
GO

/* Remove the earlier rule that made machine-generation status depend only
   on language_code; that dependency is not in 3NF. */
IF EXISTS
(
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_translations_generation_source'
      AND parent_object_id = OBJECT_ID(N'dbo.translations')
)
    ALTER TABLE dbo.translations DROP CONSTRAINT CK_translations_generation_source;
GO

/* Add the language FK when this file is applied to an earlier V2 database. */
IF NOT EXISTS
(
    SELECT 1 FROM sys.foreign_keys
    WHERE name = N'FK_translations_language'
      AND parent_object_id = OBJECT_ID(N'dbo.translations')
)
BEGIN
    ALTER TABLE dbo.translations WITH CHECK
        ADD CONSTRAINT FK_translations_language
        FOREIGN KEY (language_code) REFERENCES dbo.languages(language_code);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.translations') AND name = N'IX_translations_poi_active')
    CREATE INDEX IX_translations_poi_active ON dbo.translations(poi_id, is_active, language_code);
GO

/* ================================================================
   5. CONTENT SUBMISSIONS AND REVIEW AUDIT (ERD poi_submission/audit_log)
   Keep POI and translation review references separate to avoid repeating
   the POI key through a translation row.
   ================================================================ */
IF OBJECT_ID(N'dbo.poi_submission', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.poi_submission
    (
        id BIGINT IDENTITY(1,1) NOT NULL,
        poi_id NVARCHAR(10) NOT NULL,
        submitted_by_person_id INT NOT NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_poi_submission_created_at DEFAULT (SYSUTCDATETIME()),
        status NVARCHAR(10) NOT NULL CONSTRAINT DF_poi_submission_status DEFAULT (N'PENDING'),
        reviewed_at DATETIME2 NULL,
        reviewed_by_person_id INT NULL,
        CONSTRAINT PK_poi_submission PRIMARY KEY (id),
        CONSTRAINT FK_poi_submission_poi FOREIGN KEY (poi_id) REFERENCES dbo.pois(id),
        CONSTRAINT FK_poi_submission_submitter FOREIGN KEY (submitted_by_person_id) REFERENCES dbo.people(id),
        CONSTRAINT FK_poi_submission_reviewer FOREIGN KEY (reviewed_by_person_id) REFERENCES dbo.people(id),
        CONSTRAINT CK_poi_submission_status CHECK (status IN (N'PENDING', N'APPROVED', N'REJECTED')),
        CONSTRAINT CK_poi_submission_review CHECK
        (
            (status = N'PENDING' AND reviewed_at IS NULL AND reviewed_by_person_id IS NULL)
            OR (status <> N'PENDING' AND reviewed_at IS NOT NULL AND reviewed_by_person_id IS NOT NULL)
        )
    );
    CREATE INDEX IX_poi_submission_status_created ON dbo.poi_submission(status, created_at DESC);
END;
GO

IF OBJECT_ID(N'dbo.translation_submission', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.translation_submission
    (
        id BIGINT IDENTITY(1,1) NOT NULL,
        translation_id INT NOT NULL,
        submitted_by_person_id INT NOT NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_translation_submission_created_at DEFAULT (SYSUTCDATETIME()),
        status NVARCHAR(10) NOT NULL CONSTRAINT DF_translation_submission_status DEFAULT (N'PENDING'),
        reviewed_at DATETIME2 NULL,
        reviewed_by_person_id INT NULL,
        CONSTRAINT PK_translation_submission PRIMARY KEY (id),
        CONSTRAINT FK_translation_submission_translation FOREIGN KEY (translation_id) REFERENCES dbo.translations(id),
        CONSTRAINT FK_translation_submission_submitter FOREIGN KEY (submitted_by_person_id) REFERENCES dbo.people(id),
        CONSTRAINT FK_translation_submission_reviewer FOREIGN KEY (reviewed_by_person_id) REFERENCES dbo.people(id),
        CONSTRAINT CK_translation_submission_status CHECK (status IN (N'PENDING', N'APPROVED', N'REJECTED')),
        CONSTRAINT CK_translation_submission_review CHECK
        (
            (status = N'PENDING' AND reviewed_at IS NULL AND reviewed_by_person_id IS NULL)
            OR (status <> N'PENDING' AND reviewed_at IS NOT NULL AND reviewed_by_person_id IS NOT NULL)
        )
    );
    CREATE INDEX IX_translation_submission_status_created ON dbo.translation_submission(status, created_at DESC);
END;
GO

IF OBJECT_ID(N'dbo.audit_log', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_log
    (
        id BIGINT IDENTITY(1,1) NOT NULL,
        poi_submission_id BIGINT NULL,
        translation_submission_id BIGINT NULL,
        actor_person_id INT NOT NULL,
        action NVARCHAR(20) NOT NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_audit_log_created_at DEFAULT (SYSUTCDATETIME()),
        admin_note NVARCHAR(2000) NULL,
        CONSTRAINT PK_audit_log PRIMARY KEY (id),
        CONSTRAINT FK_audit_log_poi_submission FOREIGN KEY (poi_submission_id) REFERENCES dbo.poi_submission(id),
        CONSTRAINT FK_audit_log_translation_submission FOREIGN KEY (translation_submission_id) REFERENCES dbo.translation_submission(id),
        CONSTRAINT FK_audit_log_actor FOREIGN KEY (actor_person_id) REFERENCES dbo.people(id),
        CONSTRAINT CK_audit_log_one_submission CHECK
        (
            (poi_submission_id IS NOT NULL AND translation_submission_id IS NULL)
            OR (poi_submission_id IS NULL AND translation_submission_id IS NOT NULL)
        ),
        CONSTRAINT CK_audit_log_action CHECK (action IN (N'SUBMITTED', N'APPROVED', N'REJECTED', N'UPDATED'))
    );
    CREATE INDEX IX_audit_log_poi_submission ON dbo.audit_log(poi_submission_id, created_at DESC) WHERE poi_submission_id IS NOT NULL;
    CREATE INDEX IX_audit_log_translation_submission ON dbo.audit_log(translation_submission_id, created_at DESC) WHERE translation_submission_id IS NOT NULL;
END;
GO

/* ================================================================
   6. OWNER NOTIFICATIONS (ERD owner_notifications)
   ================================================================ */
/* Review requests store their typed content separately from the live POI
   and translations. This keeps pending edits out of public data until approval. */
IF OBJECT_ID(N'dbo.content_change_requests', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.content_change_requests
    (
        id BIGINT IDENTITY(1,1) NOT NULL,
        request_type NVARCHAR(20) NOT NULL,
        action NVARCHAR(10) NOT NULL,
        submitted_by_person_id INT NOT NULL,
        status NVARCHAR(12) NOT NULL CONSTRAINT DF_content_change_requests_status DEFAULT (N'PENDING'),
        created_at DATETIME2 NOT NULL CONSTRAINT DF_content_change_requests_created_at DEFAULT (SYSUTCDATETIME()),
        processing_at DATETIME2 NULL,
        reviewed_at DATETIME2 NULL,
        reviewed_by_person_id INT NULL,
        admin_note NVARCHAR(2000) NULL,
        CONSTRAINT PK_content_change_requests PRIMARY KEY (id),
        CONSTRAINT FK_content_change_requests_submitter FOREIGN KEY (submitted_by_person_id) REFERENCES dbo.people(id),
        CONSTRAINT FK_content_change_requests_reviewer FOREIGN KEY (reviewed_by_person_id) REFERENCES dbo.people(id),
        CONSTRAINT CK_content_change_requests_type CHECK (request_type IN (N'POI', N'TRANSLATION')),
        CONSTRAINT CK_content_change_requests_action CHECK (action IN (N'CREATE', N'UPDATE')),
        CONSTRAINT CK_content_change_requests_status CHECK (status IN (N'PENDING', N'PROCESSING', N'APPROVED', N'REJECTED')),
        CONSTRAINT CK_content_change_requests_review CHECK
        (
            (status = N'PENDING' AND processing_at IS NULL AND reviewed_at IS NULL AND reviewed_by_person_id IS NULL)
            OR (status = N'PROCESSING' AND processing_at IS NOT NULL AND reviewed_at IS NULL AND reviewed_by_person_id IS NULL)
            OR (status IN (N'APPROVED', N'REJECTED') AND processing_at IS NULL AND reviewed_at IS NOT NULL AND reviewed_by_person_id IS NOT NULL AND admin_note IS NOT NULL)
        )
    );
    CREATE INDEX IX_content_change_requests_type_status_created
        ON dbo.content_change_requests(request_type, status, created_at DESC);
    CREATE INDEX IX_content_change_requests_submitter_created
        ON dbo.content_change_requests(submitted_by_person_id, created_at DESC);
END;
GO

IF OBJECT_ID(N'dbo.poi_change_request_details', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.poi_change_request_details
    (
        request_id BIGINT NOT NULL,
        requested_poi_id NVARCHAR(10) NOT NULL,
        name NVARCHAR(200) NOT NULL,
        description NVARCHAR(MAX) NOT NULL,
        address NVARCHAR(500) NOT NULL,
        latitude DECIMAL(10,7) NOT NULL,
        longitude DECIMAL(10,7) NOT NULL,
        trigger_radius_meters DECIMAL(6,2) NOT NULL,
        previous_name NVARCHAR(200) NULL,
        previous_description NVARCHAR(MAX) NULL,
        previous_address NVARCHAR(500) NULL,
        previous_latitude DECIMAL(10,7) NULL,
        previous_longitude DECIMAL(10,7) NULL,
        previous_trigger_radius_meters DECIMAL(6,2) NULL,
        CONSTRAINT PK_poi_change_request_details PRIMARY KEY (request_id),
        CONSTRAINT FK_poi_change_request_details_request FOREIGN KEY (request_id) REFERENCES dbo.content_change_requests(id) ON DELETE CASCADE,
        CONSTRAINT CK_poi_change_request_details_latitude CHECK (latitude BETWEEN -90 AND 90),
        CONSTRAINT CK_poi_change_request_details_longitude CHECK (longitude BETWEEN -180 AND 180),
        CONSTRAINT CK_poi_change_request_details_radius CHECK (trigger_radius_meters BETWEEN 0.5 AND 100)
    );
END;
GO

IF OBJECT_ID(N'dbo.translation_change_request_details', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.translation_change_request_details
    (
        request_id BIGINT NOT NULL,
        poi_id NVARCHAR(10) NOT NULL,
        title NVARCHAR(200) NOT NULL,
        narration_text NVARCHAR(MAX) NOT NULL,
        previous_title NVARCHAR(200) NULL,
        previous_narration_text NVARCHAR(MAX) NULL,
        CONSTRAINT PK_translation_change_request_details PRIMARY KEY (request_id),
        CONSTRAINT FK_translation_change_request_details_request FOREIGN KEY (request_id) REFERENCES dbo.content_change_requests(id) ON DELETE CASCADE,
        CONSTRAINT FK_translation_change_request_details_poi FOREIGN KEY (poi_id) REFERENCES dbo.pois(id)
    );
END;
GO

IF OBJECT_ID(N'dbo.owner_notifications', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.owner_notifications
    (
        id BIGINT IDENTITY(1,1) NOT NULL,
        owner_person_id INT NOT NULL,
        notification_type NVARCHAR(30) NOT NULL,
        message NVARCHAR(MAX) NOT NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_owner_notifications_created_at DEFAULT (SYSUTCDATETIME()),
        is_read BIT NOT NULL CONSTRAINT DF_owner_notifications_is_read DEFAULT (0),
        CONSTRAINT PK_owner_notifications PRIMARY KEY (id),
        CONSTRAINT FK_owner_notifications_owner FOREIGN KEY (owner_person_id) REFERENCES dbo.people(id),
        CONSTRAINT CK_owner_notifications_type CHECK (notification_type IN (N'REGISTRATION', N'POI_REVIEW', N'TRANSLATION_REVIEW', N'SYSTEM'))
    );
    CREATE INDEX IX_owner_notifications_owner_unread ON dbo.owner_notifications(owner_person_id, is_read, created_at DESC);
END;
GO

/* ================================================================
   7. PAYMENT TRANSACTIONS
   Anonymous sessions are represented by a UUID; no personal account is
   required. A payment order and provider transaction are unique identifiers.
   ================================================================ */
IF OBJECT_ID(N'dbo.payment_transactions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.payment_transactions
    (
        id BIGINT IDENTITY(1,1) NOT NULL,
        order_id VARCHAR(50) NOT NULL,
        guest_session_id UNIQUEIDENTIFIER NOT NULL,
        amount BIGINT NOT NULL,
        currency CHAR(3) NOT NULL CONSTRAINT DF_payment_currency DEFAULT ('VND'),
        status VARCHAR(20) NOT NULL CONSTRAINT DF_payment_status DEFAULT ('PENDING'),
        momo_transaction_id VARCHAR(100) NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_payment_created_at DEFAULT (SYSUTCDATETIME()),
        paid_at DATETIME2 NULL,
        expires_at DATETIME2 NOT NULL,
        CONSTRAINT PK_payment_transactions PRIMARY KEY (id),
        CONSTRAINT UQ_payment_order_id UNIQUE (order_id),
        CONSTRAINT CK_payment_amount CHECK (amount > 0),
        CONSTRAINT CK_payment_status CHECK (status IN ('PENDING', 'PAID', 'FAILED', 'CANCELLED', 'EXPIRED')),
        CONSTRAINT CK_payment_paid_at CHECK ((status = 'PAID' AND paid_at IS NOT NULL) OR (status <> 'PAID' AND paid_at IS NULL)),
        CONSTRAINT CK_payment_expiry CHECK (expires_at > created_at)
    );
    CREATE UNIQUE INDEX UX_payment_momo_transaction
        ON dbo.payment_transactions(momo_transaction_id) WHERE momo_transaction_id IS NOT NULL;
    CREATE INDEX IX_payment_session_created
        ON dbo.payment_transactions(guest_session_id, created_at DESC);
END;
GO

/* ================================================================
   8. INTEGRITY TRIGGERS FOR ROLE-SPECIFIC RELATIONSHIPS
   ================================================================ */
CREATE OR ALTER TRIGGER dbo.TR_poi_submission_roles
ON dbo.poi_submission
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS
    (
        SELECT 1 FROM inserted AS s
        INNER JOIN dbo.people AS owner_account ON owner_account.id = s.submitted_by_person_id
        WHERE owner_account.role <> N'SHOP_OWNER'
    )
    BEGIN
        ;THROW 51003, N'Người gửi phiếu POI phải là SHOP_OWNER.', 1;
    END;

    IF EXISTS
    (
        SELECT 1 FROM inserted AS s
        INNER JOIN dbo.people AS reviewer ON reviewer.id = s.reviewed_by_person_id
        WHERE reviewer.role <> N'SYSTEM_ADMIN'
    )
    BEGIN
        ;THROW 51004, N'Người kiểm duyệt POI phải là SYSTEM_ADMIN.', 1;
    END;
END;
GO

CREATE OR ALTER TRIGGER dbo.TR_translation_submission_roles
ON dbo.translation_submission
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS
    (
        SELECT 1 FROM inserted AS s
        INNER JOIN dbo.people AS owner_account ON owner_account.id = s.submitted_by_person_id
        WHERE owner_account.role <> N'SHOP_OWNER'
    )
    BEGIN
        ;THROW 51005, N'Người gửi phiếu bản dịch phải là SHOP_OWNER.', 1;
    END;

    IF EXISTS
    (
        SELECT 1 FROM inserted AS s
        INNER JOIN dbo.people AS reviewer ON reviewer.id = s.reviewed_by_person_id
        WHERE reviewer.role <> N'SYSTEM_ADMIN'
    )
    BEGIN
        ;THROW 51006, N'Người kiểm duyệt bản dịch phải là SYSTEM_ADMIN.', 1;
    END;
END;
GO

CREATE OR ALTER TRIGGER dbo.TR_owner_notifications_role
ON dbo.owner_notifications
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS
    (
        SELECT 1 FROM inserted AS n
        INNER JOIN dbo.people AS owner_account ON owner_account.id = n.owner_person_id
        WHERE owner_account.role <> N'SHOP_OWNER'
    )
    BEGIN
        ;THROW 51007, N'Thông báo chủ quán phải gắn với tài khoản SHOP_OWNER.', 1;
    END;
END;
GO

/* ================================================================
   9. SCHEMA CHECK
   ================================================================ */
SELECT s.name AS schema_name, t.name AS table_name
FROM sys.tables AS t
INNER JOIN sys.schemas AS s ON s.schema_id = t.schema_id
WHERE s.name = N'dbo'
ORDER BY t.name;
GO
