import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import yfinance as yf
import numpy as np
from data_fetcher import export_news_data, export_screener_data, load_data
from data_processor import process_news_data, merge_data, calculate_trends, prepare_final_data
from price_fetcher import fetch_current_prices
import os
from dotenv import load_dotenv
from pathlib import Path

# Set page config
st.set_page_config(
    page_title="Financial Sentiment Dashboard",
    page_icon="📈",
    layout="wide"
)

def load_env_api_key():
    """Load API key from .env file"""
    load_dotenv()
    return os.getenv('FINVIZ_API_KEY', '')

def save_api_key(api_key):
    """Save API key to .env file"""
    env_path = Path('.env')
    
    if env_path.exists():
        # Read existing environment variables
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update or add FINVIZ_API_KEY
        api_key_found = False
        for i, line in enumerate(lines):
            if line.startswith('FINVIZ_API_KEY='):
                lines[i] = f'FINVIZ_API_KEY={api_key}\n'
                api_key_found = True
                break
        
        if not api_key_found:
            lines.append(f'FINVIZ_API_KEY={api_key}\n')
        
        # Write back to file
        with open(env_path, 'w') as f:
            f.writelines(lines)
    else:
        # Create new .env file
        with open(env_path, 'w') as f:
            f.write(f'FINVIZ_API_KEY={api_key}\n')
    
    return True

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = load_env_api_key()

def load_and_process_data(api_token):
    """Load and process data with the provided API token"""
    os.environ['FINVIZ_API_KEY'] = api_token
    
    # Fetch initial data
    news_data = export_news_data()
    screener_data = export_screener_data()
    
    if news_data is None or screener_data is None:
        st.error("Failed to fetch data. Please check your API token.")
        return None
    
    # Process data
    news_data = process_news_data(news_data)
    merged_data = merge_data(news_data, screener_data)
    
    # Fetch current prices
    unique_tickers = merged_data['Ticker'].unique()
    current_prices = fetch_current_prices(unique_tickers)
    
    # Calculate trends
    final_data = calculate_trends(merged_data, current_prices)
    return prepare_final_data(final_data)

# Sidebar for API Token management
with st.sidebar:
    st.title("Configuration")
    
    # API Key Management section
    st.subheader("API Key Management")
    
    # Show current API key status
    if st.session_state.api_key:
        st.success("API Key is configured")
    else:
        st.warning("No API Key found")
    
    # Option to update API key
    show_api_key = st.checkbox("Update API Key")
    
    if show_api_key:
        new_api_key = st.text_input(
            "Enter new API Key",
            value=st.session_state.api_key,
            type="password"
        )
        
        if st.button("Save API Key"):
            if new_api_key:
                if save_api_key(new_api_key):
                    st.session_state.api_key = new_api_key
                    st.success("API Key saved successfully!")
                    st.rerun()
                else:
                    st.error("Failed to save API Key")
            else:
                st.error("Please enter an API Key")
    
    # Load data button
    if st.button("Load Data"):
        if st.session_state.api_key:
            with st.spinner("Loading data..."):
                st.session_state.data = load_and_process_data(st.session_state.api_key)
        else:
            st.error("Please configure your API key first")

# Main dashboard
st.title("Financial Sentiment Analysis Dashboard")

if st.session_state.data is not None:
    # Create tabs
    tab1, tab2 = st.tabs(["Data View", "Sentiment Analysis"])
    
    with tab1:
        st.header("Stock Data and Sentiments")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            selected_tickers = st.multiselect(
                "Select Tickers",
                options=sorted(st.session_state.data['Ticker'].unique()),
                default=sorted(st.session_state.data['Ticker'].unique())[:5]
            )
        
        # Filter data
        filtered_data = st.session_state.data[
            st.session_state.data['Ticker'].isin(selected_tickers)
        ]
        
        # Display data table
        st.dataframe(
            filtered_data[[
                'Ticker', 'News URL', 'NLTK Sentiment', 
                'FinBERT Sentiment', 'FinVADER Sentiment',
                'Trend Analysis', 'Relative Volume'
            ]],
            hide_index=True,
            use_container_width=True
        )
    
    with tab2:
        st.header("Sentiment vs Trend Analysis")
        
        # Sentiment selection dropdown
        sentiment_option = st.selectbox(
            "Select Sentiment Metric",
            ["NLTK Sentiment", "FinBERT Sentiment", "FinVADER Sentiment"]
        )
        
        # Create scatter plot
        fig = px.scatter(
            filtered_data,
            x="Trend Analysis",
            y=sentiment_option,
            size="Relative Volume",
            color="Ticker",
            hover_data=['Ticker', 'Trend Analysis', sentiment_option, 'Relative Volume'],
            title=f"{sentiment_option} vs Trend Analysis",
        )
        
        fig.update_layout(
            xaxis_title="Trend Analysis (%)",
            yaxis_title=sentiment_option,
            showlegend=True,
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Additional statistics
        st.subheader("Summary Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Average Sentiment",
                f"{filtered_data[sentiment_option].mean():.2f}"
            )
        
        with col2:
            st.metric(
                "Average Trend",
                f"{filtered_data['Trend Analysis'].mean():.2f}%"
            )
        
        with col3:
            st.metric(
                "Average Relative Volume",
                f"{filtered_data['Relative Volume'].mean():.2f}x"
            )
else:
    if not st.session_state.api_key:
        st.info("Please configure your FinViz API token in the sidebar to proceed.")
    else:
        st.info("Click 'Load Data' in the sidebar to start analyzing.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>Financial Sentiment Analysis Dashboard | Data updates every market day</p>
    </div>
    """,
    unsafe_allow_html=True
)