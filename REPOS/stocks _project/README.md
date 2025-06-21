# Penny Stock Analysis Tool

An Agentic Loop system that analyzes penny stocks and identifies the top 10 picks with the greatest potential to rise in the next 30 days.

## Quick Start

### Web Application (Recommended)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the web server:
```bash
python app.py
```

3. Open your browser to: `http://localhost:5000`

4. Click "Start Analysis" and view results in the dashboard

### Command Line Tool

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the analysis:
```bash
python run_penny_stock_analysis.py
```

3. View results in the generated `outputs/penny_stocks_TIMESTAMP/` directory

## System Architecture

This tool uses the Agentic Loop pattern with three agents:

- **Atlas (Orchestrator)**: Coordinates the entire workflow
- **Mercury (Specialist)**: Performs technical, fundamental, and sentiment analysis
- **Apollo (Evaluator)**: Scores outputs and ensures quality (target: 90/100)

## Analysis Phases

1. **Data Collection**: Identify penny stocks (< $5, market cap > $1M)
2. **Technical Analysis**: Calculate indicators, momentum, volume patterns
3. **Fundamental Analysis**: Evaluate financial health and growth prospects
4. **Sentiment Analysis**: Process news and social media sentiment
5. **Integration**: Combine all factors into ranked recommendations

## Web Application Features

- **Interactive Dashboard**: Real-time analysis progress and results
- **Top 10 Rankings**: Sortable table with detailed metrics
- **Individual Stock Pages**: Detailed analysis for each pick
- **Data Visualizations**: Charts showing score distributions and upside potential
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **API Endpoints**: Programmatic access to analysis data

## API Endpoints

- `POST /api/start-analysis`: Start a new analysis
- `GET /api/analysis-status`: Check analysis progress
- `GET /api/results`: Get analysis results
- `GET /api/stock/<ticker>`: Get details for specific stock
- `GET /api/health`: Service health check

## Output Files

- Web results: Available through dashboard at `http://localhost:5000`
- Command line: `outputs/penny_stocks_TIMESTAMP/penny_stock_report.md`
- Raw data: `phase1/` through `phase5/` directories with JSON files

## Risk Disclaimer

**IMPORTANT**: This tool is for educational and informational purposes only. Penny stocks are highly speculative and risky. Always consult with qualified financial advisors before making investment decisions.

## Configuration

Modify the analysis parameters in `run_penny_stock_analysis.py`:
- Adjust scoring weights (technical: 40%, fundamental: 40%, sentiment: 20%)
- Change price threshold (default: < $5)
- Modify market cap minimum (default: > $1M)
- Update TARGET_SCORE for quality control (default: 90)

## Data Sources

- Yahoo Finance API for market data
- SEC filings for fundamental data
- News APIs for sentiment analysis
- Social media monitoring for buzz tracking