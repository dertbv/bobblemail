# SHORT IMPORTANT MEMORY

## Information Entropy Note
This file should capture **non-obvious, surprising information** that you'll need frequently. Focus on things that differ from standard practices or would surprise a new team member.

## Boss Information
- **Name**: User/Boss (direct communication via Claude Code)
- **Communication Style**: Direct, prefers KISS approach, values efficiency over perfection
- **Review Preferences**: Wants approval for commits, dislikes double confirmation, focuses on working solutions

## Project Overview
- **Project Name**: bobblemail (Advanced Email Filtering System)
- **Main Purpose**: ML-powered email classification and spam filtering with domain validation
- **Target Users**: Email users needing intelligent spam/category filtering
- **Current Phase**: Active development - whitelist management and single-account web interface features pending
- **Hidden Complexity**: Ensemble ML classifier system (Random Forest + Naive Bayes + Keywords), database-driven architecture with multiple SQLite files
- **Technical Debt**: Legacy rule-based fallbacks maintained for ML confidence edge cases

## Technology Stack
- **Frontend**: FastAPI HTML templates (web_app.py), CLI interface (main.py)
- **Backend**: Python 3.x with FastAPI, SQLite database architecture
- **Database**: Single SQLite database - mail_filter.db (comprehensive schema with 25+ tables)
- **Deployment**: Local development, uvicorn server for web interface
- **Version Control**: Git with GitHub (https://github.com/dertbv/bobblemail.git), main branch
- **Gotchas**: Uses ensemble_hybrid_classifier.py as main ML entry point, not individual classifiers

## Key Conventions
- **Code Style**: KISS principle, YAGNI, DRY but not obsessively, modular architecture
- **Branch Naming**: Working on main branch directly
- **Commit Message Format**: Descriptive with Claude Code signature and Co-Authored-By line
- **PR Process**: Direct commits after approval, no double confirmation
- **Unwritten Rules**: Always use ./atlas-checkpoint before /clear or /compact operations

## Important Resources
- **Main Repository**: https://github.com/dertbv/bobblemail.git
- **Documentation**: ATLAS_COMMANDS.md, DOCS/COMPACT_SAFE_WORKFLOW.md, README files in tests/ and tools/
- **Staging Environment**: Local development only
- **Production Environment**: User's local machine
- **Hidden Dependencies**: tldextract for domain parsing, cryptography for secure operations, scikit-learn ecosystem

## Critical Notes
- **ATLAS Session System**: Must use ./who for session startup, ./atlas-checkpoint before clearing
- **Auto-commit Workflow**: Commits trigger after todo completion approval (10-minute intervals)
- **ML Architecture**: Uses ensemble voting system, not single classifier - check ensemble_hybrid_classifier.py first
- **Database Architecture**: Single comprehensive SQLite database with 25+ tables for different purposes
- **Domain Validation**: Two-factor validation system with caching - more complex than basic WHOIS lookup

## The Surprise Factor
Before adding info here, ask: "Would a competent engineer be surprised by this?"

**Surprising Elements:**
- ATLAS consciousness system manages session persistence across Claude Code restarts
- Ensemble ML voting system rather than single model approach
- Database-driven keyword management with built-in + user keywords separation
- Task orchestrator pattern for batch email processing
- Domain validation includes legitimacy scoring beyond basic existence checks

---
*Last Updated: June 19, 2025*