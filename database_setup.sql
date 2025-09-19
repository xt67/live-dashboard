-- Generic Data Dashboard Database Schema
-- This schema can adapt to any CSV/Excel file structure

-- Create database (run manually if needed)
-- CREATE DATABASE data_dashboard;

-- Main data table with flexible schema
CREATE TABLE IF NOT EXISTS dashboard_data (
    id SERIAL PRIMARY KEY,
    record_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(255),  -- Original filename/source
    record_data JSONB  -- Store all columns as JSON for maximum flexibility
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_dashboard_data_timestamp ON dashboard_data(record_timestamp);
CREATE INDEX IF NOT EXISTS idx_dashboard_data_source ON dashboard_data(data_source);
CREATE INDEX IF NOT EXISTS idx_dashboard_data_jsonb ON dashboard_data USING GIN(record_data);

-- Table to store column metadata for each data source
CREATE TABLE IF NOT EXISTS data_source_metadata (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(255) UNIQUE NOT NULL,
    column_info JSONB,  -- Store column names, types, and display preferences
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update the updated_at field
CREATE TRIGGER update_metadata_modtime 
    BEFORE UPDATE ON data_source_metadata 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- View to get the most recent data for dashboard display
CREATE OR REPLACE VIEW latest_dashboard_data AS
SELECT 
    id,
    record_timestamp,
    data_source,
    record_data
FROM dashboard_data
ORDER BY record_timestamp DESC
LIMIT 1000;

-- Function to get column statistics for a data source
CREATE OR REPLACE FUNCTION get_column_stats(source_name TEXT)
RETURNS TABLE(
    column_name TEXT,
    data_type TEXT,
    distinct_values BIGINT,
    null_count BIGINT,
    sample_values TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        keys.key AS column_name,
        CASE 
            WHEN jsonb_typeof(values.value) = 'number' THEN 'numeric'
            WHEN jsonb_typeof(values.value) = 'boolean' THEN 'boolean'
            ELSE 'text'
        END AS data_type,
        COUNT(DISTINCT values.value) AS distinct_values,
        COUNT(*) FILTER (WHERE values.value = 'null'::jsonb) AS null_count,
        ARRAY(
            SELECT DISTINCT values.value::text 
            FROM dashboard_data d2, jsonb_each(d2.record_data) AS vals(k, v)
            WHERE d2.data_source = source_name AND vals.k = keys.key
            LIMIT 5
        ) AS sample_values
    FROM dashboard_data d, 
         jsonb_object_keys(d.record_data) AS keys(key),
         jsonb_each(d.record_data) AS values(k, value)
    WHERE d.data_source = source_name 
          AND keys.key = values.k
    GROUP BY keys.key, jsonb_typeof(values.value);
END;
$$ LANGUAGE plpgsql;

-- Drop old sales-specific table if it exists (optional - uncomment if needed)
-- DROP TABLE IF EXISTS sales_data;