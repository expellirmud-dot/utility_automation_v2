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
