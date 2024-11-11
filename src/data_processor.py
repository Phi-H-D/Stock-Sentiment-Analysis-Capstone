import pandas as pd

def process_news_data(news_data):
    # Add debug print to see column names
    print("Columns in news_data before processing:", news_data.columns)
    
    # Ensure consistent column naming
    news_data = news_data.copy()
    
    # Rename columns to standard format
    column_mapping = {
        'Title': 'News Title',
        'Url': 'News URL',
        'Ticker': 'TICKER'
    }
    
    news_data = news_data.rename(columns=column_mapping)
    
    # Convert date column
    if 'Date' in news_data.columns:
        news_data['Date'] = pd.to_datetime(news_data['Date'])
    
    # Handle ticker column if it contains comma-separated values
    if 'TICKER' in news_data.columns:
        if news_data['TICKER'].dtype == 'object':
            news_data['TICKER'] = news_data['TICKER'].str.split(',')
            news_data = news_data.explode('TICKER')
            news_data['TICKER'] = news_data['TICKER'].str.strip()
    
    print("Columns in news_data after processing:", news_data.columns)
    return news_data

def merge_data(news_data, screener_data):
    # Add debug print to see column names
    print("Columns in screener_data before merge:", screener_data.columns)
    
    # Ensure screener_data has consistent column names
    screener_data = screener_data.copy()
    screener_mapping = {
        'Ticker': 'TICKER',
        'Price': 'Screener Price'
    }
    screener_data = screener_data.rename(columns=screener_mapping)
    
    # Select only necessary columns from screener_data to avoid duplicates
    screener_columns = ['TICKER', 'Relative Volume', 'Screener Price']
    screener_subset = screener_data[screener_columns].copy()
    
    # Perform merge
    merged_data = pd.merge(
        news_data,
        screener_subset,
        on='TICKER',
        how='left'
    )
    
    print("Columns in merged_data:", merged_data.columns)
    return merged_data

def calculate_trends(merged_data, current_prices):
    # Convert current_prices dictionary to series for easier mapping
    current_prices_series = pd.Series(current_prices)
    
    # Add current price column
    merged_data['Current Price'] = merged_data['TICKER'].map(current_prices_series)
    
    # Convert price columns to numeric
    merged_data['Screener Price'] = pd.to_numeric(merged_data['Screener Price'], errors='coerce')
    
    # Calculate trend
    merged_data['Trend $'] = merged_data.apply(
        lambda row: row['Current Price'] - row['Screener Price'] 
        if pd.notnull(row['Current Price']) and pd.notnull(row['Screener Price']) 
        else None,
        axis=1
    )
    
    print("Columns after calculating trends:", merged_data.columns)
    return merged_data

def prepare_final_data(merged_data):
    # Select final columns in correct order
    final_columns = [
        'TICKER',
        'Date',
        'News Title',
        'News URL',
        'Relative Volume',
        'Screener Price',
        'Current Price',
        'Trend $'
    ]
    
    # Only include columns that exist
    available_columns = [col for col in final_columns if col in merged_data.columns]
    result = merged_data[available_columns].copy()
    
    # Sort by date
    if 'Date' in result.columns:
        result = result.sort_values('Date', ascending=False)
    
    # Remove duplicates
    result = result.drop_duplicates(subset=['TICKER', 'News URL'], keep='first')
    
    print("Columns in final data:", result.columns)
    return result