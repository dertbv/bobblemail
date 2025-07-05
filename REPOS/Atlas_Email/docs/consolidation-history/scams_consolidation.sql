-- SCAMS CATEGORY CONSOLIDATION
-- Generated: 2025-07-05
-- Purpose: Consolidate true fraud/scam emails into Scams category

-- Current state:
-- Scams category: 282 emails
-- Payment Scam: 10 emails (mostly not actual scams)
-- Legal & Compensation Scams: 6 emails (mostly not actual scams)
-- Emails with scam subcategories in other categories: 890

BEGIN TRANSACTION;

-- 1. Move emails with clear scam subcategories from Dangerous to Scams
-- Prize & Lottery Scams: 534 emails
UPDATE processed_emails_bulletproof
SET category = 'Scams',
    primary_category = 'Scams'
WHERE category = 'Dangerous' 
AND subcategory = 'Prize & Lottery Scams';

-- Tech Support Scams: 37 emails
UPDATE processed_emails_bulletproof
SET category = 'Scams',
    primary_category = 'Scams'
WHERE category = 'Dangerous' 
AND subcategory = 'Tech Support Scams';

-- Investment Fraud: 2 emails
UPDATE processed_emails_bulletproof
SET category = 'Scams',
    primary_category = 'Scams'
WHERE category = 'Dangerous' 
AND subcategory = 'Investment Fraud';

-- Cryptocurrency Scams: 2 emails
UPDATE processed_emails_bulletproof
SET category = 'Scams',
    primary_category = 'Scams'
WHERE category = 'Dangerous' 
AND subcategory = 'Cryptocurrency Scams';

-- 2. Move emails with clear scam subcategories from Commercial Spam to Scams
-- Investment Fraud: 156 emails
UPDATE processed_emails_bulletproof
SET category = 'Scams',
    primary_category = 'Scams'
WHERE category = 'Commercial Spam' 
AND subcategory = 'Investment Fraud';

-- Cryptocurrency Scams: 151 emails
UPDATE processed_emails_bulletproof
SET category = 'Scams',
    primary_category = 'Scams'
WHERE category = 'Commercial Spam' 
AND subcategory = 'Cryptocurrency Scams';

-- Job Scams: 14 emails
UPDATE processed_emails_bulletproof
SET category = 'Scams',
    primary_category = 'Scams'
WHERE category = 'Commercial Spam' 
AND subcategory = 'Job Scams';

-- Tech Support Scams: 4 emails
UPDATE processed_emails_bulletproof
SET category = 'Scams',
    primary_category = 'Scams'
WHERE category = 'Commercial Spam' 
AND subcategory = 'Tech Support Scams';

-- 3. Move emails with lottery/prize keywords from other categories
-- These need individual review, but strong indicators of scams
UPDATE processed_emails_bulletproof
SET category = 'Scams',
    primary_category = 'Scams',
    subcategory = CASE 
        WHEN subcategory IS NULL OR subcategory = '' THEN 'Prize & Lottery Scams'
        ELSE subcategory
    END
WHERE category NOT IN ('Scams', 'Legitimate Marketing')
AND (
    LOWER(subject) LIKE '%you have won%' OR
    LOWER(subject) LIKE '%lottery winner%' OR
    LOWER(subject) LIKE '%prize winner%' OR
    LOWER(subject) LIKE '%beneficiary%' OR
    LOWER(subject) LIKE '%inheritance%' OR
    (LOWER(subject) LIKE '%congratulations%' AND LOWER(subject) LIKE '%winner%')
);

-- 4. Note: Payment Scam and Legal & Compensation Scams categories
-- After review, these mostly contain legitimate marketing emails misclassified
-- Not moving these as they don't appear to be actual scams

COMMIT;

-- Summary of changes:
-- Dangerous → Scams: 575 emails (Prize & Lottery, Tech Support, Investment, Crypto scams)
-- Commercial Spam → Scams: 325 emails (Investment Fraud, Crypto, Job, Tech Support scams)
-- Additional keyword-based moves: ~100-200 emails (estimate)
-- Total consolidation: ~900-1100 emails