import streamlit as st
import yaml
import pandas as pd
from engine.stellar_api import fetch_exchange_data
from engine.trading_bot import TradingBot
import plotly.graph_objects as go

# Load configuration from YAML file
with open("config/config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

# %%
# Set page configuration
st.set_page_config(page_title="Stellar Trading", layout="wide")

# Sidebar
st.sidebar.image("assets/logo.jpg", use_column_width=True)
st.sidebar.title("Stellar Trading")

network_choice = st.sidebar.selectbox("Select Network", ["Mainnet", "Testnet"])
network_url = "https://horizon-testnet.stellar.org" if network_choice == "Testnet" else "https://horizon.stellar.org"

stellar_key = st.sidebar.text_input("Enter Your Stellar Key (Private)", type="password")

# Initialize a session state to track the previous Stellar key
if "previous_stellar_key" not in st.session_state:
    st.session_state["previous_stellar_key"] = ""

# If the Stellar key has changed, reset balances
if stellar_key != st.session_state["previous_stellar_key"]:
    st.session_state["previous_stellar_key"] = stellar_key
    st.session_state["balances"] = None  # Reset balances when the key changes

# Initialize bot only once when Stellar key is provided
bot = None
if stellar_key:
    bot = TradingBot(stellar_key, network=network_choice.lower())

# Save state for charts to trigger updates
if "crypto_1" not in st.session_state:
    st.session_state["crypto_1"] = list(config["asset_issuers"].keys())[0]

if "crypto_2" not in st.session_state:
    st.session_state["crypto_2"] = list(config["asset_issuers"].keys())[1]

if "interval" not in st.session_state:
    st.session_state["interval"] = "1min"

if "num_points" not in st.session_state:
    st.session_state["num_points"] = 50

if "balances" not in st.session_state:
    st.session_state["balances"] = None


# %%
# Trading History & Balance
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Account Balance")
    if stellar_key and bot:
        with st.spinner("Fetching account balances..."):
            balances = bot.get_balances()
            st.session_state['balances'] = balances
            # Display account balances with fixed height and vertical scroll
            st.dataframe(pd.DataFrame(balances), height=300)
    else:
        st.write("Please enter your Stellar Key to proceed.")

    st.subheader("Trading History")
    if stellar_key and bot:
        # Uncomment when trading history functionality is enabled
        # with st.spinner("Fetching trading history..."):
        #     trades = bot.fetch_trading_history()

        # if not trades.empty:
        #     # Display trading history with fixed height and vertical scroll
        #     st.dataframe(trades, height=300)
        # else:
        #     st.write("No trading history available for this account.")
        st.write("Trading history will be displayed here.")
    else:
        st.write("Please enter your Stellar Key to proceed.")

# %%
# Crypto Charts
with col2:
    col21, col22 = st.columns([1, 1])
    
    with col21:
        available_cryptos = list(config["asset_issuers"].keys())
        
        # Prevent resetting the second crypto selection unnecessarily
        previous_crypto_1 = st.session_state["crypto_1"]
        st.session_state["crypto_1"] = st.selectbox("First Crypto", available_cryptos, index=0)
        
        if previous_crypto_1 != st.session_state["crypto_1"]:
            # When first crypto changes, update second crypto options to exclude the selected first crypto
            available_cryptos_for_second = [crypto for crypto in available_cryptos if crypto != st.session_state["crypto_1"]]
            st.session_state["crypto_2"] = available_cryptos_for_second[0]
        
        if st.session_state['balances']:
            balance_1 = None
            # Find matching balance for the first crypto
            for balance in st.session_state['balances']:
                if balance['Asset'] == st.session_state["crypto_1"]:
                    balance_1 = balance['Balance']
            st.write(f"Available:  {balance_1} {st.session_state['crypto_1']}")
    
    with col22:
        # Only update second crypto options when the first crypto changes
        available_cryptos_for_second = [crypto for crypto in available_cryptos if crypto != st.session_state["crypto_1"]]
        st.session_state["crypto_2"] = st.selectbox("Second Crypto", available_cryptos_for_second, index=0)
        
        if st.session_state['balances']:
            balance_2 = None
            # Find matching balance for the second crypto
            for balance in st.session_state['balances']:
                if balance['Asset'] == st.session_state["crypto_2"]:
                    balance_2 = balance['Balance']
            st.write(f"Available:  {balance_2} {st.session_state['crypto_2']}")
    
    # Only update the chart when crypto selection, interval, or number of time points change
    candlestick_tab, chart_tab = st.tabs(["Candlestick Chart", "Line Chart"])
    
    col221, col222 = st.columns([3, 1])
    
    with col221:
        time_intervals = ["1m", "2m", "5m", "15m", "1h", "1d", "1w"]
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
        st.session_state["interval"] = interval_mapping[selected_interval]
    
    with col222:
        st.session_state["num_points"] = st.slider("Number of Time Points", min_value=10, max_value=100, value=50, step=10)

    # Fetch price data based on selected crypto pair, interval, and number of points
    with st.spinner(f"Fetching {st.session_state['interval']} interval {st.session_state['num_points']} points data..."):
        price_data = fetch_exchange_data(
            network_url=network_url,
            crypto_pair=f"{st.session_state['crypto_1']}/{st.session_state['crypto_2']}",
            interval=st.session_state["interval"],
            num_points=st.session_state["num_points"]
        )

    # Plot charts if price data is available
    if not price_data.empty:
        layout_adjustments = {
            "margin": dict(l=20, r=20, t=20, b=20),
            "xaxis": {"title": "Time", "automargin": True, "rangeslider": {"visible": False}},
            "yaxis": {"title": f"{st.session_state['crypto_1']}/{st.session_state['crypto_2']}", "automargin": True},
            "yaxis2": {"title": "Volume", "overlaying": "y", "side": "right"},
            "height": 300,
            "showlegend": False  # Disable legend
        }

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

        with chart_tab:
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=price_data['timestamp'], y=(price_data['open']+price_data['close']+price_data['high']+price_data['low'])/4, mode='lines', name='Price'))
            if 'volume' in price_data.columns:
                fig_line.add_trace(go.Bar(x=price_data['timestamp'], y=price_data['volume'], name='Volume', yaxis='y2', opacity=0.5))
            else:
                st.write("Volume data is not available for this trading pair.")
            fig_line.update_layout(**layout_adjustments)
            st.plotly_chart(fig_line, use_container_width=True)

    else:
        st.write("No data available for the selected crypto pair.")
