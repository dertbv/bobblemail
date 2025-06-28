# Stocks Project Structure

## Penny Stock Analyzer (30-Day Picks)
- **Purpose**: Identify stocks with 20%+ growth potential in 30 days
- **Architecture**: 5-phase analysis pipeline
- **Status**: ✅ Enterprise-grade, actively used daily

## Directory Structure

```
stocks_project/                  # Penny stock analyzer (30-day picks)
├── Core Components:
│   ├── app.py                           # Flask web app (port 8080)
│   ├── run_penny_stock_analysis.py      # 5-phase analyzer
│   └── live_research_system.py          # Real-time market data
│
├── Web Interface:
│   ├── templates/                       # Flask/Jinja2 templates
│   └── static/                          # CSS/JS assets
│
├── Analysis Pipeline:
│   └── outputs/                         # Timestamped results
│       └── penny_stocks_YYYYMMDD/       # Per-run analysis
│           ├── phase1-5/                # JSON phase outputs
│           └── penny_stock_report.md    # Final report
│
├── Build System:
│   ├── build_macos.py                  # macOS app builder
│   ├── stocks.spec                     # PyInstaller config
│   └── create_dmg.sh                   # DMG creator
│
└── docs/penny_stocks/                  # Analysis documentation
```

## 5-Phase Analysis Pipeline
- **Phase 1**: Stock discovery and filtering
- **Phase 2**: Technical analysis (RSI, MACD, moving averages)
- **Phase 3**: Fundamental analysis (revenue, earnings, ratios)
- **Phase 4**: Sentiment analysis (news, social media)
- **Phase 5**: Final rankings with exit strategies

## Features
- Live market data with 15-minute TTL cache
- Non-blocking async operations
- Comprehensive security (input validation, XSS protection)
- Native macOS packaging capability
- File locking for concurrent operation safety
- Investment rationale generation from data

## Interface
- **Flask App**: http://localhost:8080
- **Data Output**: Timestamped JSON outputs for each analysis run

## Build System
- **macOS Packaging**: PyInstaller-based native app creation
- **DMG Creation**: Automated disk image generation
- **Distribution Ready**: Enterprise packaging for deployment

## Key Technical Features
- TTL-based caching prevents API rate limiting
- Modular 5-phase analysis with JSON outputs
- Memory caching with fcntl file locking
- Real-time market data integration with yfinance API
- Comprehensive penny stock screening and analysis

## Technical Innovations
- TTL-based caching prevents API rate limiting
- Modular 5-phase analysis with JSON outputs
- Enterprise packaging for distribution
- File locking for concurrent operation safety
- Investment rationale generation from data

## Quick Access
- **Config**: `app.py` (Flask app configuration)
- **Data**: `outputs/penny_stocks_YYYYMMDD/` (Timestamped analysis results)
- **Documentation**: `docs/penny_stocks/` (Analysis documentation)
- **Web Interface**: http://localhost:8080 (Flask app)