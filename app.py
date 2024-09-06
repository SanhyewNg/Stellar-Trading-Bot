import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from engine.stellar_api import fetch_price_data, fetch_trading_history
from engine.trading_bot import TradingBot
from datetime import datetime
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(page_title="Stellar Trading Bot", layout="wide")

# Display the logo at the top of the sidebar
st.sidebar.image("assets/logo.jpg", use_column_width=True)

# Sidebar for Stellar Key
st.sidebar.title("Stellar Trading Bot")

network_choice = st.sidebar.selectbox("Select Network", ["Testnet", "Mainnet"])
stellar_key = st.sidebar.text_input("Enter Your Stellar Key", type="password")

# Sidebar for chart type
chart_type = st.sidebar.selectbox("Select Chart Type", ["Line Chart", "Candlestick Chart"])

# Sidebar for trading pair
crypto_pair = st.sidebar.selectbox("Select Trading Pair", ["XLM/USDC", "BTC/USD"])

# Function to plot an empty chart with axes
def plot_empty_chart():
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot([], [])  # Empty plot
    ax.set_title("Chart Area")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    st.pyplot(fig)

# Function to display an empty trading history table
def display_empty_trading_history():
    # Create an empty DataFrame with the desired columns
    empty_df = pd.DataFrame(columns=["Date", "Action", "Amount", "Price"])
    st.table(empty_df)


# Initialize TradingBot if key is provided
if stellar_key:
    bot = TradingBot(stellar_key, network="testnet" if network_choice == "Testnet" else "mainnet")
    
    with st.spinner("Fetching price data..."):
        # Fetch price data
        price_data = fetch_price_data(crypto_pair)

    if not price_data.empty:
        # Create columns for chart and trading history
        col1, col2 = st.columns([2, 1])  # Adjust the width ratio as needed

        with col1:
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

        with col2:
            with st.spinner("Fetching trading history..."):
                # Fetch trading history
                trading_history = fetch_trading_history(bot)

            # Display trading history as table
            st.subheader("Trading History")
            if not trading_history.empty:
                st.table(trading_history)
            else:
                st.write("No trading history available for this account.")

        # # Overlay trading history on chart
        # st.subheader("Price Chart with Trading History")
        # fig, ax = plt.subplots(figsize=(10, 5))
        # ax.plot(price_data['timestamp'], price_data['close'], label='Price')

        # # Add buy/sell markers
        # for index, trade in trading_history.iterrows():
        #     trade_date = datetime.strptime(trade['Date'], "%Y-%m-%dT%H:%M:%SZ")
        #     color = 'green' if trade['Action'] == 'Buy' else 'red'
        #     ax.axvline(trade_date, color=color, linestyle='--', alpha=0.7)
        #     ax.text(trade_date, trade['Price'], f"{trade['Action']} {trade['Amount']}", rotation=90, verticalalignment='bottom', color=color)

        # ax.set_title(f"{crypto_pair} Price with Trading History")
        # ax.set_xlabel("Date")
        # ax.set_ylabel("Price")
        # ax.legend()
        # st.pyplot(fig)

    else:
        st.write("No price data available for the selected trading pair.")

else:
    # Display placeholder charts and trading history
    st.title("Stellar Trading Bot")
    st.write("Please enter your Stellar Key to proceed.")

    # Create columns for chart and trading history
    col1, col2 = st.columns([2, 1])  # Adjust the width ratio as needed

    with col1:
        # Placeholder for price chart
        st.subheader("Price Chart")
        plot_empty_chart()

    with col2:
        # Placeholder for trading history table
        st.subheader("Trading History")
        display_empty_trading_history()
