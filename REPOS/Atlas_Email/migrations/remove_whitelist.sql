-- Migration: Remove whitelist functionality and clean up historical data
-- Date: 2025-07-04
-- Purpose: Eliminate all whitelist-related data and prevent future occurrences

-- Step 1: Update historical "Whitelisted" entries to "Legitimate Marketing"
-- These are transactional emails from legitimate services that should be preserved
UPDATE processed_emails_bulletproof 
SET category = 'Legitimate Marketing',
    reason = 'Transactional email from legitimate service (migrated from whitelist)'
WHERE category = 'Whitelisted';

-- Step 2: Drop the is_whitelisted column from domains table
-- First check if column exists (SQLite doesn't support IF EXISTS for ALTER TABLE)
-- This requires a table recreation in SQLite
CREATE TABLE domains_new (
    domain VARCHAR(255) UNIQUE,
    risk_score FLOAT,
    ml_confidence_scores TEXT, -- JSON array
    total_occurrences INTEGER DEFAULT 1,
    action_taken TEXT,
    validation_results TEXT, -- JSON
    associated_categories TEXT, -- JSON array
    last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Copy data from old table (excluding is_whitelisted)
INSERT INTO domains_new (
    domain, risk_score, ml_confidence_scores, total_occurrences,
    action_taken, validation_results, associated_categories,
    last_seen, first_seen, created_at, updated_at
)
SELECT 
    domain, risk_score, ml_confidence_scores, total_occurrences,
    action_taken, validation_results, associated_categories,
    last_seen, first_seen, created_at, updated_at
FROM domains;

-- Drop old table and rename new one
DROP TABLE domains;
ALTER TABLE domains_new RENAME TO domains;

-- Step 3: Add CHECK constraint to prevent "Whitelisted" category
-- SQLite doesn't support adding constraints to existing tables, 
-- so we need to recreate the processed_emails_bulletproof table
-- For now, we'll document this as a future enhancement

-- Step 4: Clean up any whitelist-related configuration
DELETE FROM configurations 
WHERE config_key LIKE '%whitelist%';

-- Step 5: Update schema version
UPDATE schema_version 
SET version = 6, 
    updated_at = CURRENT_TIMESTAMP,
    description = 'Removed whitelist functionality'
WHERE version = (SELECT MAX(version) FROM schema_version);

-- Insert new version record if table exists
INSERT OR IGNORE INTO schema_version (version, updated_at, description)
VALUES (6, CURRENT_TIMESTAMP, 'Removed whitelist functionality');

-- Verification queries (run these manually to confirm migration success)
-- SELECT COUNT(*) as whitelist_count FROM processed_emails_bulletproof WHERE category = 'Whitelisted';
-- SELECT * FROM domains LIMIT 1; -- Verify is_whitelisted column is gone