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
    .neutral-card {
        background: linear-gradient(135deg, #666666 0%, #444444 100%);
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
    }
    .chart-header {
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

class GlobalIndexTracker:
    def __init__(self):
        self.index_data = None
        self.historical_data = None
        self.index_info = {
            '^GSPC': {'name': 'S&P 500', 'region': 'USA', 'currency': 'USD'},
            '^DJI': {'name': 'Dow Jones', 'region': 'USA', 'currency': 'USD'},
            '^IXIC': {'name': 'NASDAQ', 'region': 'USA', 'currency': 'USD'},
            '^N225': {'name': 'Nikkei 225', 'region': 'Japan', 'currency': 'JPY'},
            '^HSI': {'name': 'Hang Seng', 'region': 'Hong Kong', 'currency': 'HKD'},
            '^TPX': {'name': 'TOPIX', 'region': 'Japan', 'currency': 'JPY'},
            '000001.SS': {'name': 'Shanghai Comp', 'region': 'China', 'currency': 'CNY'},
            '399106.SZ': {'name': 'Shenzhen Comp', 'region': 'China', 'currency': 'CNY'},
            '000827.SS': {'name': 'CSI 300', 'region': 'China', 'currency': 'CNY'},
            '^FTSE': {'name': 'FTSE 100', 'region': 'UK', 'currency': 'GBP'},
            '^GDAXI': {'name': 'DAX', 'region': 'Germany', 'currency': 'EUR'},
            '^FCHI': {'name': 'CAC 40', 'region': 'France', 'currency': 'EUR'},
            '^AXJO': {'name': 'ASX 200', 'region': 'Australia', 'currency': 'AUD'},
            '^BSESN': {'name': 'BSE Sensex', 'region': 'India', 'currency': 'INR'},
            '^NSEI': {'name': 'Nifty 50', 'region': 'India', 'currency': 'INR'},
        }
    
    def fetch_index_data(self, symbols):
        """Fetch current data for multiple indices"""
        try:
            results = []
            
            for symbol in symbols:
                try:
                    # Fetch data for each symbol individually for better reliability
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")  # Get 2 days of data
                    
                    if not hist.empty and len(hist) >= 2:
                        current_day = hist.iloc[-1]
                        previous_day = hist.iloc[-2]
                        
                        info = self.index_info.get(symbol, {'name': symbol, 'region': 'Unknown', 'currency': 'USD'})
                        
                        # Calculate changes
                        current_close = current_day['Close']
                        prev_close = previous_day['Close']
                        change = current_close - prev_close
                        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
                        
                        # Format volume
                        volume = current_day['Volume']
                        if pd.notnull(volume):
                            volume_str = f"{volume:,.0f}"
                        else:
                            volume_str = "N/A"
                        
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
                            'Volume': volume_str,
                            'Raw_Volume': volume
                        })
                    
                except Exception as e:
                    st.warning(f"Could not fetch data for {symbol}: {str(e)}")
                    continue
            
            if results:
                self.index_data = pd.DataFrame(results)
                return True
            else:
                st.error("No data could be fetched for any symbols.")
                return False
                
        except Exception as e:
            st.error(f"Error fetching index data: {str(e)}")
            return False

    def fetch_historical_data(self, symbols, period="3mo"):
        """Fetch historical data for normalized chart"""
        try:
            historical_data = {}
            
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period=period)
                    
                    if not hist.empty:
                        # Normalize prices to percentage change from start
                        start_price = hist['Close'].iloc[0]
                        hist['Normalized'] = (hist['Close'] / start_price - 1) * 100
                        historical_data[symbol] = hist
                    
                except Exception as e:
                    st.warning(f"Could not fetch historical data for {symbol}: {str(e)}")
                    continue
            
            self.historical_data = historical_data
            return len(historical_data) > 0
            
        except Exception as e:
            st.error(f"Error fetching historical data: {str(e)}")
            return False

    def create_normalized_chart(self, selected_symbols, period="3mo"):
        """Create normalized performance chart"""
        if not self.historical_data:
            return None
        
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set1
        color_idx = 0
        
        for symbol in selected_symbols:
            if symbol in self.historical_data:
                hist_data = self.historical_data[symbol]
                index_name = self.index_info.get(symbol, {}).get('name', symbol)
                
                fig.add_trace(go.Scatter(
                    x=hist_data.index,
                    y=hist_data['Normalized'],
                    name=index_name,
                    mode='lines',
                    line=dict(width=2.5, color=colors[color_idx % len(colors)]),
                    hovertemplate=(
                        '<b>%{text}</b><br>' +
                        'Date: %{x|%Y-%m-%d}<br>' +
                        'Performance: %{y:.2f}%<br>' +
                        '<extra></extra>'
                    ),
                    text=[index_name] * len(hist_data)
                ))
                color_idx += 1
        
        fig.update_layout(
            title=f"Normalized Performance Comparison ({period})",
            xaxis_title="Date",
            yaxis_title="Performance (%)",
            hovermode="x unified",
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            plot_bgcolor='rgba(240, 240, 240, 0.1)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
        )
        
        # Add horizontal zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.7)
        
        return fig
    
    def display_index_cards(self, filtered_data):
        """Display index performance cards"""
        if filtered_data.empty:
            st.warning("No indices match your filter criteria.")
            return
        
        st.subheader("📊 Index Performance Cards")
        
        # Create columns for the cards
        cols = st.columns(2)
        
        for i, (_, index) in enumerate(filtered_data.iterrows()):
            col_idx = i % 2
            with cols[col_idx]:
                # Determine card color based on performance
                if index['Change %'] > 0:
                    card_class = "green-card"
                    change_icon = "📈"
                elif index['Change %'] < 0:
                    card_class = "red-card"
                    change_icon = "📉"
                else:
                    card_class = "neutral-card"
                    change_icon = "➡️"
                
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
                    <p><strong>Volume:</strong> {index['Volume']}</p>
                </div>
                """, unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="main-header">🌍 Global Index Tracker</h1>', unsafe_allow_html=True)
    
    # Initialize tracker
    tracker = GlobalIndexTracker()
    
    # Default indices from your file
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
    
    # Chart settings
    st.sidebar.header("Chart Settings")
    chart_period = st.sidebar.selectbox(
        "Chart Period:",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=1
    )
    
    # Always show load button
    if st.sidebar.button("🔄 Load Market Data", type="primary"):
        with st.spinner("Fetching latest market data..."):
            if selected_indices:
                if tracker.fetch_index_data(selected_indices):
                    # Also fetch historical data for charts
                    tracker.fetch_historical_data(selected_indices, chart_period)
                    st.sidebar.success("Data loaded successfully!")
                else:
                    st.sidebar.error("Failed to load data. Please try again.")
            else:
                st.sidebar.warning("Please select at least one index to track.")
    
    # If no data loaded yet, load default data
    if tracker.index_data is None:
        with st.spinner("Loading initial market data..."):
            tracker.fetch_index_data(default_indices)
            tracker.fetch_historical_data(default_indices, chart_period)
    
    # Display data if available
    if tracker.index_data is not None and not tracker.index_data.empty:
        # Summary metrics
        st.subheader("📈 Market Overview")
        
        positive_count = len(tracker.index_data[tracker.index_data['Change %'] > 0])
        negative_count = len(tracker.index_data[tracker.index_data['Change %'] < 0])
        total_count = len(tracker.index_data)
        
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
        
        # NORMALIZED PERFORMANCE CHART
        st.markdown('<div class="chart-header"><h3>📈 Normalized Performance Comparison</h3></div>', unsafe_allow_html=True)
        
        if tracker.historical_data:
            chart_fig = tracker.create_normalized_chart(selected_indices, chart_period)
            if chart_fig:
                st.plotly_chart(chart_fig, use_container_width=True)
                
                # Chart explanation
                with st.expander("ℹ️ About Normalized Chart"):
                    st.markdown("""
                    **What is a normalized chart?**
                    - All indices start at 0% on the first day of the selected period
                    - Shows percentage change from the starting point
                    - Allows easy comparison of performance across different indices
                    - Perfect for identifying relative strength/weakness
                    
                    **How to read it:**
                    - Lines above 0% = positive performance
                    - Lines below 0% = negative performance  
                    - Steeper slopes = stronger momentum
                    - Crossovers = changes in relative performance
                    """)
            else:
                st.info("No historical data available for chart.")
        else:
            st.info("Click 'Load Market Data' to generate performance charts.")
        
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
            st.dataframe(
                filtered_data[[
                    'Symbol', 'Name', 'Region', 'Currency', 'Price', 
                    'Change', 'Change %', 'Volume'
                ]],
                use_container_width=True,
                height=400
            )
            
            # Performance statistics
            st.subheader("📊 Performance Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_change = filtered_data['Change %'].mean()
                st.metric("Average Change", f"{avg_change:+.2f}%")
            
            with col2:
                best_performer = filtered_data.loc[filtered_data['Change %'].idxmax()]
                st.metric("Best Performer", f"{best_performer['Name']} ({best_performer['Change %']:+.2f}%)")
            
            with col3:
                worst_performer = filtered_data.loc[filtered_data['Change %'].idxmin()]
                st.metric("Worst Performer", f"{worst_performer['Name']} ({worst_performer['Change %']:+.2f}%)")
                
        else:
            st.info("No indices match your current filters.")
    
    else:
        st.error("No market data available. Please click 'Load Market Data' to fetch data.")

if __name__ == "__main__":
    main()
