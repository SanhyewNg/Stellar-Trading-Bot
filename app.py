import threading
import time
import streamlit as st
import yaml
import pandas as pd
from engine.stellar_api import fetch_exchange_data
from engine.trading_bot import TradingBot
import plotly.graph_objects as go

# Load configuration from YAML file
with open("config/config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

# Initialize session state values if not already set
for key, default in [("crypto_1", list(config["asset_issuers"].keys())[0]), 
                     ("crypto_2", list(config["asset_issuers"].keys())[1]),
                     ("interval", "1min"), 
                     ("num_points", 50), 
                     ("balances", None),
                     ("algo_active", False),
                     ("previous_stellar_key", "")]:  # algo_active to track if algo trading is on
    if key not in st.session_state:
        st.session_state[key] = default

chart_layout_adjustments = {
    "margin": dict(l=20, r=20, t=20, b=20),
    "xaxis": {"title": "Time", "automargin": True, "rangeslider": {"visible": False}},
    "yaxis": {"title": f"{st.session_state['crypto_1']}/{st.session_state['crypto_2']}", "automargin": True},
    "yaxis2": {"title": "Volume", "overlaying": "y", "side": "right"},
    "height": 300,
    "showlegend": False
}

# Set page configuration
st.set_page_config(page_title="Stellar Trading", layout="wide")

# Sidebar
st.sidebar.image("assets/logo.jpg", use_column_width=True)
st.sidebar.title("Stellar Trading")

network_choice = st.sidebar.selectbox("Select Network", ["Mainnet", "Testnet"])
network_url = "https://horizon-testnet.stellar.org" if network_choice == "Testnet" else "https://horizon.stellar.org"

stellar_key = st.sidebar.text_input("Enter Your Stellar Key (Private)", type="password")
if stellar_key != st.session_state["previous_stellar_key"]:
    st.session_state["previous_stellar_key"] = stellar_key
    st.session_state["balances"] = None  # Reset balances when the key changes

# Initialize the TradingBot instance
bot = TradingBot(stellar_key, network=network_choice.lower()) if stellar_key else None
if stellar_key and bot:
    with st.spinner("Fetching account balances..."):
        balances = bot.get_balances()
        st.session_state['balances'] = balances

# Trading History & Balance
col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("Account")

    st.write("**Balances**")
    if stellar_key and st.session_state["balances"]:
        with st.spinner("Fetching account balances..."):
            balances = bot.get_balances()
            st.session_state['balances'] = balances
            st.dataframe(pd.DataFrame(balances), height=175, use_container_width=True)
    else:
        st.write("Please enter your Stellar Key to proceed.")

    st.write("**Trading History**")
    if stellar_key and bot:
        trades = pd.DataFrame(columns=["Time", "Sell", "Buy", "Amount", "Price", "Total"])
        if not trades.empty:
            st.dataframe(trades, height=350, use_container_width=True)
        else:
            st.write("No trading history available for this account.")
            st.dataframe(trades, height=350, use_container_width=True)
    else:
        st.write("Please enter your Stellar Key to proceed.")

# Crypto Charts
with col1:
    st.subheader("Exchange")

    col11, col12 = st.columns([1, 1])
    
    with col11:
        available_cryptos = list(config["asset_issuers"].keys())
        previous_crypto_1 = st.session_state["crypto_1"]
        st.session_state["crypto_1"] = st.selectbox("First Crypto", available_cryptos, index=0, label_visibility="hidden")
        
        if previous_crypto_1 != st.session_state["crypto_1"]:
            available_cryptos_for_second = [crypto for crypto in available_cryptos if crypto != st.session_state["crypto_1"]]
            st.session_state["crypto_2"] = available_cryptos_for_second[0]
        
        if st.session_state['balances']:
            balance_1 = None
            for balance in st.session_state['balances']:
                if balance['Asset'] == st.session_state["crypto_1"]:
                    balance_1 = balance['Balance']
            st.write(f"Available:  {balance_1} {st.session_state['crypto_1']}")
    
    with col12:
        available_cryptos_for_second = [crypto for crypto in available_cryptos if crypto != st.session_state["crypto_1"]]
        st.session_state["crypto_2"] = st.selectbox("Second Crypto", available_cryptos_for_second, index=0, label_visibility="hidden")
        
        if st.session_state['balances']:
            balance_2 = None
            for balance in st.session_state['balances']:
                if balance['Asset'] == st.session_state["crypto_2"]:
                    balance_2 = balance['Balance']
            st.write(f"Available:  {balance_2} {st.session_state['crypto_2']}")

    candlestick_tab, chart_tab = st.tabs(["Candlestick Chart", "Line Chart"])
    
    _, col13, col14, _ = st.columns([1, 6, 2, 1])
    
    with col13:
        time_intervals = ["1m", "2m", "5m", "15m", "1h", "1d", "1w"]
        selected_interval = st.radio("Interval of Time Points", time_intervals, horizontal=True)
        interval_mapping = {
            "1m": "1min",
            "2m": "2min",
            "5m": "5min",
            "15m": "15min",
            "1h": "1h",
            "1d": "1d",
            "1w": "1w"
        }
        st.session_state["interval"] = interval_mapping[selected_interval]
    
    with col14:
        st.session_state["num_points"] = st.slider("Number of Time Points", min_value=30, max_value=100, value=50, step=10)

    with st.spinner(f"Fetching {st.session_state['num_points']} * {st.session_state['interval']} data..."):
        price_data = fetch_exchange_data(
            network_url=network_url,
            crypto_pair=f"{st.session_state['crypto_1']}/{st.session_state['crypto_2']}",
            interval=st.session_state["interval"],
            num_points=st.session_state["num_points"]
        )

    if not price_data.empty:
        price_data['open'] = price_data['open'].interpolate(method='linear')
        price_data['close'] = price_data['close'].interpolate(method='linear')

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
            fig_candle.update_layout(**chart_layout_adjustments)
            st.plotly_chart(fig_candle, use_container_width=True)

        with chart_tab:
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=price_data['timestamp'], y=(price_data['open'] + price_data['close']) / 2, mode='lines', name='Price'))
            if 'volume' in price_data.columns:
                fig_line.add_trace(go.Bar(x=price_data['timestamp'], y=price_data['volume'], name='Volume', yaxis='y2', opacity=0.5))
            else:
                st.write("Volume data is not available for this trading pair.")
            fig_line.update_layout(**chart_layout_adjustments)
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.write("No data available for the selected crypto pair.")

