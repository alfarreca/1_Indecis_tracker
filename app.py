import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from io import BytesIO

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
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1E88E5;
        margin-bottom: 1rem;
    }
    .positive-change {
        color: #28a745;
        font-weight: bold;
    }
    .negative-change {
        color: #dc3545;
        font-weight: bold;
    }
    .index-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
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
            '^SPX': {'name': 'S&P 500 (Alternative)', 'region': 'USA', 'currency': 'USD'},
            '000001.SS': {'name': 'Shanghai Composite', 'region': 'China', 'currency': 'CNY'},
            '399106.SZ': {'name': 'Shenzhen Composite', 'region': 'China', 'currency': 'CNY'},
            '000827.SS': {'name': 'CSI 300', 'region': 'China', 'currency': 'CNY'},
            'TXGM.TS': {'name': 'TSX Composite', 'region': 'Canada', 'currency': 'CAD'},
            '^FTSE': {'name': 'FTSE 100', 'region': 'UK', 'currency': 'GBP'},
            '^GDAXI': {'name': 'DAX', 'region': 'Germany', 'currency': 'EUR'},
            '^FCHI': {'name': 'CAC 40', 'region': 'France', 'currency': 'EUR'},
            '^STOXX50E': {'name': 'Euro Stoxx 50', 'region': 'Europe', 'currency': 'EUR'},
            '^AXJO': {'name': 'ASX 200', 'region': 'Australia', 'currency': 'AUD'},
            '^BSESN': {'name': 'BSE Sensex', 'region': 'India', 'currency': 'INR'},
            '^NSEI': {'name': 'Nifty 50', 'region': 'India', 'currency': 'INR'},
            '^KS11': {'name': 'KOSPI', 'region': 'South Korea', 'currency': 'KRW'},
            '^TWII': {'name': 'Taiwan Weighted', 'region': 'Taiwan', 'currency': 'TWD'},
        }
    
    def fetch_index_data(self, symbols, period="1d"):
        """Fetch current data for multiple indices"""
        try:
            data = yf.download(symbols, period=period, group_by='ticker')
            
            results = []
            for symbol in symbols:
                if symbol in data:
                    ticker_data = data[symbol]
                    if not ticker_data.empty:
                        last_row = ticker_data.iloc[-1]
                        info = self.index_info.get(symbol, {'name': symbol, 'region': 'Unknown', 'currency': 'USD'})
                        
                        # Calculate daily change
                        if len(ticker_data) > 1:
                            prev_close = ticker_data.iloc[-2]['Close']
                            current_close = last_row['Close']
                            change = current_close - prev_close
                            change_pct = (change / prev_close) * 100
                        else:
                            change = 0
                            change_pct = 0
                        
                        results.append({
                            'Symbol': symbol,
                            'Name': info['name'],
                            'Region': info['region'],
                            'Currency': info['currency'],
                            'Price': current_close,
                            'Change': change,
                            'Change %': change_pct,
                            'Open': last_row['Open'],
                            'High': last_row['High'],
                            'Low': last_row['Low'],
                            'Volume': last_row['Volume']
                        })
            
            self.index_data = pd.DataFrame(results)
            return True
            
        except Exception as e:
            st.error(f"Error fetching index data: {str(e)}")
            return False
    
    def fetch_historical_data(self, symbols, period="1y"):
        """Fetch historical data for charts"""
        try:
            data = yf.download(symbols, period=period, group_by='ticker')
            self.historical_data = data
            return True
        except Exception as e:
            st.error(f"Error fetching historical data: {str(e)}")
            return False
    
    def calculate_technical_indicators(self, symbol_data):
        """Calculate basic technical indicators"""
        if symbol_data.empty:
            return {}
        
        closes = symbol_data['Close']
        
        # Simple Moving Averages
        sma_20 = closes.rolling(window=20).mean().iloc[-1]
        sma_50 = closes.rolling(window=50).mean().iloc[-1]
        sma_200 = closes.rolling(window=200).mean().iloc[-1]
        
        # RSI
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        return {
            'SMA_20': sma_20,
            'SMA_50': sma_50,
            'SMA_200': sma_200,
            'RSI': rsi
        }
    
    def display_dashboard(self):
        """Display the main dashboard"""
        if self.index_data is None:
            return
        
        # Summary metrics
        st.subheader("🌍 Global Market Overview")
        
        # Overall market sentiment
        positive_count = len(self.index_data[self.index_data['Change %'] > 0])
        negative_count = len(self.index_data[self.index_data['Change %'] < 0])
        total_count = len(self.index_data)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Indices", total_count)
        with col2:
            st.metric("↗️ Advancing", positive_count)
        with col3:
            st.metric("↘️ Declining", negative_count)
        with col4:
            sentiment = "🟢 Bullish" if positive_count > negative_count else "🔴 Bearish" if negative_count > positive_count else "🟡 Neutral"
            st.metric("Market Sentiment", sentiment)
        
        # Filters
        st.subheader("Filter Indices")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            regions = st.multiselect("Regions", self.index_data['Region'].unique(), default=self.index_data['Region'].unique())
        with col2:
            min_change = st.slider("Min Change %", -5.0, 5.0, -5.0, 0.1)
        with col3:
            max_change = st.slider("Max Change %", -5.0, 5.0, 5.0, 0.1)
        
        # Apply filters
        filtered_data = self.index_data[
            (self.index_data['Region'].isin(regions)) &
            (self.index_data['Change %'] >= min_change) &
            (self.index_data['Change %'] <= max_change)
        ]
        
        # Display indices in cards
        st.subheader("Index Performance")
        
        for _, index in filtered_data.iterrows():
            change_class = "positive-change" if index['Change %'] > 0 else "negative-change"
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(f"""
                <div class="index-card">
                    <h3>{index['Name']} ({index['Symbol']})</h3>
                    <p><strong>Region:</strong> {index['Region']} | <strong>Currency:</strong> {index['Currency']}</p>
                    <h2>{index['Price']:,.2f}</h2>
                    <p class="{change_class}">
                        {index['Change']:+.2f} ({index['Change %']:+.2f}%) 
                        {'📈' if index['Change %'] > 0 else '📉'}
                    </p>
                    <p>Open: {index['Open']:,.2f} | High: {index['High']:,.2f} | Low: {index['Low']:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Detailed table view
        st.subheader("Detailed Performance Table")
        
        display_df = filtered_data[[
            'Symbol', 'Name', 'Region', 'Currency', 'Price', 
            'Change', 'Change %', 'Volume'
        ]].copy()
        
        # Format numbers
        display_df['Price'] = display_df['Price'].apply(lambda x: f"{x:,.2f}")
        display_df['Change'] = display_df['Change'].apply(lambda x: f"{x:+.2f}")
        display_df['Change %'] = display_df['Change %'].apply(lambda x: f"{x:+.2f}%")
        display_df['Volume'] = display_df['Volume'].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "N/A")
        
        st.dataframe(display_df, use_container_width=True)
        
        # Visualizations
        st.subheader("Market Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Performance heatmap by region
            region_performance = filtered_data.groupby('Region')['Change %'].mean().reset_index()
            fig = px.bar(
                region_performance,
                x='Region',
                y='Change %',
                title='Average Performance by Region',
                color='Change %',
                color_continuous_scale=['red', 'white', 'green']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Change distribution
            fig = px.histogram(
                filtered_data,
                x='Change %',
                title='Distribution of Daily Changes',
                nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Historical charts for selected indices
        st.subheader("Historical Charts")
        
        selected_indices = st.multiselect(
            "Select indices for historical charts",
            options=self.index_data['Symbol'].tolist(),
            default=self.index_data['Symbol'].tolist()[:3]
        )
        
        if selected_indices and self.historical_data is not None:
            period = st.selectbox("Chart Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
            
            if st.button("Update Historical Charts"):
                self.fetch_historical_data(selected_indices, period)
            
            fig = go.Figure()
            
            for symbol in selected_indices:
                if symbol in self.historical_data:
                    hist_data = self.historical_data[symbol]
                    if not hist_data.empty:
                        fig.add_trace(go.Scatter(
                            x=hist_data.index,
                            y=hist_data['Close'],
                            name=self.index_info.get(symbol, {}).get('name', symbol),
                            mode='lines'
                        ))
            
            fig.update_layout(
                title='Historical Performance',
                xaxis_title='Date',
                yaxis_title='Price',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Technical analysis section
        st.subheader("Technical Analysis")
        
        if selected_indices and self.historical_data is not None:
            tech_data = []
            for symbol in selected_indices:
                if symbol in self.historical_data:
                    indicators = self.calculate_technical_indicators(self.historical_data[symbol])
                    if indicators:
                        tech_data.append({
                            'Symbol': symbol,
                            'Name': self.index_info.get(symbol, {}).get('name', symbol),
                            'SMA 20': indicators['SMA_20'],
                            'SMA 50': indicators['SMA_50'],
                            'SMA 200': indicators['SMA_200'],
                            'RSI': indicators['RSI']
                        })
            
            if tech_data:
                tech_df = pd.DataFrame(tech_data)
                st.dataframe(tech_df, use_container_width=True)

def main():
    st.markdown('<h1 class="main-header">🌍 Global Index Tracker</h1>', unsafe_allow_html=True)
    
    # Initialize tracker
    tracker = GlobalIndexTracker()
    
    # Sidebar controls
    st.sidebar.header("Configuration")
    
    # Default indices from the uploaded file
    default_indices = ['^GSPC', '^DJI', '^IXIC', '^N225', '^HSI', '^TPX', 
                      '^SPX', '000001.SS', '399106.SZ', '000827.SS', 'TXGM.TS']
    
    # Additional popular indices
    additional_indices = st.sidebar.multiselect(
        "Add more indices",
        options=['^FTSE', '^GDAXI', '^FCHI', '^STOXX50E', '^AXJO', '^BSESN', '^NSEI', '^KS11', '^TWII'],
        default=[]
    )
    
    all_indices = default_indices + additional_indices
    
    update_frequency = st.sidebar.selectbox("Update Frequency", ["1m", "5m", "15m", "30m", "1h"], index=2)
    
    if st.sidebar.button("🔄 Refresh Data", type="primary"):
        with st.spinner("Fetching latest market data..."):
            success = tracker.fetch_index_data(all_indices)
            if success:
                tracker.fetch_historical_data(all_indices, "1y")
                st.sidebar.success("Data updated successfully!")
    
    # Initial data load
    if tracker.index_data is None:
        with st.spinner("Loading initial data..."):
            tracker.fetch_index_data(all_indices)
            tracker.fetch_historical_data(all_indices, "1y")
    
    if tracker.index_data is not None:
        tracker.display_dashboard()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Data Source**: Yahoo Finance  
    **Update Frequency**: Every {}  
    **Note**: Prices are delayed by 15-20 minutes
    """.format(update_frequency))

if __name__ == "__main__":
    main()
