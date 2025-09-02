import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time

# Page configuration
st.set_page_config(
    page_title="Global Index Tracker",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .positive-change {
        color: #28a745;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .negative-change {
        color: #dc3545;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .index-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .green-card {
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
    }
    .red-card {
        background: linear-gradient(135deg, #F44336 0%, #C62828 100%);
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class GlobalIndexTracker:
    def __init__(self):
        self.index_data = None
        self.historical_data = None
        self.index_info = {
            '^GSPC': {'name': 'S&P 500', 'region': 'USA', 'currency': 'USD'},
            '^DJI': {'name': 'Dow Jones Industrial Average', 'region': 'USA', 'currency': 'USD'},
            '^IXIC': {'name': 'NASDAQ Composite', 'region': 'USA', 'currency': 'USD'},
            '^N225': {'name': 'Nikkei 225', 'region': 'Japan', 'currency': 'JPY'},
            '^HSI': {'name': 'Hang Seng Index', 'region': 'Hong Kong', 'currency': 'HKD'},
            '^TPX': {'name': 'TOPIX', 'region': 'Japan', 'currency': 'JPY'},
            '000001.SS': {'name': 'Shanghai Composite', 'region': 'China', 'currency': 'CNY'},
            '399106.SZ': {'name': 'Shenzhen Composite', 'region': 'China', 'currency': 'CNY'},
            '000827.SS': {'name': 'CSI 300', 'region': 'China', 'currency': 'CNY'},
            '^FTSE': {'name': 'FTSE 100', 'region': 'UK', 'currency': 'GBP'},
            '^GDAXI': {'name': 'DAX', 'region': 'Germany', 'currency': 'EUR'},
            '^FCHI': {'name': 'CAC 40', 'region': 'France', 'currency': 'EUR'},
            '^AXJO': {'name': 'ASX 200', 'region': 'Australia', 'currency': 'AUD'},
            '^BSESN': {'name': 'BSE Sensex', 'region': 'India', 'currency': 'INR'},
            '^NSEI': {'name': 'Nifty 50', 'region': 'India', 'currency': 'INR'},
        }
    
    def fetch_index_data(self, symbols):
        """Fetch current data for multiple indices with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Fetch data for all symbols at once
                data = yf.download(
                    symbols, 
                    period="2d",  # Get 2 days to calculate change
                    group_by='ticker',
                    progress=False
                )
                
                results = []
                for symbol in symbols:
                    if symbol in data:
                        ticker_data = data[symbol]
                        if not ticker_data.empty and len(ticker_data) >= 2:
                            # Get current and previous day data
                            current_day = ticker_data.iloc[-1]
                            previous_day = ticker_data.iloc[-2]
                            
                            info = self.index_info.get(symbol, {'name': symbol, 'region': 'Unknown', 'currency': 'USD'})
                            
                            # Calculate changes
                            current_close = current_day['Close']
                            prev_close = previous_day['Close']
                            change = current_close - prev_close
                            change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
                            
                            results.append({
                                'Symbol': symbol,
                                'Name': info['name'],
                                'Region': info['region'],
                                'Currency': info['currency'],
                                'Price': current_close,
                                'Change': change,
                                'Change %': change_pct,
                                'Open': current_day['Open'],
                                'High': current_day['High'],
                                'Low': current_day['Low'],
                                'Volume': current_day['Volume']
                            })
                
                if results:
                    self.index_data = pd.DataFrame(results)
                    return True
                else:
                    st.warning(f"No data returned for symbols: {symbols}")
                    return False
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    st.error(f"Failed to fetch data after {max_retries} attempts: {str(e)}")
                    return False
                time.sleep(2)  # Wait before retrying
    
    def display_index_cards(self, filtered_data):
        """Display index performance cards"""
        if filtered_data.empty:
            st.warning("No indices match your filter criteria.")
            return
        
        st.subheader("📊 Index Performance Cards")
        
        # Create columns for the cards
        cols = st.columns(2)  # 2 cards per row
        
        for i, (_, index) in enumerate(filtered_data.iterrows()):
            col_idx = i % 2
            with cols[col_idx]:
                # Determine card color based on performance
                card_class = "green-card" if index['Change %'] > 0 else "red-card"
                if index['Change %'] == 0:
                    card_class = "index-card"
                
                change_icon = "📈" if index['Change %'] > 0 else "📉" if index['Change %'] < 0 else "➡️"
                
                st.markdown(f"""
                <div class="index-card {card_class}">
                    <h3>{index['Name']} ({index['Symbol']})</h3>
                    <p><strong>Region:</strong> {index['Region']} | <strong>Currency:</strong> {index['Currency']}</p>
                    <h2 class="metric-value">{index['Price']:,.2f}</h2>
                    <p class="{'positive-change' if index['Change %'] > 0 else 'negative-change'}">
                        {change_icon} {index['Change']:+.2f} ({index['Change %']:+.2f}%)
                    </p>
                    <p><strong>Daily Range:</strong> {index['Low']:,.2f} - {index['High']:,.2f}</p>
                    <p><strong>Open:</strong> {index['Open']:,.2f}</p>
                    <p><strong>Volume:</strong> {index['Volume']:,.0f if pd.notnull(index['Volume']) else 'N/A'}</p>
                </div>
                """, unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="main-header">🌍 Global Index Tracker</h1>', unsafe_allow_html=True)
    
    # Initialize tracker
    tracker = GlobalIndexTracker()
    
    # Default indices
    default_indices = [
        '^GSPC', '^DJI', '^IXIC', '^N225', '^HSI', 
        '^TPX', '000001.SS', '399106.SZ', '000827.SS'
    ]
    
    # Sidebar
    st.sidebar.header("Configuration")
    
    selected_indices = st.sidebar.multiselect(
        "Select indices to track:",
        options=list(tracker.index_info.keys()),
        default=default_indices
    )
    
    # Fetch data button
    if st.sidebar.button("🔄 Load Market Data", type="primary"):
        with st.spinner("Fetching latest market data..."):
            if tracker.fetch_index_data(selected_indices):
                st.sidebar.success("Data loaded successfully!")
            else:
                st.sidebar.error("Failed to load data. Please try again.")
    
    # If no data loaded yet, load default data
    if tracker.index_data is None:
        with st.spinner("Loading initial market data..."):
            tracker.fetch_index_data(default_indices)
    
    # Display data if available
    if tracker.index_data is not None:
        # Summary metrics
        st.subheader("📈 Market Overview")
        
        positive_count = len(tracker.index_data[tracker.index_data['Change %'] > 0])
        negative_count = len(tracker.index_data[tracker.index_data['Change %'] < 0])
        total_count = len(tracker.index_data)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Indices", total_count)
        with col2:
            st.metric("↗️ Advancing", positive_count, f"+{positive_count}")
        with col3:
            st.metric("↘️ Declining", negative_count, f"-{negative_count}")
        with col4:
            sentiment = "🟢 Bullish" if positive_count > negative_count else "🔴 Bearish" if negative_count > positive_count else "🟡 Neutral"
            st.metric("Market Sentiment", sentiment)
        
        # Filters
        st.subheader("🔍 Filter Indices")
        col1, col2 = st.columns(2)
        
        with col1:
            regions = st.multiselect(
                "Select Regions:",
                options=tracker.index_data['Region'].unique(),
                default=tracker.index_data['Region'].unique()
            )
        with col2:
            performance_filter = st.selectbox(
                "Show indices:",
                options=["All", "Gainers Only", "Losers Only", "No Change"]
            )
        
        # Apply filters
        filtered_data = tracker.index_data[tracker.index_data['Region'].isin(regions)]
        
        if performance_filter == "Gainers Only":
            filtered_data = filtered_data[filtered_data['Change %'] > 0]
        elif performance_filter == "Losers Only":
            filtered_data = filtered_data[filtered_data['Change %'] < 0]
        elif performance_filter == "No Change":
            filtered_data = filtered_data[filtered_data['Change %'] == 0]
        
        # Display index cards
        tracker.display_index_cards(filtered_data)
        
        # Detailed table
        st.subheader("📋 Detailed Performance Table")
        
        if not filtered_data.empty:
            # Format the display table
            display_df = filtered_data.copy()
            display_df['Price'] = display_df['Price'].apply(lambda x: f"{x:,.2f}")
            display_df['Change'] = display_df['Change'].apply(lambda x: f"{x:+.2f}")
            display_df['Change %'] = display_df['Change %'].apply(lambda x: f"{x:+.2f}%")
            display_df['Volume'] = display_df['Volume'].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "N/A")
            
            st.dataframe(
                display_df[[
                    'Symbol', 'Name', 'Region', 'Currency', 'Price', 
                    'Change', 'Change %', 'Volume'
                ]],
                use_container_width=True,
                height=400
            )
        else:
            st.info("No indices match your current filters.")
    
    else:
        st.error("Failed to load market data. Please try refreshing the page or check your internet connection.")

if __name__ == "__main__":
    main()
