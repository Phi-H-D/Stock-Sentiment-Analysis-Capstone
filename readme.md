# Financial News Sentiment Analysis Dashboard

A real-time dashboard for analyzing financial news sentiment and market trends. This project combines news feeds, multiple sentiment analyzers, and market data to provide insights into the relationship between news sentiment and stock price movements.

## Features

- Real-time financial news aggregation from Yahoo Finance RSS feeds
- Multi-model sentiment analysis using:
  - NLTK Sentiment Analyzer
  - FinVADER (Financial domain-specific)
  - FinBERT (Financial BERT model)
- Market data integration with real-time price tracking
- Interactive dashboard with:
  - Sentiment analysis results table
  - Price trend visualization
  - Volume-weighted sentiment analysis
  - Correlation metrics
- Auto-refresh capability for real-time monitoring
- Data export functionality

## Prerequisites

- Python 3.8 or higher
- FINVIZ API Token (for market data)
- Sufficient disk space for ML models
- Internet connection for real-time data fetching

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <project-directory>
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Download required NLTK data:
```bash
python -c "import nltk; nltk.download('vader_lexicon')"
```

5. Create a `.env` file in the project root and add your FINVIZ API token:
```
FINVIZ_API_TOKEN=your_token_here
```

## Project Structure

```
├── dashboard.py              # Streamlit dashboard application
├── data_fetcher.py          # Data fetching utilities
├── data_processor.py        # Data processing and transformation
├── price_fetcher.py         # Real-time price data fetching
├── rss feed with sentiment analyzers.py  # News fetching and sentiment analysis
├── main.py                  # Main script for data pipeline
├── requirements.txt         # Project dependencies
└── config.py               # Configuration settings
```

## Dashboard Usage

### Starting the Dashboard
```bash
streamlit run dashboard.py
```

### Data Refresh Options

1. **Manual Refresh**
   - Click "Refresh Now" button in the sidebar
   - This will automatically:
     1. Run data collection from FINVIZ (main.py)
     2. Run RSS feed sentiment analysis (rss feed with sentiment analyzers.py)
     3. Update the dashboard with new data
   - Progress will be shown during refresh

2. **Auto-Refresh**
   - Set desired interval (5, 10, 20, or 30 minutes)
   - Click "Start Auto-refresh" to begin automatic updates
   - Each refresh cycle will:
     1. Run main.py for market data
     2. Run RSS sentiment analysis
     3. Update visualizations automatically
   - Status indicator shows when auto-refresh is active
   - Click "Stop Auto-refresh" to disable

3. **API Token Management**
   - Enter/update FINVIZ API token directly in dashboard
   - Token is securely saved to .env file
   - New token will be used in subsequent data refreshes

## Dashboard Features

### Sentiment Analysis Tab
- Filter by ticker symbols
- Set minimum sentiment threshold
- Filter by relative volume
- View detailed sentiment scores from multiple models
- Export data as CSV

### Trend Analysis Tab
- Scatter plot of sentiment vs price changes
- Volume-weighted sentiment analysis
- Sentiment distribution visualization
- Correlation metrics

## Data Pipeline

1. **Data Collection**
   - News data from Yahoo Finance RSS feeds
   - Market data from FINVIZ API
   - Real-time price data from Yahoo Finance

2. **Sentiment Analysis**
   - NLTK: General sentiment analysis
   - FinVADER: Financial domain-specific lexicon
   - FinBERT: Transformer-based financial sentiment

3. **Data Processing**
   - News data cleaning and normalization
   - Price trend calculation
   - Volume-weighted sentiment aggregation

## Auto-Refresh Configuration

The dashboard supports automatic data updates with configurable intervals:
- Available intervals: 5, 10, 20, or 30 minutes
- Manual refresh option available
- Status indicator shows current auto-refresh state

## Troubleshooting

Common issues and solutions:

1. **Missing Data Files**
   - Ensure all required CSV files exist
   - Check file permissions
   - Run main.py to regenerate data files

2. **API Token Issues**
   - Verify FINVIZ API token in .env file
   - Check token validity and permissions

3. **Sentiment Model Errors**
   - Ensure sufficient disk space for models
   - Check internet connection for model downloads
   - Verify NLTK data installation
