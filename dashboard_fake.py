import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
from dotenv import load_dotenv
from pathlib import Path
import os
from dummy_data_generator import generate_dummy_data

# Set page config
st.set_page_config(
    page_title="Financial Sentiment Dashboard",
    page_icon="📈",
    layout="wide"
)

def load_env_api_token():
    """Load API token from .env file"""
    load_dotenv()
    return os.getenv('FINVIZ_API_TOKEN', '')

def save_api_token(api_token):
    """Save API token to .env file"""
    env_path = Path('.env')
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        token_found = False
        for i, line in enumerate(lines):
            if line.startswith('FINVIZ_API_TOKEN='):
                lines[i] = f'FINVIZ_API_TOKEN={api_token}\n'
                token_found = True
                break
        
        if not token_found:
            lines.append(f'FINVIZ_API_TOKEN={api_token}\n')
        
        with open(env_path, 'w') as f:
            f.writelines(lines)
    else:
        with open(env_path, 'w') as f:
            f.write(f'FINVIZ_API_TOKEN={api_token}\n')
    
    return True

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'api_token' not in st.session_state:
    st.session_state.api_token = load_env_api_token()
if 'using_dummy_data' not in st.session_state:
    st.session_state.using_dummy_data = False

def load_and_process_data(api_token=None, use_dummy=False):
    """Load either real or dummy data"""
    if use_dummy:
        st.session_state.using_dummy_data = True
        return generate_dummy_data()
    
    try:
        # Your actual data loading code here
        # For now, we'll use dummy data
        st.warning("API integration not yet implemented. Using dummy data instead.")
        st.session_state.using_dummy_data = True
        return generate_dummy_data()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# Sidebar for configuration
with st.sidebar:
    st.title("Configuration")
    
    # API Token Management section
    st.subheader("API Token Management")
    
    if st.session_state.api_token:
        st.success("API Token is configured")
    else:
        st.warning("No API Token found")
    
    show_api_token = st.checkbox("Update API Token")
    
    if show_api_token:
        new_api_token = st.text_input(
            "Enter new API Token",
            value=st.session_state.api_token,
            type="password"
        )
        
        if st.button("Save API Token"):
            if new_api_token:
                if save_api_token(new_api_token):
                    st.session_state.api_token = new_api_token
                    st.success("API Token saved successfully!")
                    st.rerun()
                else:
                    st.error("Failed to save API Token")
            else:
                st.error("Please enter an API Token")
    
    # Data loading options
    st.subheader("Data Options")
    use_dummy = st.checkbox("Use Demo Data", value=not bool(st.session_state.api_token))
    
    if st.button("Load Data"):
        with st.spinner("Loading data..."):
            st.session_state.data = load_and_process_data(
                st.session_state.api_token,
                use_dummy=use_dummy
            )

# Main dashboard
st.title("Financial Sentiment Analysis Dashboard")

if st.session_state.using_dummy_data:
    st.info("Currently using demo data. Configure API token for real-time data.")

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
    if not st.session_state.api_token and not st.session_state.using_dummy_data:
        st.info("Please configure your FinViz API token in the sidebar or use demo data to proceed.")
    else:
        st.info("Click 'Load Data' in the sidebar to start analyzing.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>Financial Sentiment Analysis Dashboard | Data updates every market day</p>
        {}</p>
    </div>
    """.format(
        "Using Demo Data" if st.session_state.using_dummy_data else "Using Live Data"
    ),
    unsafe_allow_html=True
)