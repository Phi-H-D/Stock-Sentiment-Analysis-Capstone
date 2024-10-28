import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_dummy_data(num_tickers=20, news_per_ticker=5):
    """Generate realistic dummy financial data for dashboard demo"""
    
    # Common tickers for demo
    tickers = [
        'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'NVDA', 'TSLA', 'JPM', 
        'BAC', 'WMT', 'DIS', 'NFLX', 'INTC', 'AMD', 'CRM', 'PYPL', 'ADBE', 
        'CSCO', 'VZ', 'KO'
    ][:num_tickers]
    
    # Generate base data
    data = []
    current_time = datetime.now()
    
    for ticker in tickers:
        for _ in range(news_per_ticker):
            # Generate realistic news timestamps within last 24 hours
            news_time = current_time - timedelta(
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )
            
            # Generate sentiment scores with realistic distributions
            nltk_sentiment = np.random.normal(0.2, 0.3)  # Slightly positive bias
            finbert_sentiment = np.random.normal(0.3, 0.25)  # More positive bias
            finvader_sentiment = np.random.normal(0.15, 0.35)  # Wide distribution
            
            # Clip sentiments to realistic ranges
            nltk_sentiment = np.clip(nltk_sentiment, -1, 1)
            finbert_sentiment = np.clip(finbert_sentiment, -1, 1)
            finvader_sentiment = np.clip(finvader_sentiment, -1, 1)
            
            # Generate trend analysis (price movement %)
            trend = np.random.normal(
                0.1 * nltk_sentiment,  # Slight correlation with sentiment
                0.02
            ) * 100  # Convert to percentage
            
            # Generate relative volume (usually between 0.5 and 3)
            rel_volume = abs(np.random.lognormal(0, 0.5))
            
            # Create news URL
            news_url = f"https://finance.example.com/{ticker.lower()}/{int(news_time.timestamp())}"
            
            data.append({
                'Ticker': ticker,
                'News URL': news_url,
                'NLTK Sentiment': round(nltk_sentiment, 3),
                'FinBERT Sentiment': round(finbert_sentiment, 3),
                'FinVADER Sentiment': round(finvader_sentiment, 3),
                'Trend Analysis': round(trend, 2),
                'Relative Volume': round(rel_volume, 2),
                'Timestamp': news_time
            })
    
    return pd.DataFrame(data)

# Generate and save dummy data
if __name__ == "__main__":
    dummy_data = generate_dummy_data()
    dummy_data.to_csv('dummy_financial_data.csv', index=False)
    print("Dummy data generated and saved to 'dummy_financial_data.csv'")