# Toggleable trading control
if stellar_key:
    if st.session_state["algo_active"]:
        if st.button("Stop Algo Trading"):
            st.session_state["algo_active"] = False
            st.success("Algorithmic trading stopped.")
            st.rerun()
    else:
        if st.button("Start Algo Trading"):
            st.session_state["algo_active"] = True
            st.success("Algorithmic trading started.")
            st.rerun()

# Periodic trading logic
if stellar_key and st.session_state["algo_active"]:
    def periodic_trading():
        interval_seconds = {
            "1min": 60,
            "2min": 120,
            "5min": 300,
            "15min": 900,
            "1h": 3600,
            "1d": 86400,
            "1w": 604800
        }
        trade_interval = interval_seconds.get(st.session_state["interval"], 60)  # Default to 1 minute

        while st.session_state["algo_active"]:
            try:
                price_data = fetch_exchange_data(
                    network_url=network_url,
                    crypto_pair=f"{st.session_state['crypto_1']}/{st.session_state['crypto_2']}",
                    interval=st.session_state["interval"],
                    num_points=st.session_state["num_points"]
                )
                balances = bot.get_balances()
                bot.do_exchange(
                    base_asset_code=st.session_state['crypto_1'],
                    counter_asset_code=st.session_state['crypto_2'],
                    price_data=price_data,
                    balances=balances
                )
            except Exception as e:
                st.error(f"An error occurred: {e}")
            time.sleep(trade_interval)
    while True:
        periodic_trading()
    # # Run periodic trading in a separate thread
    # if 'trading_thread' not in st.session_state:
    #     st.session_state['trading_thread'] = threading.Thread(target=periodic_trading, daemon=True)
    #     st.session_state['trading_thread'].start()
