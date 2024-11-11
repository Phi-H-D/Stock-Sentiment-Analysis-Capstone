import os
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (parent of src)
PROJECT_ROOT = Path(__file__).parent.parent

# Define data directory
DATA_DIR = PROJECT_ROOT / 'data'

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Load environment variables from .env file in project root
load_dotenv(PROJECT_ROOT / '.env')

# API endpoints
NEWS_URL = "https://elite.finviz.com/news_export.ashx"
SCREENER_BASE_URL = "https://elite.finviz.com/export.ashx"

# File paths in data directory
NEWS_FILE = DATA_DIR / "news_data.csv"
SCREENER_FILE = DATA_DIR / "screener_data.csv"
OUTPUT_FILE = DATA_DIR / "finviz_news_and_stock_data.csv"
RSS_NEWS_FILE = DATA_DIR / "yahoo_rss_news_with_sentiment_analysis.csv"

# API Token
FINVIZ_API_TOKEN = os.getenv("FINVIZ_API_TOKEN")

# Screener filters
SCREENER_FILTERS = "v=152&p=i1&f=cap_0.001to&ft=4&o=-afterchange&ar=10&c=0,1,6,24,25,85,26,27,28,29,30,31,84,50,51,83,61,63,64,67,65,66,71,72"

def get_data_file_path(filename: str) -> Path:
    """
    Get the full path for a file in the data directory.
    
    Args:
        filename (str): Name of the file
        
    Returns:
        Path: Full path to the file in the data directory
    """
    return DATA_DIR / filename

def ensure_data_dir_exists():
    """Ensure the data directory exists"""
    DATA_DIR.mkdir(exist_ok=True)

def get_env_file_path() -> Path:
    """Get the path to the .env file in the project root"""
    return PROJECT_ROOT / '.env'

def list_data_files() -> list:
    """
    List all files in the data directory
    
    Returns:
        list: List of all files in the data directory
    """
    ensure_data_dir_exists()
    return [f.name for f in DATA_DIR.iterdir() if f.is_file()]

def clean_data_dir(pattern: str = None):
    """
    Remove files from the data directory.
    
    Args:
        pattern (str, optional): If provided, only remove files matching this pattern
    """
    ensure_data_dir_exists()
    for file in DATA_DIR.iterdir():
        if file.is_file():
            if pattern is None or pattern in file.name:
                file.unlink()

def get_project_root() -> Path:
    """
    Get the project root directory
    
    Returns:
        Path: Path to the project root directory
    """
    return PROJECT_ROOT

def validate_config():
    """
    Validate the configuration settings
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    if not FINVIZ_API_TOKEN:
        print("Warning: FINVIZ_API_TOKEN not set in environment variables")
        return False
    
    ensure_data_dir_exists()
    return True