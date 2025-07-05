-- Commercial Spam Consolidation Script
-- Generated: 2025-07-05
-- Purpose: Consolidate various spam categories into Commercial Spam according to 4-category system

-- Initial state
SELECT 'Initial Commercial Spam count:' as description, COUNT(*) as count 
FROM processed_emails_bulletproof 
WHERE category = 'Commercial Spam';

-- Categories to consolidate counts
SELECT 'Categories to consolidate:' as description;
SELECT category, COUNT(*) as count 
FROM processed_emails_bulletproof 
WHERE category IN (
    'Marketing Spam',
    'Health & Medical Spam',
    'Adult & Dating Spam',
    'Gambling Spam',
    'Financial & Investment Spam',
    'Real Estate Spam',
    'Education/Training Spam',
    'Business Opportunity Spam'
)
GROUP BY category
ORDER BY count DESC;

-- Begin consolidation
BEGIN TRANSACTION;

-- Update Marketing Spam -> Commercial Spam
UPDATE processed_emails_bulletproof
SET category = 'Commercial Spam',
    primary_category = 'Commercial Spam',
    subcategory = CASE 
        WHEN subcategory IS NULL OR subcategory = '' THEN 'General Marketing'
        ELSE subcategory
    END
WHERE category = 'Marketing Spam';

-- Update Health & Medical Spam -> Commercial Spam
UPDATE processed_emails_bulletproof
SET category = 'Commercial Spam',
    primary_category = 'Commercial Spam',
    subcategory = CASE 
        WHEN subcategory IS NULL OR subcategory = '' THEN 'Health Products'
        ELSE subcategory
    END
WHERE category = 'Health & Medical Spam';

-- Update Adult & Dating Spam -> Commercial Spam
UPDATE processed_emails_bulletproof
SET category = 'Commercial Spam',
    primary_category = 'Commercial Spam',
    subcategory = CASE 
        WHEN subcategory IS NULL OR subcategory = '' THEN 'Adult & Dating'
        ELSE subcategory
    END
WHERE category = 'Adult & Dating Spam';

-- Update Gambling Spam -> Commercial Spam
UPDATE processed_emails_bulletproof
SET category = 'Commercial Spam',
    primary_category = 'Commercial Spam',
    subcategory = CASE 
        WHEN subcategory IS NULL OR subcategory = '' THEN 'Gambling & Casino'
        ELSE subcategory
    END
WHERE category = 'Gambling Spam';

-- Update Financial & Investment Spam -> Commercial Spam
-- Note: Only marketing-style financial spam, not actual scams
UPDATE processed_emails_bulletproof
SET category = 'Commercial Spam',
    primary_category = 'Commercial Spam',
    subcategory = CASE 
        WHEN subcategory IS NULL OR subcategory = '' THEN 'Financial Marketing'
        ELSE subcategory
    END
WHERE category = 'Financial & Investment Spam'
AND (
    subject LIKE '%crypto%' OR
    subject LIKE '%stock%' OR
    subject LIKE '%investment%' OR
    subject LIKE '%retire%' OR
    subject LIKE '%401k%' OR
    subject LIKE '%IRA%' OR
    subject LIKE '%bitcoin%' OR
    sender_email LIKE '%invest%' OR
    sender_email LIKE '%capital%' OR
    sender_email LIKE '%financial%' OR
    sender_email LIKE '%crypto%' OR
    sender_email LIKE '%stock%'
);

-- Update Real Estate Spam -> Commercial Spam
UPDATE processed_emails_bulletproof
SET category = 'Commercial Spam',
    primary_category = 'Commercial Spam',
    subcategory = CASE 
        WHEN subcategory IS NULL OR subcategory = '' THEN 'Real Estate'
        ELSE subcategory
    END
WHERE category = 'Real Estate Spam';

-- Update Education/Training Spam -> Commercial Spam
UPDATE processed_emails_bulletproof
SET category = 'Commercial Spam',
    primary_category = 'Commercial Spam',
    subcategory = CASE 
        WHEN subcategory IS NULL OR subcategory = '' THEN 'Education & Training'
        ELSE subcategory
    END
WHERE category = 'Education/Training Spam';

-- Update Business Opportunity Spam -> Commercial Spam
UPDATE processed_emails_bulletproof
SET category = 'Commercial Spam',
    primary_category = 'Commercial Spam',
    subcategory = CASE 
        WHEN subcategory IS NULL OR subcategory = '' THEN 'Business Opportunities'
        ELSE subcategory
    END
WHERE category = 'Business Opportunity Spam';

COMMIT;

-- Final state
SELECT 'Final Commercial Spam count:' as description, COUNT(*) as count 
FROM processed_emails_bulletproof 
WHERE category = 'Commercial Spam';

-- Verify consolidation
SELECT 'Remaining categories after consolidation:' as description;
SELECT category, COUNT(*) as count 
FROM processed_emails_bulletproof 
GROUP BY category
ORDER BY count DESC;