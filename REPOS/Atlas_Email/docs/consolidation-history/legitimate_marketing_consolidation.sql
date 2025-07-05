-- Legitimate Marketing Consolidation SQL
-- Date: 2025-07-05
-- Purpose: Consolidate legitimate marketing emails into the correct category

-- Current count: 1524 Legitimate Marketing emails

-- 1. Update Zappos emails (legitimate shoe retailer)
UPDATE processed_emails_bulletproof 
SET category = 'Legitimate Marketing', primary_category = 'Promotional Email'
WHERE (sender_domain LIKE '%zappos.com') 
AND category IN ('Commercial Spam', 'Scams', 'Dangerous');
-- Affects approximately 220 emails

-- 2. Update legitimate shipping company emails
UPDATE processed_emails_bulletproof 
SET category = 'Legitimate Marketing', primary_category = 'Transactional Email'
WHERE sender_domain IN ('fedex.com', 'message.fedex.com', 'ups.com')
AND category IN ('Commercial Spam', 'Scams', 'Dangerous');
-- Affects approximately 6 emails

-- 3. Update legitimate financial institution emails
UPDATE processed_emails_bulletproof 
SET category = 'Legitimate Marketing', primary_category = 'Financial Services'
WHERE (sender_domain LIKE '%chase.com' OR sender_domain LIKE '%capitalone.com')
AND category IN ('Commercial Spam', 'Scams', 'Dangerous');
-- Affects approximately 3 emails

-- 4. Update legitimate e-commerce emails
UPDATE processed_emails_bulletproof 
SET category = 'Legitimate Marketing', primary_category = 'Promotional Email'
WHERE sender_domain IN ('reply.ebay.com', 'ebay.com', 'service.paypal.com', 'emails.paypal.com', 'robinhood.com')
AND category IN ('Commercial Spam', 'Scams');
-- Affects approximately 19 emails

-- 5. Update misclassified Amazon emails (only legitimate ones)
UPDATE processed_emails_bulletproof 
SET category = 'Legitimate Marketing', primary_category = 'Promotional Email'
WHERE sender_domain = 'amazon.com'
AND category IN ('Commercial Spam', 'Scams');
-- Affects approximately 11 emails

-- 6. Update all Promotional Email category to Legitimate Marketing
UPDATE processed_emails_bulletproof 
SET category = 'Legitimate Marketing', primary_category = 'Promotional Email'
WHERE category = 'Promotional Email';
-- Affects approximately 80 emails

-- 7. Update legitimate retailers
UPDATE processed_emails_bulletproof 
SET category = 'Legitimate Marketing', primary_category = 'Promotional Email'
WHERE sender_domain IN ('mail.aliexpress.com', 'mg.homedepot.com', 'digital.costco.com', 'patreon.com')
AND category IN ('Commercial Spam', 'Promotional Email');
-- Affects approximately 18 emails

-- 8. Update The Spruce (legitimate home & garden website)
UPDATE processed_emails_bulletproof 
SET category = 'Legitimate Marketing', primary_category = 'Newsletter'
WHERE sender_domain = 'mail.thespruce.com'
AND category = 'Commercial Spam';
-- Affects approximately 50 emails

-- Note: Leaving financial newsletter domains in Commercial Spam as they appear to be investment scams
-- Total emails to be consolidated: approximately 407