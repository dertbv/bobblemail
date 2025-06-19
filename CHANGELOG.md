# Changelog

All notable changes to the Email Filtering System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

2025-06-15  fix: Nextdoor domain protection failure – Community Email category, 621 emails preserved

## [2025-06-15] - Revolutionary Two-Factor Email Validation
### Added
- Universal business prefix detection system with ~100 legitimate email patterns (marketing@, offers@, support@, etc.)
- Two-factor email validator combining business prefix validation + domain legitimacy checks
- Smart content-based routing system for failed validations to appropriate spam categories
- Enhanced gibberish domain detection for random alphanumeric domains
- Integrated two-factor system into main classification pipeline with seamless fallback

### Fixed
- Classification priority logic ensuring Phishing > specific spam categories > Brand Impersonation hierarchy
- Brand impersonation over-detection issues with legitimate promotional emails
- Gibberish domains bypassing brand impersonation filters

### Changed
- Promotional email classification now uses revolutionary two-factor authentication approach
- Failed validations route to specific spam categories instead of generic Brand Impersonation

## [2025-06-14] - Promotional Email Deletion Fix
### Fixed
- Promotional email deletion bypass for domain validation to enable proper spam deletion from legitimate retailers
- Domain validation bypass logic to skip preservation for promotional/marketing content
- Extended bypass to include Health & Medical Spam, Payment Scam, Phishing, Brand Impersonation categories

### Added
- `loft.com` to legitimate domains list in spam_classifier.py
- Enhanced promotional keywords database with `% off`, `price drop`, `re-order` patterns

### Changed
- email_processor.py now treats "Promotional Email" as spam category for deletion

## [2025-06-12] - Alternative Ranking System
### Added
- Revolutionary iterative classification learning with ranked alternatives
- Intelligent alternative ranking with multi-factor scoring (up to 8 ranked alternatives per email)
- Smart exclusion logic tracking previous attempts to prevent loops
- Multi-source intelligence combining keyword matching, domain analysis, brand detection, ML confidence

### Fixed
- Protection patterns integration - security vulnerability preventing user-protected email deletion
- Brand impersonation enhancement reducing false positives from political figures and financial terms
- Phishing detection refinement with 34 new keywords across 6 attack vectors
- Spam classification accuracy with 18 missing detection keywords

## [2025-06-11] - Major Codebase Cleanup
### Removed
- 33 obsolete files (32% reduction: 104 → 71 files)
- 3 backup files, 9 debug scripts, 11 specific email test files
- 2 obsolete classifiers, 6 one-time analysis files, 2 HTML test files

### Added
- Category validation page completely rebuilt with clean, simple architecture
- Working JavaScript with reliable email loading and thumbs up/down feedback
- UTF-8 decoding for proper sender address and subject handling

### Changed
- Replaced complex 730+ line implementation with 200 lines of clean code
- Improved codebase maintainability and navigation

## [2025-06-10] - ML Ensemble & Phishing Breakthrough
### Added
- Advanced ML ensemble system with Random Forest (40%) + Naive Bayes (30%) + Keyword Matching (30%)
- Enterprise-grade phishing detection with 90 emails migrated
- New Phishing category with HIGHEST priority classification
- 45+ phishing keywords across 6 attack vectors with 80-95% confidence
- Pattern recognition for prize scams, credential theft, verification scams

### Changed
- Database expanded from 1,511 → 2,716 records
- Perfect deduplication maintained with zero remaining duplicates
- Optimized queries with keyword database cleanup

### Fixed
- Database connection leaks and file descriptor exhaustion
- Two-pass architecture completely removed (problematic dual-classifier system)
- 28% codebase reduction focused on active functionality only

## Project Status
- **System Status**: 🚀 **REVOLUTIONARY** with breakthrough two-factor email validation  
- **Next Milestone**: Universal subdomain complexity detection and global spam pattern enhancement  
- **Architecture Health**: ✅ Revolutionary classification system deployed and operational