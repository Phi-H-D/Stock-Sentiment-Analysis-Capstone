import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np
from pathlib import Path
import time
import schedule
import threading
from queue import Queue
import subprocess
import os
from dotenv import load_dotenv, set_key

# Get the directory where the dashboard script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

# Set page config
st.set_page_config(
    page_title="Financial News Sentiment Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'refresh_thread' not in st.session_state:
    st.session_state.refresh_thread = None
if 'stop_refresh' not in st.session_state:
    st.session_state.stop_refresh = False

def save_api_token(token):
    """Save the FINVIZ API token to .env file"""
    env_path = SCRIPT_DIR / '.env'
    if not env_path.exists():
        env_path.touch()
    
    set_key(str(env_path), 'FINVIZ_API_TOKEN', token)
    st.success("API token saved successfully!")
    # Ensure the token is immediately available to child processes
    os.environ['FINVIZ_API_TOKEN'] = token

def run_data_updates():
    """Run the main.py and RSS feed analyzer scripts"""
    try:
        # Construct full paths to scripts
        main_script = SCRIPT_DIR / 'main.py'
        rss_script = SCRIPT_DIR / 'rss feed with sentiment analyzers.py'
        
        # Check if scripts exist
        if not main_script.exists():
            st.error(f"Cannot find main.py in {SCRIPT_DIR}")
            return False
        if not rss_script.exists():
            st.error(f"Cannot find rss feed with sentiment analyzers.py in {SCRIPT_DIR}")
            return False
        
        # Run scripts with correct working directory
        subprocess.run(['python', str(main_script)], 
                      check=True, 
                      cwd=str(SCRIPT_DIR))
        subprocess.run(['python', str(rss_script)], 
                      check=True,
                      cwd=str(SCRIPT_DIR))
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Error running updates: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return False

def auto_refresh(interval_minutes):
    """Background thread for auto-refresh"""
    while not st.session_state.stop_refresh:
        if run_data_updates():
            st.experimental_rerun()
        time.sleep(interval_minutes * 60)

def start_auto_refresh(interval_minutes):
    """Start the auto-refresh thread"""
    if st.session_state.refresh_thread is not None:
        st.session_state.stop_refresh = True
        st.session_state.refresh_thread.join()
    
    st.session_state.stop_refresh = False
    st.session_state.refresh_thread = threading.Thread(
        target=auto_refresh,
        args=(interval_minutes,)
    )
    st.session_state.refresh_thread.start()

def stop_auto_refresh():
    """Stop the auto-refresh thread"""
    if st.session_state.refresh_thread is not None:
        st.session_state.stop_refresh = True
        st.session_state.refresh_thread.join()
        st.session_state.refresh_thread = None

def load_data():
    """Load data with proper path handling"""
    try:
        # Use correct paths for data files
        sentiment_path = SCRIPT_DIR / 'yahoo_rss_news_with_sentiment_analysis.csv'
        screener_path = SCRIPT_DIR / 'screener_data.csv'
        
        if not sentiment_path.exists():
            st.error(f"Cannot find sentiment data file at {sentiment_path}")
            return None
        if not screener_path.exists():
            st.error(f"Cannot find screener data file at {screener_path}")
            return None
        
        # Load RSS sentiment data
        sentiment_df = pd.read_csv(sentiment_path)
        sentiment_df['ticker'] = sentiment_df['ticker'].str.strip('"\'')
        sentiment_df['price_change'] = sentiment_df['price_after'] - sentiment_df['price_at_news']
        
        # Load screener data
        screener_df = pd.read_csv(screener_path)
        screener_df = screener_df.rename(columns={'Ticker': 'TICKER'})
        screener_df['TICKER'] = screener_df['TICKER'].str.strip('"\'')
        
        # Clean screener data
        screener_df['Relative Volume'] = pd.to_numeric(screener_df['Relative Volume'], errors='coerce')
        
        # Merge the dataframes
        merged_df = pd.merge(
            sentiment_df,
            screener_df[['TICKER', 'Relative Volume']],
            left_on='ticker',
            right_on='TICKER',
            how='left'
        )
        
        merged_df.drop('TICKER', axis=1, inplace=True)
        merged_df['Relative Volume'] = merged_df['Relative Volume'].fillna(1.0)
        
        return merged_df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        print(f"Detailed error: {str(e)}")
        return None

# Sidebar settings
with st.sidebar:
    st.header("Settings")
    
    # Display current script directory
    st.text(f"Working directory:\n{SCRIPT_DIR}")
    
    # API Token Management
    st.subheader("API Token Management")
    load_dotenv(SCRIPT_DIR / '.env')
    current_token = os.getenv('FINVIZ_API_TOKEN', '')
    
    if current_token:
        st.write("Current token: " + "*" * len(current_token))
    
    new_token = st.text_input("Enter new FINVIZ API token", type="password")
    if st.button("Save Token"):
        save_api_token(new_token)
    
    # Auto-refresh settings
    st.subheader("Auto-refresh Settings")
    refresh_interval = st.selectbox(
        "Refresh Interval",
        options=[5, 10, 20, 30],
        format_func=lambda x: f"Every {x} minutes"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Auto-refresh"):
            start_auto_refresh(refresh_interval)
            st.success(f"Auto-refresh started ({refresh_interval} min)")
    
    with col2:
        if st.button("Stop Auto-refresh"):
            stop_auto_refresh()
            st.success("Auto-refresh stopped")
    
    # Manual refresh button
    if st.button("Refresh Now"):
        with st.spinner("Updating data..."):
            if run_data_updates():
                st.success("Data updated successfully!")
                st.rerun()

    # Display auto-refresh status
    if st.session_state.refresh_thread is not None:
        st.info(f"Auto-refresh is active ({refresh_interval} min interval)")

def format_sentiment(val):
    if pd.isna(val):
        return ""
    return f"{val:.3f}"

def format_volume(val):
    if pd.isna(val):
        return ""
    return f"{val:.1f}x"

# Main dashboard layout
st.title("Financial News Sentiment Analysis Dashboard")

# Create tabs
tab1, tab2 = st.tabs(["Sentiment Analysis", "Price Analysis"])

with tab1:
    st.header("News Sentiment Analysis")

    # Load the merged data
    data = load_data()
    
    if data is not None:
        # Filter options with three columns
        col1, col2, col3 = st.columns(3)
        with col1:
            # Pre-select all tickers by default
            all_tickers = sorted(data['ticker'].unique())
            selected_tickers = st.multiselect(
                "Select Tickers",
                options=all_tickers,
                default=all_tickers
            )
        
        with col2:
            min_sentiment = st.slider(
                "Minimum Aggregate Body Sentiment",
                min_value=-1.0,
                max_value=1.0,
                value=-1.0,
                step=0.1
            )
        
        with col3:
            min_volume = st.number_input(
                "Minimum Relative Volume",
                min_value=0.0,
                max_value=float(data['Relative Volume'].max()),
                value=0.0,
                step=0.1,
                format="%.1f"
            )
        
        # Filter data with added volume filter
        filtered_data = data[
            (data['ticker'].isin(selected_tickers)) &
            (data['aggregate_body_sentiment'] >= min_sentiment) &
            (data['Relative Volume'] >= min_volume)
        ]
        
        if not filtered_data.empty:
            # Select columns to display
            display_columns = [
                'ticker',
                'publish_time',
                'title',
                'Relative Volume',
                'nltk_body_sentiment',
                'finvader_body_sentiment',
                'finbert_body_sentiment',
                'aggregate_body_sentiment',
                'price_change'
            ]
            
            # Create display DataFrame
            display_df = filtered_data[display_columns].copy()
            
            # Format datetime
            display_df['publish_time'] = pd.to_datetime(display_df['publish_time']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Format sentiment columns
            sentiment_columns = [
                'nltk_body_sentiment',
                'finvader_body_sentiment',
                'finbert_body_sentiment',
                'aggregate_body_sentiment'
            ]
            
            # Create a copy for display that includes the link column for making titles clickable
            display_df_with_links = display_df.copy()
            
            # Format numeric columns
            for col in sentiment_columns:
                display_df_with_links[col] = display_df_with_links[col].apply(lambda x: float(x) if pd.notnull(x) else None)
                display_df[col] = display_df[col].apply(format_sentiment)
            
            display_df_with_links['price_change'] = display_df_with_links['price_change'].apply(lambda x: float(x) if pd.notnull(x) else None)
            display_df['price_change'] = display_df['price_change'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
            
            display_df_with_links['Relative Volume'] = display_df_with_links['Relative Volume'].apply(lambda x: float(x) if pd.notnull(x) else None)
            display_df['Relative Volume'] = display_df['Relative Volume'].apply(format_volume)
            
            # Create column configuration for st.dataframe
            column_config = {
                "ticker": "Ticker",
                "publish_time": "Publish Time",
                "title": st.column_config.LinkColumn(
                    "Title",
                    help="Click to read the article",
                    width="medium",
                ),
                "Relative Volume": st.column_config.NumberColumn(
                    "Relative Volume",
                    help="Trading volume relative to average",
                    format="%.1f"
                ),
                "nltk_body_sentiment": st.column_config.NumberColumn(
                    "NLTK Sentiment",
                    help="NLTK sentiment score",
                    format="%.3f"
                ),
                "finvader_body_sentiment": st.column_config.NumberColumn(
                    "FinVADER Sentiment",
                    help="FinVADER sentiment score",
                    format="%.3f"
                ),
                "finbert_body_sentiment": st.column_config.NumberColumn(
                    "FinBERT Sentiment",
                    help="FinBERT sentiment score",
                    format="%.3f"
                ),
                "aggregate_body_sentiment": st.column_config.NumberColumn(
                    "Aggregate Sentiment",
                    help="Average of all sentiment scores",
                    format="%.3f"
                ),
                "price_change": st.column_config.NumberColumn(
                    "Price Change",
                    help="Change in price after news",
                    format="$%.2f"
                ),
            }
            
            # Create the links for titles
            display_df_with_links['title'] = filtered_data.apply(
                lambda x: x['link'],
                axis=1
            )
            
            # Display the sortable dataframe
            st.write("News Sentiment Analysis Results")
            st.dataframe(
                display_df_with_links,
                column_config=column_config,
                hide_index=True,
                use_container_width=True
            )
            
            # Add download button
            csv = filtered_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Data as CSV",
                data=csv,
                file_name="sentiment_analysis_data.csv",
                mime="text/csv",
            )
            
            # Display summary statistics
            st.subheader("Summary Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_sentiment = filtered_data['aggregate_body_sentiment'].mean()
                st.metric(
                    "Average Sentiment",
                    f"{avg_sentiment:.3f}",
                    delta=None
                )
            
            with col2:
                avg_price_change = filtered_data['price_change'].mean()
                st.metric(
                    "Average Price Change",
                    f"${avg_price_change:.2f}",
                    delta=f"{(avg_price_change/filtered_data['price_at_news'].mean()*100):.1f}%"
                )
            
            with col3:
                avg_volume = filtered_data['Relative Volume'].mean()
                st.metric(
                    "Average Relative Volume",
                    f"{avg_volume:.1f}",
                    delta=None
                )
            
            with col4:
                total_articles = len(filtered_data)
                st.metric(
                    "Total Articles",
                    total_articles,
                    delta=None
                )
        if filtered_data.empty:
            st.warning("No data available for the selected filters. Try adjusting the Relative Volume, Sentiment, or Ticker selections.")
    else:
        st.error("Unable to load data. Please check if the required CSV files exist.")

with tab2:
    st.header("Trend vs Sentiment Analysis")

    if data is not None and not filtered_data.empty:
        # Sentiment type selector
        sentiment_options = {
            'NLTK Sentiment': 'nltk_body_sentiment',
            'FinVADER Sentiment': 'finvader_body_sentiment',
            'FinBERT Sentiment': 'finbert_body_sentiment',
            'Aggregate Sentiment': 'aggregate_body_sentiment'
        }
        
        selected_sentiment = st.selectbox(
            "Select Sentiment Analysis Type",
            options=list(sentiment_options.keys())
        )
        
        sentiment_column = sentiment_options[selected_sentiment]
        
        # Create scatter plot with size based on relative volume
        fig = px.scatter(
            filtered_data,
            x=sentiment_column,
            y="price_change",
            color="ticker",
            size="Relative Volume",  # Size based on relative volume
            hover_data=['title', 'publish_time', 'Relative Volume'],
            title=f"Trend vs {selected_sentiment} (Size indicates Relative Volume)",
            labels={
                sentiment_column: selected_sentiment,
                'price_change': 'Price Trend ($)',
                'ticker': 'Ticker',
                'Relative Volume': 'Relative Volume'
            }
        )
        
        fig.update_layout(
            showlegend=True,
            height=600,
            xaxis_title=selected_sentiment,
            yaxis_title="Price Trend ($)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Calculate and display correlation
        correlation = filtered_data[sentiment_column].corr(filtered_data['price_change'])
        st.metric(
            f"Correlation: {selected_sentiment} vs Price Trend",
            f"{correlation:.3f}",
            delta=None
        )
        
        # Additional analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment distribution
            positive_count = len(filtered_data[filtered_data[sentiment_column] > 0.2])
            negative_count = len(filtered_data[filtered_data[sentiment_column] < -0.2])
            neutral_count = len(filtered_data) - positive_count - negative_count
            
            sentiment_distribution = pd.DataFrame({
                'Sentiment': ['Positive', 'Neutral', 'Negative'],
                'Count': [positive_count, neutral_count, negative_count]
            })
            
            fig_sentiment = px.pie(
                sentiment_distribution,
                values='Count',
                names='Sentiment',
                title=f'{selected_sentiment} Distribution'
            )
            st.plotly_chart(fig_sentiment)
        
        with col2:
            # Volume-weighted sentiment analysis
            volume_weighted_sentiment = (
                filtered_data[sentiment_column] * filtered_data['Relative Volume']
            ).mean() / filtered_data['Relative Volume'].mean()
            
            st.metric(
                "Volume-Weighted Sentiment",
                f"{volume_weighted_sentiment:.3f}",
                delta=f"{volume_weighted_sentiment - filtered_data[sentiment_column].mean():.3f} vs unweighted"
            )
            
            # High volume impact
            high_volume_sentiment = filtered_data[
                filtered_data['Relative Volume'] > filtered_data['Relative Volume'].median()
            ][sentiment_column].mean()
            
            st.metric(
                "High Volume Sentiment (Above Median)",
                f"{high_volume_sentiment:.3f}",
                delta=None
            )