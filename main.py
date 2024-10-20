from data_fetcher import export_news_data, export_screener_data, load_data
from data_processor import process_news_data, merge_data, calculate_trends, prepare_final_data
from price_fetcher import fetch_current_prices
from config import NEWS_FILE, SCREENER_FILE, OUTPUT_FILE

def main():
    # Fetch and save data
    print("Fetching and saving news data...")
    news_data = export_news_data()
    print("Fetching and saving screener data...")
    screener_data = export_screener_data()

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
    news_data = process_news_data(news_data)
    merged_data = merge_data(news_data, screener_data)

    print("Fetching current prices...")
    unique_tickers = merged_data['Ticker'].unique()
    current_prices = fetch_current_prices(unique_tickers)

    print("Calculating trends...")
    merged_data = calculate_trends(merged_data, current_prices)

    result = prepare_final_data(merged_data)

    # Save to CSV
    result.to_csv(OUTPUT_FILE, index=False)
    print(f"Data extracted and saved to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    main()
