/* Idempotent migration for moderated POI and translation changes. */
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
        CONSTRAINT PK_translation_change_request_details PRIMARY KEY (request_id),
        CONSTRAINT FK_translation_change_request_details_request FOREIGN KEY (request_id) REFERENCES dbo.content_change_requests(id) ON DELETE CASCADE,
        CONSTRAINT FK_translation_change_request_details_poi FOREIGN KEY (poi_id) REFERENCES dbo.pois(id)
    );
END;
GO
