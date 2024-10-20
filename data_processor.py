import pandas as pd

def process_news_data(news_data):
    news_data['Date'] = pd.to_datetime(news_data['Date'])
    news_data['Ticker'] = news_data['Ticker'].str.split(',')
    news_data = news_data.explode('Ticker')
    news_data['Ticker'] = news_data['Ticker'].str.strip()
    return news_data

def merge_data(news_data, screener_data):
    return pd.merge(news_data, screener_data[['Ticker', 'Relative Volume', 'Price']], on='Ticker', how='left')

def calculate_trends(merged_data, current_prices):
    merged_data['Current Price'] = merged_data['Ticker'].map(current_prices)
    merged_data['Price'] = pd.to_numeric(merged_data['Price'], errors='coerce')
    merged_data['Trend $'] = merged_data.apply(lambda row: 
        row['Current Price'] - row['Price'] if pd.notnull(row['Current Price']) and pd.notnull(row['Price']) else None, 
        axis=1
    )
    return merged_data

def prepare_final_data(merged_data):
    result = merged_data[['Ticker', 'Date', 'Title', 'Relative Volume', 'Price', 'Current Price', 'Trend $']]
    result.columns = ['TICKER', 'Date', 'News', 'Relative Volume', 'Screener Price', 'Current Price', 'Trend $']
    result = result.sort_values('Date', ascending=False).drop_duplicates(subset=['TICKER', 'News'], keep='first')
    return result
