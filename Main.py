import requests
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import io
import os

# API endpoints
NEWS_URL = "https://elite.finviz.com/news_export.ashx?v=3&auth=e324a44e-3f12-4184-b9d9-649c30ce6efb"
SCREENER_URL = "https://elite.finviz.com/export.ashx?v=152&p=i1&f=cap_0.001to&ft=4&o=-afterchange&ar=10&c=0,1,6,24,25,85,26,27,28,29,30,31,84,50,51,83,61,63,64,67,65,66,71,72&auth=e324a44e-3f12-4184-b9d9-649c30ce6efb"

# File names for saved data
NEWS_FILE = "news_data.csv"
SCREENER_FILE = "screener_data.csv"

def fetch_and_save_data(url, file_name):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        df = pd.read_csv(io.StringIO(response.text))
        df.to_csv(file_name, index=False)
        print(f"Data saved to {file_name}")
        return df
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {str(e)}")
        return None

def load_data(file_name):
    if os.path.exists(file_name):
        return pd.read_csv(file_name)
    else:
        print(f"File {file_name} not found.")
        return None

def get_current_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
    return None

def main():
    # Fetch and save data
    print("Fetching and saving news data...")
    news_data = fetch_and_save_data(NEWS_URL, NEWS_FILE)
    print("Fetching and saving screener data...")
    screener_data = fetch_and_save_data(SCREENER_URL, SCREENER_FILE)

    if news_data is None or screener_data is None:
        print("Failed to fetch data. Attempting to load from saved files...")
        news_data = load_data(NEWS_FILE)
        screener_data = load_data(SCREENER_FILE)

    if news_data is None or screener_data is None:
        print("Unable to proceed. Required data is missing.")
        return

    print("News data columns:", news_data.columns.tolist())
    print("Screener data columns:", screener_data.columns.tolist())

    print("Processing data...")
    # Process news data
    news_data['Date'] = pd.to_datetime(news_data['Date'])
    news_data['Ticker'] = news_data['Ticker'].str.split(',')
    news_data = news_data.explode('Ticker')
    news_data['Ticker'] = news_data['Ticker'].str.strip()

    # Merge news and screener data
    merged_data = pd.merge(news_data, screener_data[['Ticker', 'Relative Volume', 'Price']], on='Ticker', how='left')

    # Get current prices
    print("Fetching current prices...")
    unique_tickers = merged_data['Ticker'].unique()
    current_prices = {}
    for ticker in unique_tickers:
        price = get_current_price(ticker)
        if price is not None:
            current_prices[ticker] = price
        else:
            print(f"Unable to fetch current price for {ticker}")

    # Calculate Trend $
    print("Calculating trends...")
    merged_data['Current Price'] = merged_data['Ticker'].map(current_prices)
    merged_data['Price'] = pd.to_numeric(merged_data['Price'], errors='coerce')
    merged_data['Trend $'] = merged_data.apply(lambda row: 
        row['Current Price'] - row['Price'] if pd.notnull(row['Current Price']) and pd.notnull(row['Price']) else None, 
        axis=1
    )

    # Select and rename columns
    result = merged_data[['Ticker', 'Date', 'Title', 'Relative Volume', 'Price', 'Current Price', 'Trend $']]
    result.columns = ['TICKER', 'Date', 'News', 'Relative Volume', 'Screener Price', 'Current Price', 'Trend $']

    # Sort by date (most recent first) and drop duplicates keeping the first occurrence
    result = result.sort_values('Date', ascending=False).drop_duplicates(subset=['TICKER', 'News'], keep='first')

    # Save to CSV
    result.to_csv('finviz_news_and_stock_data.csv', index=False)
    print("Data extracted and saved to 'finviz_news_and_stock_data.csv'")

if __name__ == "__main__":
    main()