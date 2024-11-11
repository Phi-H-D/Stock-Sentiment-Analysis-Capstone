import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_volume():
    """Generate relative volume with better distribution across ranges"""
    # Define volume ranges with their probabilities
    volume_ranges = {
        'low': (0, 1, 0.2),      # 20% chance
        'normal': (1, 5, 0.3),   # 30% chance
        'high': (5, 20, 0.2),    # 20% chance
        'very_high': (20, 100, 0.15),  # 15% chance
        'extreme': (100, 1000, 0.15)   # 15% chance
    }
    
    # Random selection based on probabilities
    choice = np.random.random()
    cumulative_prob = 0
    
    for range_name, (min_val, max_val, prob) in volume_ranges.items():
        cumulative_prob += prob
        if choice <= cumulative_prob:
            return round(np.random.uniform(min_val, max_val), 2)
    
    return round(np.random.uniform(0, 5), 2)  # Fallback case

def generate_dummy_data(num_tickers=20, news_per_ticker=5):
    """Generate realistic dummy financial data matching the dashboard format"""
    
    # Common tickers for demo
    tickers = [
        'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'NVDA', 'TSLA', 'JPM', 
        'BAC', 'WMT', 'DIS', 'NFLX', 'INTC', 'AMD', 'CRM', 'PYPL', 'ADBE', 
        'CSCO', 'VZ', 'KO'
    ][:num_tickers]
    
    # Generate base data
    sentiment_data = []
    screener_data = []
    current_time = datetime.now()
    
    # Generate some high-volume tickers
    high_volume_tickers = np.random.choice(tickers, size=int(len(tickers) * 0.3), replace=False)
    
    for ticker in tickers:
        # Generate relative volume
        if ticker in high_volume_tickers:
            # For high-volume tickers, use higher ranges
            rel_volume = np.random.choice([
                np.random.uniform(20, 100),   # very high
                np.random.uniform(100, 1000)  # extreme
            ])
        else:
            rel_volume = generate_volume()
        
        screener_data.append({
            'Ticker': ticker,
            'Relative Volume': round(rel_volume, 2),
            'Volume': int(np.random.randint(500000, 5000000)),
            'Price': round(np.random.uniform(10, 1000), 2),
            'Change': round(np.random.normal(0, 2), 2)
        })
        
        for _ in range(news_per_ticker):
            # Generate realistic news timestamps within last 24 hours
            publish_time = current_time - timedelta(
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )
            
            # Generate sentiment scores with correlation to volume
            base_sentiment = np.random.normal(0, 0.5)
            volume_factor = rel_volume / 1000  # Normalize volume to 0-1 range
            
            # Add some correlation between volume and sentiment intensity
            sentiment_multiplier = 1 + (volume_factor * 0.5)
            
            nltk_sentiment = round(np.clip(base_sentiment * sentiment_multiplier, -1, 1), 3)
            finbert_sentiment = round(np.clip((base_sentiment + np.random.normal(0, 0.2)) * sentiment_multiplier, -1, 1), 3)
            finvader_sentiment = round(np.clip((base_sentiment + np.random.normal(0, 0.3)) * sentiment_multiplier, -1, 1), 3)
            
            # Calculate aggregate sentiment
            aggregate_sentiment = round(np.mean([nltk_sentiment, finbert_sentiment, finvader_sentiment]), 3)
            
            # Generate price changes with some correlation to both sentiment and volume
            base_price = round(np.random.uniform(10, 1000), 2)
            sentiment_impact = aggregate_sentiment * (1 + volume_factor)
            price_change = round(sentiment_impact * np.random.uniform(0.5, 2.0), 2)
            
            # Generate volume-appropriate title
            volume_desc = (
                'Amid Extremely Heavy Trading' if rel_volume > 100
                else 'Amid Heavy Trading' if rel_volume > 20
                else 'on High Volume' if rel_volume > 5
                else 'with Average Volume' if rel_volume > 0.5
                else 'on Light Volume'
            )
            
            movement_words = {
                'positive': ['Surges', 'Rallies', 'Soars', 'Jumps', 'Spikes'] if rel_volume > 20
                           else ['Gains', 'Advances', 'Improves', 'Rises', 'Climbs'],
                'negative': ['Plunges', 'Crashes', 'Dives', 'Tumbles', 'Collapses'] if rel_volume > 20
                           else ['Drops', 'Declines', 'Falls', 'Weakens', 'Retreats'],
                'neutral': ['Swings', 'Shifts', 'Moves', 'Trades', 'Fluctuates']
            }
            
            sentiment_category = (
                'positive' if aggregate_sentiment > 0.2
                else 'negative' if aggregate_sentiment < -0.2
                else 'neutral'
            )
            
            movement_word = np.random.choice(movement_words[sentiment_category])
            
            news_titles = [
                f"{ticker} {movement_word} {volume_desc}",
                f"Breaking: {ticker} {movement_word} {volume_desc}",
                f"Alert: {ticker} {movement_word} {volume_desc}",
                f"Market Watch: {ticker} {movement_word} Today",
                f"Trading Update: {ticker} Stock {movement_word}"
            ]
            
            sentiment_data.append({
                'ticker': ticker,
                'publish_time': publish_time.strftime('%Y-%m-%d %H:%M:%S'),
                'title': np.random.choice(news_titles),
                'link': f"https://finance.example.com/{ticker.lower()}/{int(publish_time.timestamp())}",
                'nltk_body_sentiment': nltk_sentiment,
                'finbert_body_sentiment': finbert_sentiment,
                'finvader_body_sentiment': finvader_sentiment,
                'aggregate_body_sentiment': aggregate_sentiment,
                'price_at_news': base_price,
                'price_after': base_price + price_change,
                'price_change': price_change
            })
    
    return (pd.DataFrame(sentiment_data), pd.DataFrame(screener_data))

# Generate and save dummy data
if __name__ == "__main__":
    sentiment_df, screener_df = generate_dummy_data()
    sentiment_df.to_csv('yahoo_rss_news_with_sentiment_analysis.csv', index=False)
    screener_df.to_csv('screener_data.csv', index=False)
    print("Dummy data generated and saved to CSV files")
    
    # Print volume distribution statistics
    print("\nRelative Volume Distribution:")
    volume_ranges = {
        '0-1x': lambda x: x <= 1,
        '1-5x': lambda x: 1 < x <= 5,
        '5-20x': lambda x: 5 < x <= 20,
        '20-100x': lambda x: 20 < x <= 100,
        '100-1000x': lambda x: x > 100
    }
    
    for range_name, range_func in volume_ranges.items():
        count = len(screener_df[screener_df['Relative Volume'].apply(range_func)])
        percentage = (count / len(screener_df)) * 100
        print(f"{range_name}: {count} tickers ({percentage:.1f}%)")