import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from engine.stellar_api import fetch_price_data, fetch_trading_history
from engine.trading_bot import TradingBot
from datetime import datetime
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(page_title="Stellar Trading Bot", layout="wide")

# Sidebar for Stellar Key
st.sidebar.title("Stellar Trading Bot")
stellar_key = st.sidebar.text_input("Enter Your Stellar Key", type="password")

# Sidebar for chart type
chart_type = st.sidebar.selectbox("Select Chart Type", ["Line Chart", "Candlestick Chart"])

# Sidebar for trading pair
crypto_pair = st.sidebar.selectbox("Select Trading Pair", ["XLM/USD", "BTC/USD"])

# Initialize TradingBot if key is provided
if stellar_key:
    bot = TradingBot(stellar_key)

    # Fetch price data
    price_data = fetch_price_data(crypto_pair)

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

    # Fetch trading history
    trading_history = fetch_trading_history(bot)

    # Display trading history as table
    st.subheader("Trading History")
    st.table(trading_history)

    # Overlay trading history on chart
    st.subheader("Price Chart with Trading History")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(price_data['timestamp'], price_data['close'], label='Price')

    # Add buy/sell markers
    for index, trade in trading_history.iterrows():
        trade_date = datetime.strptime(trade['Date'], "%Y-%m-%d")
        color = 'green' if trade['Action'] == 'Buy' else 'red'
        ax.axvline(trade_date, color=color, linestyle='--', alpha=0.7)
        ax.text(trade_date, trade['Price'], f"{trade['Action']} {trade['Amount']}", rotation=90, verticalalignment='bottom', color=color)

    ax.set_title(f"{crypto_pair} Price with Trading History")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()
    st.pyplot(fig)

else:
    st.warning("Please enter your Stellar Key to proceed.")
