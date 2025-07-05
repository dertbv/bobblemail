-- Performance Optimization Indexes Migration
-- Date: 2025-07-05
-- Purpose: Add indexes to improve query performance for Atlas_Email system

-- ============================================================================
-- BACKUP REMINDER: Always backup database before running migrations
-- sqlite3 mail_filter.db ".backup mail_filter_backup.db"
-- ============================================================================

-- Start transaction for atomic operation
BEGIN TRANSACTION;

-- ============================================================================
-- processed_emails_bulletproof table indexes
-- ============================================================================

-- Composite index for email lookup (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_processed_emails_uid_folder 
ON processed_emails_bulletproof(uid, folder_name);

-- Index for sender domain analysis
CREATE INDEX IF NOT EXISTS idx_processed_emails_sender_domain
ON processed_emails_bulletproof(sender_domain);

-- Index for date-based queries
CREATE INDEX IF NOT EXISTS idx_processed_emails_date
ON processed_emails_bulletproof(date_received);

-- Index for classification queries
CREATE INDEX IF NOT EXISTS idx_processed_emails_classification
ON processed_emails_bulletproof(result_4category, confidence);

-- Index for account-based queries
CREATE INDEX IF NOT EXISTS idx_processed_emails_account
ON processed_emails_bulletproof(account_id);

-- ============================================================================
-- domains table indexes
-- ============================================================================

-- Primary lookup index
CREATE INDEX IF NOT EXISTS idx_domains_domain
ON domains(domain);

-- Composite index for domain validation queries
CREATE INDEX IF NOT EXISTS idx_domains_domain_lastseen
ON domains(domain, last_seen);

-- Index for validation status queries
CREATE INDEX IF NOT EXISTS idx_domains_validation
ON domains(is_valid, domain_type);

-- ============================================================================
-- flags table indexes
-- ============================================================================

-- Composite index for flag lookups
CREATE INDEX IF NOT EXISTS idx_flags_uid_folder
ON flags(uid, folder_name);

-- Index for flag type queries
CREATE INDEX IF NOT EXISTS idx_flags_type_status
ON flags(flag_type, review_status);

-- Index for timestamp-based queries
CREATE INDEX IF NOT EXISTS idx_flags_timestamp
ON flags(flagged_at);

-- ============================================================================
-- analytics table indexes
-- ============================================================================

-- Index for analytics queries by category
CREATE INDEX IF NOT EXISTS idx_analytics_category_date
ON analytics(category, date);

-- Index for analytics aggregation
CREATE INDEX IF NOT EXISTS idx_analytics_date_category_type
ON analytics(date, category, type);

-- ============================================================================
-- geographic_intelligence table indexes
-- ============================================================================

-- Index for IP-based lookups
CREATE INDEX IF NOT EXISTS idx_geographic_ip
ON geographic_intelligence(sender_ip);

-- Index for country-based analysis
CREATE INDEX IF NOT EXISTS idx_geographic_country
ON geographic_intelligence(country_code);

-- Composite index for geographic risk queries
CREATE INDEX IF NOT EXISTS idx_geographic_risk
ON geographic_intelligence(risk_level, country_code);

-- ============================================================================
-- Create performance_metrics table for monitoring
-- ============================================================================

CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR(50) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    duration_ms REAL NOT NULL,
    count INTEGER DEFAULT 1,
    metadata TEXT,  -- JSON field for additional data
    
    -- Indexes for performance metrics queries
    INDEX idx_metrics_timestamp (timestamp),
    INDEX idx_metrics_category_operation (category, operation),
    INDEX idx_metrics_duration (duration_ms)
);

-- ============================================================================
-- Add index statistics view for monitoring
-- ============================================================================

CREATE VIEW IF NOT EXISTS index_statistics AS
SELECT 
    m.name as index_name,
    m.tbl_name as table_name,
    COUNT(*) as index_count
FROM sqlite_master m
WHERE m.type = 'index' 
  AND m.name NOT LIKE 'sqlite_%'
GROUP BY m.tbl_name, m.name
ORDER BY m.tbl_name, m.name;

-- ============================================================================
-- Analyze tables to update query planner statistics
-- ============================================================================

ANALYZE processed_emails_bulletproof;
ANALYZE domains;
ANALYZE flags;
ANALYZE analytics;
ANALYZE geographic_intelligence;

-- Commit transaction
COMMIT;

-- ============================================================================
-- Rollback script (save separately as rollback_performance_indexes.sql)
-- ============================================================================
/*
-- To rollback these changes, run:

BEGIN TRANSACTION;

-- Drop all created indexes
DROP INDEX IF EXISTS idx_processed_emails_uid_folder;
DROP INDEX IF EXISTS idx_processed_emails_sender_domain;
DROP INDEX IF EXISTS idx_processed_emails_date;
DROP INDEX IF EXISTS idx_processed_emails_classification;
DROP INDEX IF EXISTS idx_processed_emails_account;

DROP INDEX IF EXISTS idx_domains_domain;
DROP INDEX IF EXISTS idx_domains_domain_lastseen;
DROP INDEX IF EXISTS idx_domains_validation;

DROP INDEX IF EXISTS idx_flags_uid_folder;
DROP INDEX IF EXISTS idx_flags_type_status;
DROP INDEX IF EXISTS idx_flags_timestamp;

DROP INDEX IF EXISTS idx_analytics_category_date;
DROP INDEX IF EXISTS idx_analytics_date_category_type;

DROP INDEX IF EXISTS idx_geographic_ip;
DROP INDEX IF EXISTS idx_geographic_country;
DROP INDEX IF EXISTS idx_geographic_risk;

-- Drop performance metrics table
DROP TABLE IF EXISTS performance_metrics;

-- Drop statistics view
DROP VIEW IF EXISTS index_statistics;

COMMIT;
*/