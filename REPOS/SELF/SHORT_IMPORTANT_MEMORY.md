# SHORT IMPORTANT MEMORY

## Information Entropy Note
This file should capture **non-obvious, surprising information** that you'll need frequently. Focus on things that differ from standard practices or would surprise a new team member.

## Boss Information
- **Name**: Bobble
- **Communication Style**: Direct feedback when frustrated, values working solutions over elegant architecture
- **Review Preferences**: Will clearly state when development has gone off track, prefers practical solutions

## Project Overview
- **Project Name**: Email Project + Stocks Project (dual active projects)
- **Main Purpose**: Email: ML-based spam filtering (95.6% accuracy) | Stocks: Agentic Loop penny stock analysis
- **Target Users**: Email: Personal/small business | Stocks: Individual investors seeking 30-day growth picks
- **Current Phase**: Email: Production-ready, post-refactor | Stocks: Active development, category analysis
- **Hidden Complexity**: Email: Circular import resolution, ensemble ML voting | Stocks: Memory caching preventing real-time updates
- **Technical Debt**: Email: SQLite won't scale, needs PostgreSQL | Stocks: No test coverage, regulatory compliance gaps

## Technology Stack
- **Frontend**: Flask templates (both projects), HTML/CSS/JavaScript dashboards
- **Backend**: Python 3.13, Flask web apps, FastAPI (email), yfinance API (stocks)
- **Database**: Email: SQLite with analytics | Stocks: JSON files with fcntl locking
- **Deployment**: Local development, no CI/CD pipeline yet
- **Version Control**: Git with main branch
- **Gotchas**: Flask memory caching persists across requests, Flask url_for incompatible with FastAPI templates

## Key Conventions
- **Code Style**: Extensive emoji use in logs (🤖, ✅, ❌), KISS/YAGNI/DRY principles
- **Branch Naming**: main branch primary
- **Commit Message Format**: Descriptive with Claude Code attribution
- **PR Process**: Direct commits after Boss review
- **Unwritten Rules**: Always clear caches when debugging memory issues, use file locking for concurrent operations

## Important Resources
- **Main Repository**: /Users/Badman/Desktop/email/REPOS/
- **Documentation**: CLAUDE.md, DEVELOPMENT_BELIEFS.md, working logs in WORKING_LOG/
- **Staging Environment**: Local Flask dev servers (ports 5000, 5006)
- **Production Environment**: Not yet deployed
- **Hidden Dependencies**: yfinance API (rate limited), IMAP providers (Gmail, iCloud), personal whitelist domains

## Critical Notes
- **Memory Cache Bug**: Flask global variables persist across requests - requires explicit clearing
- **File Locking Required**: JSON operations need fcntl locking to prevent corruption during concurrent access
- **ML Provider Thresholds**: Gmail 85%, iCloud 80% confidence thresholds for spam detection
- **Circular Imports**: Use classification_utils.py and config_loader.py as bridge modules
- **Domain Validation**: Advanced gibberish detection with entropy analysis - performance optimized with regex

## The Surprise Factor
Before adding info here, ask: "Would a competent engineer be surprised by this?"

---
*Last Updated: June 22, 2025 - Post repository survey and stocks project debugging*