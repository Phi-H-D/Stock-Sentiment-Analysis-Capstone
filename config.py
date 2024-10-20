import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API endpoints
NEWS_URL = "https://elite.finviz.com/news_export.ashx"
SCREENER_BASE_URL = "https://elite.finviz.com/export.ashx"

# File names for saved data
NEWS_FILE = "news_data.csv"
SCREENER_FILE = "screener_data.csv"
OUTPUT_FILE = "finviz_news_and_stock_data.csv"

# API Token
FINVIZ_API_TOKEN = os.getenv("FINVIZ_API_TOKEN")

# Screener filters
SCREENER_FILTERS = "v=152&p=i1&f=cap_0.001to&ft=4&o=-afterchange&ar=10&c=0,1,6,24,25,85,26,27,28,29,30,31,84,50,51,83,61,63,64,67,65,66,71,72"
