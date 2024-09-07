import streamlit as st
import pandas as pd
import yaml
from engine.stellar_api import fetch_price_data, fetch_trading_history
from engine.trading_bot import TradingBot
import plotly.graph_objects as go

# Load configuration from YAML file
with open("config/config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

# Set page configuration
st.set_page_config(page_title="Stellar Trading Bot", layout="wide")

st.sidebar.title("Stellar Trading Bot")
st.sidebar.image("assets/logo.jpg", use_column_width=True)

# Select network and Stellar key input
network_choice = st.sidebar.selectbox("Select Network", ["Testnet", "Mainnet"])
stellar_key = st.sidebar.text_input("Enter Your Stellar Key", type="password")

# Function to display an empty trading history table
def display_empty_trading_history():
    empty_df = pd.DataFrame(columns=["Date", "Action", "Amount", "Price"])
    st.table(empty_df)

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Trading History")

    if stellar_key:
        bot = TradingBot(stellar_key, network="testnet" if network_choice == "Testnet" else "mainnet")
        
        with st.spinner("Fetching trading history..."):
            trading_history = fetch_trading_history(bot)

        if not trading_history.empty:
            st.table(trading_history)
        else:
            st.write("No trading history available for this trading pair.")
            display_empty_trading_history()
    else:
        st.write("Please enter your Stellar Key to proceed.")
        display_empty_trading_history()

with col2:
    col21, col22 = st.columns([1, 1])

    available_cryptos = list(config["asset_issuers"].keys())

    with col21:
        crypto_1 = st.selectbox("First Crypto", available_cryptos, index=0)

    available_cryptos_for_second = [crypto for crypto in available_cryptos if crypto != crypto_1]

    with col22:
        crypto_2 = st.selectbox("Second Crypto", available_cryptos_for_second, index=0)

    chart_tab, candlestick_tab = st.tabs(["Line Chart", "Candlestick Chart"])

    time_intervals = ["1m", "5m", "15m", "1h", "1d", "1w"]
    selected_interval = st.radio("", time_intervals, horizontal=True)

    interval_mapping = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "1h": "1h",
        "1d": "1d",
        "1w": "1w"
    }
    interval = interval_mapping[selected_interval]

    with st.spinner(f"Fetching {selected_interval} price data..."):
        price_data = fetch_price_data(crypto_1 + "/" + crypto_2, interval=interval)

    if not price_data.empty:
        layout_adjustments = {
            "margin": dict(l=20, r=20, t=20, b=20),
            "xaxis": {"title": "Time", "automargin": True, "rangeslider": {"visible": False}},  # Hide range slider
            "yaxis": {"title": "Price", "automargin": True},
            "yaxis2": {"title": "Volume", "overlaying": "y", "side": "right"},  # Secondary y-axis for volume
            "height": 500  # Adjust chart height
        }

        with chart_tab:
            fig_line = go.Figure()

            # Price line chart
            fig_line.add_trace(go.Scatter(x=price_data['timestamp'], y=price_data['close'], mode='lines', name='Price'))

            # Check if volume data is available
            if 'volume' in price_data.columns:
                fig_line.add_trace(go.Bar(x=price_data['timestamp'], y=price_data['volume'], name='Volume', yaxis='y2', opacity=0.5))
            else:
                st.write("Volume data is not available for this trading pair.")

            fig_line.update_layout(**layout_adjustments)
            st.plotly_chart(fig_line, use_container_width=True)

        with candlestick_tab:
            fig_candle = go.Figure(data=[go.Candlestick(
                x=price_data['timestamp'],
                open=price_data['open'],
                high=price_data['high'],
                low=price_data['low'],
                close=price_data['close']
            )])

            if 'volume' in price_data.columns:
                fig_candle.add_trace(go.Bar(x=price_data['timestamp'], y=price_data['volume'], name='Volume', yaxis='y2', opacity=0.3))

            fig_candle.update_layout(**layout_adjustments)
            st.plotly_chart(fig_candle, use_container_width=True)
    else:
        st.write("No price data available for the selected trading pair.")
