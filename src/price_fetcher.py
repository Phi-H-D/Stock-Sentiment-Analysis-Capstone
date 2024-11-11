import yfinance as yf

def get_current_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
    return None

def fetch_current_prices(tickers):
    current_prices = {}
    for ticker in tickers:
        price = get_current_price(ticker)
        if price is not None:
            current_prices[ticker] = price
        else:
            print(f"Unable to fetch current price for {ticker}")
    return current_prices
