import pandas as pd
import feedparser
from datetime import datetime, timedelta
import time
import csv
import yfinance as yf
import pytz
from pandas.tseries.offsets import BDay
import re
import requests
from bs4 import BeautifulSoup
from nltk.sentiment import SentimentIntensityAnalyzer
from finvader import finvader
from transformers import pipeline
import numpy as np

# Global variable for FinBERT pipeline
FINBERT_PIPELINE = None

# Initialize sentiment analyzers
print("Initializing sentiment analyzers...")
nltk_sia = SentimentIntensityAnalyzer()
def initialize_finbert():
    global FINBERT_PIPELINE
    if FINBERT_PIPELINE is None:
        print("Initializing FinBERT model...")
        FINBERT_PIPELINE = pipeline("text-classification", model="ProsusAI/finbert")


NY_TZ = pytz.timezone('America/New_York')

def clean_text(text):
    # Remove special characters while preserving spaces
    text = re.sub(r'[^A-Za-z0-9\s]', ' ', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def chunk_text(text, max_length=500):
    """Split text into chunks that won't exceed the model's maximum length after tokenization"""
    # Roughly estimate that each word will be 1-2 tokens
    words_per_chunk = max_length // 2  
    words = text.split()
    
    # Split into chunks
    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunk = ' '.join(words[i:i + words_per_chunk])
        chunks.append(chunk)
    return chunks

def get_finbert_sentiment(text):
    try:
        global FINBERT_PIPELINE
        if FINBERT_PIPELINE is None:
            initialize_finbert()
        
        # Split long text into chunks
        chunks = chunk_text(text)
        
        # Get sentiment for each chunk
        sentiments = []
        for chunk in chunks:
            result = FINBERT_PIPELINE(chunk)[0]
            
            # Convert the prediction to a score between -1 and 1
            if result['label'] == 'positive':
                sentiments.append(result['score'])
            elif result['label'] == 'negative':
                sentiments.append(-result['score'])
            else:  # neutral
                sentiments.append(0.0)
        
        # Average the sentiments if we had multiple chunks
        if sentiments:
            return sum(sentiments) / len(sentiments)
        return 0.0
        
    except Exception as e:
        print(f"Error in FinBERT sentiment analysis: {str(e)}")
        return 0.0  # Return neutral sentiment in case of error

def get_nltk_sentiment(text):
    cleaned_text = clean_text(text)
    scores = nltk_sia.polarity_scores(cleaned_text)
    return scores['compound']

def get_finvader_sentiment(text):
    try:
        cleaned_text = clean_text(text)
        # Use finvader directly as shown in the example
        sentiment = finvader(cleaned_text, 
                           use_sentibignomics=True, 
                           use_henry=True, 
                           indicator='compound')
        return sentiment
    except Exception as e:
        print(f"Error in FinVADER sentiment analysis: {str(e)}")
        return 0.0

def get_body_sentiment(url):
    try:
        page = requests.get(url, timeout=10)
        soup = BeautifulSoup(page.content, 'html.parser')
        paragraphs = soup.find_all('p')
        combined_text = " ".join([p.get_text() for p in paragraphs])
        
        combined_text = clean_text(combined_text)
        
        # Get sentiments
        nltk_sentiment = get_nltk_sentiment(combined_text)
        finvader_sentiment = get_finvader_sentiment(combined_text)
        finbert_sentiment = get_finbert_sentiment(combined_text)
        
        return {
            'nltk_body_sentiment': nltk_sentiment,
            'finvader_body_sentiment': finvader_sentiment,
            'finbert_body_sentiment': finbert_sentiment
        }
    except Exception as e:
        print(f"Error fetching body sentiment: {str(e)}")
        return {
            'nltk_body_sentiment': None,
            'finvader_body_sentiment': None,
            'finbert_body_sentiment': None
        }

def adjust_sentiment_for_trend(sentiment_score, trend_percentage):
    trend_factor = 0.01  # Base adjustment factor for trend
    
    if trend_percentage > 0:
        base_sentiment = 0.1
        adjustment = min(trend_factor * trend_percentage, 1.0)
    else:
        base_sentiment = -0.1
        adjustment = max(trend_factor * trend_percentage, -1.0)
    
    adjusted_sentiment = base_sentiment + adjustment
    return max(min(adjusted_sentiment, 1.0), -1.0)

def fetch_yahoo_rss_news(ticker):
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    feed = feedparser.parse(url)
    news_items = []
    today = datetime.now(NY_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    
    for entry in feed.entries:
        publish_time = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z").astimezone(NY_TZ)
        if publish_time >= today:
            title_sentiments = {
                'nltk_title_sentiment': get_nltk_sentiment(entry.title),
                'finvader_title_sentiment': get_finvader_sentiment(entry.title),
                'finbert_title_sentiment': get_finbert_sentiment(entry.title)
            }
            
            body_sentiments = get_body_sentiment(entry.link)
            
            formatted_time = publish_time.strftime("%Y-%m-%d %H:%M:%S")
            news_item = {
                'ticker': ticker,
                'publish_time': formatted_time,
                'title': entry.title,
                'link': entry.link,
                **title_sentiments,
                **body_sentiments
            }
            news_items.append(news_item)
    
    return news_items

def is_market_open(time):
    return (time.weekday() < 5 and  # Monday to Friday
            ((time.hour == 9 and time.minute >= 30) or  # 9:30 AM to 4:00 PM
             (time.hour > 9 and time.hour < 16) or
             (time.hour == 16 and time.minute == 0)))

def get_price_trend(ticker, news_time):
    try:
        stock = yf.Ticker(ticker)
        current_time = datetime.now(NY_TZ)
        
        if is_market_open(news_time):
            start_time = news_time - timedelta(minutes=10)
            end_time = min(news_time + timedelta(minutes=10), current_time)
            data = stock.history(start=start_time, end=end_time, interval="1m")
            
            if len(data) > 0:
                price_10_min_before = data.iloc[0]['Close']
                price_at_news = data.loc[data.index.asof(news_time), 'Close']
                price_after = data.iloc[-1]['Close']
                
                trend_before = ((price_at_news - price_10_min_before) / price_10_min_before) * 100
                trend_after = ((price_after - price_at_news) / price_at_news) * 100
                
                minutes_after = min(10, (end_time - news_time).total_seconds() / 60)
                
                nltk_adjusted = adjust_sentiment_for_trend(0, trend_after)
                finvader_adjusted = adjust_sentiment_for_trend(0, trend_after)
                finbert_adjusted = adjust_sentiment_for_trend(0, trend_after)
                
                return {
                    'price_10_min_before': price_10_min_before,
                    'price_at_news': price_at_news,
                    'price_after': price_after,
                    'trend_before': trend_before,
                    'trend_after': trend_after,
                    'minutes_after': minutes_after,
                    'market_status': "Open",
                    'nltk_price_sentiment': nltk_adjusted,
                    'finvader_price_sentiment': finvader_adjusted,
                    'finbert_price_sentiment': finbert_adjusted
                }
        
        return {
            'price_10_min_before': None,
            'price_at_news': None,
            'price_after': None,
            'trend_before': None,
            'trend_after': None,
            'minutes_after': None,
            'market_status': "Closed",
            'nltk_price_sentiment': None,
            'finvader_price_sentiment': None,
            'finbert_price_sentiment': None
        }
    except Exception as e:
        print(f"Error fetching price trend for {ticker} at {news_time}: {str(e)}")
        return {
            'price_10_min_before': None,
            'price_at_news': None,
            'price_after': None,
            'trend_before': None,
            'trend_after': None,
            'minutes_after': None,
            'market_status': "Error",
            'nltk_price_sentiment': None,
            'finvader_price_sentiment': None,
            'finbert_price_sentiment': None
        }

def main():
    try:
        df = pd.read_csv('finviz_news_and_stock_data.csv')
        tickers = df['TICKER'].unique()
    except FileNotFoundError:
        print("Error: 'finviz_news_and_stock_data.csv' not found. Please ensure the file exists.")
        return
    except pd.errors.EmptyDataError:
        print("Error: 'finviz_news_and_stock_data.csv' is empty.")
        return
    except KeyError:
        print("Error: 'TICKER' column not found in 'finviz_news_and_stock_data.csv'.")
        return

    all_news = []
    for ticker in tickers:
        print(f"Fetching news for {ticker}")
        news = fetch_yahoo_rss_news(ticker)
        all_news.extend(news)
        time.sleep(1)

    news_df = pd.DataFrame(all_news)
    if news_df.empty:
        print("No news found for today. Exiting.")
        return

    news_df['publish_time'] = pd.to_datetime(news_df['publish_time']).dt.tz_localize(NY_TZ)
    news_df = news_df.sort_values('publish_time', ascending=False)

    print("Analyzing price trends and calculating adjusted sentiments...")
    trends = news_df.apply(lambda row: get_price_trend(row['ticker'], row['publish_time']), axis=1)
    
    for key in trends.iloc[0].keys():
        news_df[key] = trends.apply(lambda x: x[key])

    news_df['publish_time'] = news_df['publish_time'].dt.strftime('%Y-%m-%d %H:%M:%S')

    for column_type in ['title', 'body', 'price']:
        columns = [f'{analyzer}_{column_type}_sentiment' 
                  for analyzer in ['nltk', 'finvader', 'finbert']]
        news_df[f'aggregate_{column_type}_sentiment'] = news_df[columns].mean(axis=1)

    output_file = 'yahoo_rss_news_with_sentiment_analysis.csv'
    news_df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL)
    print(f"News data with sentiment analysis saved to '{output_file}'")
    print(f"Total news items: {len(news_df)}")

if __name__ == "__main__":
    main()