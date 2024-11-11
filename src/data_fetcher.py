import requests
import pandas as pd
import io
from config import NEWS_URL, SCREENER_BASE_URL, FINVIZ_API_TOKEN, SCREENER_FILTERS, NEWS_FILE, SCREENER_FILE

def fetch_and_save_data(url, file_name):
    try:
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        df.to_csv(file_name, index=False)
        print(f"Data saved to {file_name}")
        return df
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {str(e)}")
        return None

def export_news_data():
    url = f"{NEWS_URL}?v=3&auth={FINVIZ_API_TOKEN}"
    return fetch_and_save_data(url, NEWS_FILE)

def export_screener_data():
    url = f"{SCREENER_BASE_URL}?{SCREENER_FILTERS}&auth={FINVIZ_API_TOKEN}"
    return fetch_and_save_data(url, SCREENER_FILE)

def load_data(file_name):
    try:
        return pd.read_csv(file_name)
    except FileNotFoundError:
        print(f"File {file_name} not found.")
        return None
