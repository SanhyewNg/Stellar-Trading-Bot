import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from engine.stellar_api import fetch_price_data, fetch_trading_history
from engine.trading_bot import TradingBot
from datetime import datetime
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(page_title="Stellar Trading Bot", layout="wide")

st.sidebar.title("Stellar Trading Bot")
# Display the logo at the top of the sidebar
st.sidebar.image("assets/logo.jpg", use_column_width=True)

network_choice = st.sidebar.selectbox("Select Network", ["Testnet", "Mainnet"])
stellar_key = st.sidebar.text_input("Enter Your Stellar Key", type="password")

chart_type = st.sidebar.selectbox("Select Chart Type", ["Line Chart", "Candlestick Chart"])

# Sidebar for trading pair
crypto_pair = st.sidebar.selectbox("Select Trading Pair", ["XLM/USDC", "BTC/USD"])

# Function to display an empty trading history table
def display_empty_trading_history():
    # Create an empty DataFrame with the desired columns
    empty_df = pd.DataFrame(columns=["Date", "Action", "Amount", "Price"])
    st.table(empty_df)

# Fetch price data and render price chart
with st.spinner("Fetching price data..."):
    price_data = fetch_price_data(crypto_pair, interval="1s")

# st.title("Stellar Trading Bot")

col1, col2 = st.columns([1, 1])  # Adjust the width ratio as needed
# Create columns for chart and trading history
with col2:
    if not price_data.empty:
        # Display the selected chart
        st.title(f"{crypto_pair} Price Chart")
        if chart_type == "Line Chart":
            st.line_chart(price_data.set_index("timestamp")["close"])
        elif chart_type == "Candlestick Chart":
            # Implement candlestick chart using Plotly
            fig = go.Figure(data=[go.Candlestick(
                x=price_data['timestamp'],
                open=price_data['open'],
                high=price_data['high'],
                low=price_data['low'],
                close=price_data['close']
            )])
            fig.update_layout(title=f"{crypto_pair} Candlestick Chart", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig)
    else:
        st.write("No price data available for the selected trading pair.")

with col1:
    # Placeholder for trading history table
    st.subheader("Trading History")

    # Initialize TradingBot if key is provided
    if stellar_key:
        bot = TradingBot(stellar_key, network="testnet" if network_choice == "Testnet" else "mainnet")
        
        with st.spinner("Fetching trading history..."):
            # Fetch trading history
            trading_history = fetch_trading_history(bot)

        if not trading_history.empty:
            st.table(trading_history)
        else:
            st.write("No trading history available for this trading pair.")
            display_empty_trading_history()


    else:
        # Display placeholder trading history
        st.write("Please enter your Stellar Key to proceed.")
        display_empty_trading_history()
