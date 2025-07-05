-- Atlas Email Classification Correction Script
-- Created: 2025-07-05
-- Purpose: Fix misclassified emails currently labeled as "Commercial Spam"

-- First, let's create a backup table just in case
CREATE TABLE IF NOT EXISTS processed_emails_backup_20250105 AS 
SELECT * FROM processed_emails_bulletproof;

-- Test updates on small batch first (5 records each)
-- These will be commented out after testing

-- Test 1: Investment Fraud → Financial & Investment Spam
/*
UPDATE processed_emails_bulletproof 
SET category = 'Financial & Investment Spam',
    primary_category = 'Financial & Investment Spam'
WHERE category = 'Commercial Spam' 
  AND subcategory = 'Investment Fraud'
LIMIT 5;
*/

-- Full updates after testing

-- 1. Investment Fraud (156 emails) → Financial & Investment Spam
UPDATE processed_emails_bulletproof 
SET category = 'Financial & Investment Spam',
    primary_category = 'Financial & Investment Spam'
WHERE category = 'Commercial Spam' 
  AND subcategory = 'Investment Fraud';

-- 2. Cryptocurrency Scams (151 emails) → Financial & Investment Spam
UPDATE processed_emails_bulletproof 
SET category = 'Financial & Investment Spam',
    primary_category = 'Financial & Investment Spam'
WHERE category = 'Commercial Spam' 
  AND subcategory = 'Cryptocurrency Scams';

-- 3. Investment & Trading (143 emails) → Financial & Investment Spam
-- These appear to be fraudulent investment offers based on content
UPDATE processed_emails_bulletproof 
SET category = 'Financial & Investment Spam',
    primary_category = 'Financial & Investment Spam'
WHERE category = 'Commercial Spam' 
  AND subcategory = 'Investment & Trading';

-- 4. Political News Spam (462 emails) → Dangerous
-- These contain disinformation and conspiracy theories
UPDATE processed_emails_bulletproof 
SET category = 'Dangerous',
    primary_category = 'Dangerous'
WHERE category = 'Commercial Spam' 
  AND subcategory = 'Political News Spam';

-- 5. Political Content (37 emails) → Dangerous
-- Similar to above but less explicitly labeled
UPDATE processed_emails_bulletproof 
SET category = 'Dangerous',
    primary_category = 'Dangerous'
WHERE category = 'Commercial Spam' 
  AND subcategory = 'Political Content';

-- 6. Health & Pharma Spam (136 emails) → Health & Medical Spam
UPDATE processed_emails_bulletproof 
SET category = 'Health & Medical Spam',
    primary_category = 'Health & Medical Spam'
WHERE category = 'Commercial Spam' 
  AND subcategory = 'Health & Pharma Spam';

-- 7. Prize & Lottery Scams (64 emails) → Scams
UPDATE processed_emails_bulletproof 
SET category = 'Scams',
    primary_category = 'Scams'
WHERE category = 'Commercial Spam' 
  AND subcategory = 'Prize & Lottery Scams';

-- 8. Adult Content (135 emails) → Adult & Dating Spam
UPDATE processed_emails_bulletproof 
SET category = 'Adult & Dating Spam',
    primary_category = 'Adult & Dating Spam'
WHERE category = 'Commercial Spam' 
  AND subcategory = 'Adult Content';

-- Summary query to verify changes
SELECT 
    subcategory,
    category as new_category,
    COUNT(*) as count
FROM processed_emails_bulletproof
WHERE subcategory IN (
    'Investment Fraud', 
    'Cryptocurrency Scams', 
    'Investment & Trading',
    'Political News Spam', 
    'Political Content',
    'Health & Pharma Spam', 
    'Prize & Lottery Scams', 
    'Adult Content'
)
GROUP BY subcategory, category
ORDER BY subcategory, count DESC;