/* Preserve the submitted before/after values for update requests. */
IF COL_LENGTH(N'dbo.poi_change_request_details', N'previous_name') IS NULL
    ALTER TABLE dbo.poi_change_request_details ADD previous_name NVARCHAR(200) NULL;
GO
IF COL_LENGTH(N'dbo.poi_change_request_details', N'previous_description') IS NULL
    ALTER TABLE dbo.poi_change_request_details ADD previous_description NVARCHAR(MAX) NULL;
GO
IF COL_LENGTH(N'dbo.poi_change_request_details', N'previous_address') IS NULL
    ALTER TABLE dbo.poi_change_request_details ADD previous_address NVARCHAR(500) NULL;
GO
IF COL_LENGTH(N'dbo.poi_change_request_details', N'previous_latitude') IS NULL
    ALTER TABLE dbo.poi_change_request_details ADD previous_latitude DECIMAL(10,7) NULL;
GO
IF COL_LENGTH(N'dbo.poi_change_request_details', N'previous_longitude') IS NULL
    ALTER TABLE dbo.poi_change_request_details ADD previous_longitude DECIMAL(10,7) NULL;
GO
IF COL_LENGTH(N'dbo.poi_change_request_details', N'previous_trigger_radius_meters') IS NULL
    ALTER TABLE dbo.poi_change_request_details ADD previous_trigger_radius_meters DECIMAL(6,2) NULL;
GO
