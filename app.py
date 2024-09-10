import streamlit as st
import yaml
from engine.stellar_api import fetch_price_data
from engine.trading_bot import TradingBot
import plotly.graph_objects as go

# Load configuration from YAML file
with open("config/config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

# Set page configuration
st.set_page_config(page_title="Stellar Trading", layout="wide")

# Sidebar
st.sidebar.image("assets/logo.jpg", use_column_width=True)
st.sidebar.title("Stellar Trading")
network_choice = st.sidebar.selectbox("Select Network", ["Mainnet", "Testnet"])
stellar_key = st.sidebar.text_input("Enter Your Stellar Key (Private)", type="password")

# Determine the network URL based on selection
network_url = "https://horizon-testnet.stellar.org" if network_choice == "Testnet" else "https://horizon.stellar.org"

## Main Page
col1, col2 = st.columns([1, 2])

# Trading History
with col1:
    st.subheader("Account Balance")
    if stellar_key:
        bot = TradingBot(stellar_key, network=network_choice.lower())
        
        with st.spinner("Fetching account balances..."):
            balances = bot.get_balances()
            # Display account balances with fixed height and vertical scroll
            st.dataframe(balances, height=300)
    else:
        st.write("Please enter your Stellar Key to proceed.")

    st.subheader("Trading History")
    if stellar_key:
        bot = TradingBot(stellar_key, network=network_choice.lower())
        
        with st.spinner("Fetching trading history..."):
            trades = bot.fetch_trades()

        if not trades.empty:
            st.write("Trade History:")
            # Display trading history with fixed height and vertical scroll
            st.dataframe(trades, height=300)
        else:
            st.write("No trading history available for this account.")
    else:
        st.write("Please enter your Stellar Key to proceed.")

# Crypto Charts
with col2:
    col21, col22 = st.columns([1, 1])
    with col21:
        available_cryptos = list(config["asset_issuers"].keys())
        crypto_1 = st.selectbox("First Crypto", available_cryptos, index=0)
    with col22:
        available_cryptos_for_second = [crypto for crypto in available_cryptos if crypto != crypto_1]
        crypto_2 = st.selectbox("Second Crypto", available_cryptos_for_second, index=0)

    chart_tab, candlestick_tab = st.tabs(["Line Chart", "Candlestick Chart"])

    col221, col222 = st.columns([3, 1])
    with col221:
        time_intervals = ["15s", "30s", "1m", "2m", "5m", "15m", "1h", "1d", "1w"]
        selected_interval = st.radio("Interval of Time Points", time_intervals, horizontal=True)
        interval_mapping = {
            "5s": "5s",
            "15s": "15s",
            "30s": "30s",
            "1m": "1min",
            "2m": "2min",
            "5m": "5min",
            "15m": "15min",
            "1h": "1h",
            "1d": "1d",
            "1w": "1w"
        }
        interval = interval_mapping[selected_interval]

    with col222:
        num_points = st.slider("Number of Time Points", min_value=10, max_value=100, value=30, step=10)

    with st.spinner(f"Fetching {interval} interval {num_points} points data..."):
        price_data = fetch_price_data(network_url=network_url, 
                                      crypto_pair=f"{crypto_1}/{crypto_2}", 
                                      interval=interval, 
                                      num_points=num_points)

    if not price_data.empty:
        layout_adjustments = {
            "margin": dict(l=20, r=20, t=20, b=20),
            "xaxis": {"title": "Time", "automargin": True, "rangeslider": {"visible": False}},
            "yaxis": {"title": "Price", "automargin": True},
            "yaxis2": {"title": "Volume", "overlaying": "y", "side": "right"},
            "height": 400
        }

        with chart_tab:
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=price_data['timestamp'], y=price_data['close'], mode='lines', name='Price'))
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
        st.write("No price data available for the selected crypto pair.")
