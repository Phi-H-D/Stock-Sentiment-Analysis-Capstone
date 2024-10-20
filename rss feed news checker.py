import pandas as pd
import feedparser
from datetime import datetime
import time
import csv
from collections import defaultdict

def fetch_yahoo_rss_news(ticker):
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    feed = feedparser.parse(url)
    news_items = []
    for entry in feed.entries:
        news_items.append({
            'ticker': ticker,
            'publish_time': datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z"),
            'title': entry.title,
            'link': entry.link
        })
    return news_items

def remove_duplicates(news_items):
    unique_news = defaultdict(list)
    for item in news_items:
        key = (item['title'], item['link'])
        unique_news[key].append(item)
    
    deduplicated_news = []
    for news_list in unique_news.values():
        # Keep the item with the earliest publish time
        earliest_news = min(news_list, key=lambda x: x['publish_time'])
        # Combine tickers if the same news appears for multiple tickers
        earliest_news['ticker'] = ','.join(sorted(set(item['ticker'] for item in news_list)))
        deduplicated_news.append(earliest_news)
    
    return deduplicated_news

def main():
    # Read the existing CSV file
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

    # Fetch news for each ticker
    all_news = []
    for ticker in tickers:
        print(f"Fetching news for {ticker}")
        news = fetch_yahoo_rss_news(ticker)
        all_news.extend(news)
        time.sleep(1)  # To avoid overwhelming the API

    # Remove duplicates
    print("Removing duplicate news items...")
    unique_news = remove_duplicates(all_news)

    # Convert to DataFrame and sort by publish time
    news_df = pd.DataFrame(unique_news)
    news_df = news_df.sort_values('publish_time', ascending=False)

    # Save to CSV
    news_df.to_csv('yahoo_rss_news_deduplicated.csv', index=False, quoting=csv.QUOTE_ALL)
    print("Deduplicated Yahoo RSS news data saved to 'yahoo_rss_news_deduplicated.csv'")

    # Print some statistics
    print(f"Total news items fetched: {len(all_news)}")
    print(f"Unique news items after deduplication: {len(unique_news)}")

if __name__ == "__main__":
    main()
