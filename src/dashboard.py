import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
import subprocess
from dotenv import load_dotenv, set_key


# Get the directory where the dashboard script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

# Set page config
st.set_page_config(
    page_title="Financial News Sentiment Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

# Initialize session state variables
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None
if 'next_refresh' not in st.session_state:
    st.session_state.next_refresh = None
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 5
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = False

    
def save_api_token(token):
    """Save the FINVIZ API token to .env file"""
    env_path = SCRIPT_DIR / '.env'
    if not env_path.exists():
        env_path.touch()
    
    set_key(str(env_path), 'FINVIZ_API_TOKEN', token)
    st.success("API token saved successfully!")
    os.environ['FINVIZ_API_TOKEN'] = token

def run_data_updates():
    """Run the main.py and RSS feed analyzer scripts"""
    try:
        main_script = SCRIPT_DIR / 'main.py'
        rss_script = SCRIPT_DIR / 'rss feed with sentiment analyzers.py'
        
        if not main_script.exists():
            st.error(f"Cannot find main.py in {SCRIPT_DIR}")
            return False
        if not rss_script.exists():
            st.error(f"Cannot find rss feed with sentiment analyzers.py in {SCRIPT_DIR}")
            return False
        
        subprocess.run(['python', str(main_script)], 
                      check=True, 
                      cwd=str(SCRIPT_DIR))
        subprocess.run(['python', str(rss_script)], 
                      check=True,
                      cwd=str(SCRIPT_DIR))
        
        # Update last refresh time and calculate next refresh time
        st.session_state.last_refresh = datetime.now()
        st.session_state.next_refresh = st.session_state.last_refresh + timedelta(minutes=st.session_state.refresh_interval)
        return True
    except Exception as e:
        st.error(f"Error running updates: {str(e)}")
        return False
    
def load_demo_data():
    """Generate and load demo data"""
    try:
        from dummy_data_generator import generate_dummy_data
        sentiment_df, screener_df = generate_dummy_data()
        
        # Merge the dataframes
        merged_df = pd.merge(
            sentiment_df,
            screener_df[['Ticker', 'Relative Volume']],
            left_on='ticker',
            right_on='Ticker',
            how='left'
        )
        
        # Clean up columns
        merged_df.drop('Ticker', axis=1, inplace=True)
        merged_df['Relative Volume'] = merged_df['Relative Volume'].fillna(1.0)
        
        return merged_df
    except Exception as e:
        st.error(f"Error loading demo data: {str(e)}")
        return None

def check_auto_refresh():
    """Check if it's time to refresh based on the interval"""
    if st.session_state.auto_refresh and st.session_state.next_refresh:
        if datetime.now() >= st.session_state.next_refresh:
            with st.spinner("Auto-refreshing data..."):
                if run_data_updates():
                    st.rerun()

def load_data():
    """Load data with proper path handling"""
    if st.session_state.demo_mode:
        return load_demo_data()
    
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
    
    # Demo mode toggle
    demo_mode = st.checkbox("Demo Mode", value=st.session_state.demo_mode)
    if demo_mode != st.session_state.demo_mode:
        st.session_state.demo_mode = demo_mode
        st.rerun()
    
    if not st.session_state.demo_mode:
        # Regular mode settings
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
        
        # Auto-refresh settings (only show in regular mode)
        st.subheader("Auto-refresh Settings")
        st.session_state.refresh_interval = st.selectbox(
            "Refresh Interval",
            options=[5, 10, 20, 30],
            format_func=lambda x: f"Every {x} minutes"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Auto-refresh"):
                st.session_state.auto_refresh = True
                st.session_state.last_refresh = datetime.now()
                st.session_state.next_refresh = st.session_state.last_refresh + timedelta(minutes=st.session_state.refresh_interval)
                st.success(f"Auto-refresh started ({st.session_state.refresh_interval} min)")
        
        with col2:
            if st.button("Stop Auto-refresh"):
                st.session_state.auto_refresh = False
                st.session_state.next_refresh = None
                st.success("Auto-refresh stopped")
        
        # Manual refresh button
        if st.button("Refresh Now"):
            with st.spinner("Updating data..."):
                if run_data_updates():
                    st.success("Data updated successfully!")
                    st.rerun()

        # Display auto-refresh status
        if st.session_state.auto_refresh:
            st.info(f"Auto-refresh is active ({st.session_state.refresh_interval} min interval)")
            if st.session_state.next_refresh:
                st.write("Next refresh at:", st.session_state.next_refresh.strftime("%I:%M:%S %p"))
    else:
        st.info("Demo mode active - using generated data")
        if st.button("Regenerate Demo Data"):
            st.rerun()

# Check for auto-refresh at the start of each run
check_auto_refresh()

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
        
        # Calculate the maximum absolute values for both axes to make plot symmetric
        max_sentiment = max(abs(filtered_data[sentiment_column].min()), 
                          abs(filtered_data[sentiment_column].max()))
        max_price = max(abs(filtered_data['price_change'].min()), 
                       abs(filtered_data['price_change'].max()))
        
        # Create scatter plot with quadrant lines
        fig = px.scatter(
            filtered_data,
            x=sentiment_column,
            y="price_change",
            color="ticker",
            size="Relative Volume",
            hover_data=['title', 'publish_time', 'Relative Volume'],
            title=f"Trend vs {selected_sentiment} (Size indicates Relative Volume)",
            labels={
                sentiment_column: selected_sentiment,
                'price_change': 'Price Trend ($)',
                'ticker': 'Ticker',
                'Relative Volume': 'Relative Volume'
            }
        )
        
        # Update layout with contrasting center lines
        fig.update_layout(
            showlegend=True,
            height=600,
            xaxis=dict(
                zeroline=False,  # We'll add our own zero line
                range=[-max_sentiment * 1.1, max_sentiment * 1.1],
                gridcolor='rgba(128,128,128,0.2)',  # Subtle grid
                title=selected_sentiment
            ),
            yaxis=dict(
                zeroline=False,  # We'll add our own zero line
                range=[-max_price * 1.1, max_price * 1.1],
                gridcolor='rgba(128,128,128,0.2)',  # Subtle grid
                title="Price Trend ($)"
            ),
            shapes=[
                # Vertical line at x=0
                dict(
                    type='line',
                    x0=0, x1=0,
                    y0=-max_price * 1.1,
                    y1=max_price * 1.1,
                    line=dict(
                        color='rgb(255, 195, 0)',  # Bright gold
                        width=2  # Thicker line
                    )
                ),
                # Horizontal line at y=0
                dict(
                    type='line',
                    x0=-max_sentiment * 1.1,
                    x1=max_sentiment * 1.1,
                    y0=0, y1=0,
                    line=dict(
                        color='rgb(255, 195, 0)',  # Bright gold
                        width=2  # Thicker line
                    )
                )
            ],
            # Add quadrant labels
            annotations=[
                dict(
                    x=max_sentiment * 0.9,
                    y=max_price * 0.9,
                    text="Positive Sentiment<br>Price Increase",
                    showarrow=False,
                    font=dict(size=10, color='rgba(255,255,255,0.8)'),
                    align='center'
                ),
                dict(
                    x=-max_sentiment * 0.9,
                    y=max_price * 0.9,
                    text="Negative Sentiment<br>Price Increase",
                    showarrow=False,
                    font=dict(size=10, color='rgba(255,255,255,0.8)'),
                    align='center'
                ),
                dict(
                    x=max_sentiment * 0.9,
                    y=-max_price * 0.9,
                    text="Positive Sentiment<br>Price Decrease",
                    showarrow=False,
                    font=dict(size=10, color='rgba(255,255,255,0.8)'),
                    align='center'
                ),
                dict(
                    x=-max_sentiment * 0.9,
                    y=-max_price * 0.9,
                    text="Negative Sentiment<br>Price Decrease",
                    showarrow=False,
                    font=dict(size=10, color='rgba(255,255,255,0.8)'),
                    align='center'
                )
            ]
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