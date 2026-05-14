CREATE TABLE IF NOT EXISTS extracted_bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT,
    vendor_name TEXT,
    total REAL,
    raw_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS correction_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id INTEGER,
    field_name TEXT,
    original_value TEXT,
    corrected_value TEXT,
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS migration_history (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dashboard_projection_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bucket TEXT NOT NULL,
    stable_key TEXT NOT NULL,
    record_type TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bucket, record_type, stable_key)
);

CREATE INDEX IF NOT EXISTS idx_dashboard_projection_bucket_order
ON dashboard_projection_records(bucket, record_type, sort_order, stable_key);
