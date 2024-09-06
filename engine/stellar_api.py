import yaml
import pandas as pd
from datetime import datetime
from stellar_sdk import Server, Asset
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
with open("config/config.yaml", "r") as file:
    config = yaml.safe_load(file)


def fetch_price_data(pair, interval="1h", limit=100):
    """
    Fetch historical trade data from Stellar Horizon API and aggregate into OHLC.
    """
    server = Server("https://horizon.stellar.org")

    # Log the asset pair being processed
    logging.info(f"Fetching trade data for pair: {pair}, interval: {interval}, limit: {limit}")

    # Split the asset pair (e.g., "XLM/USD")
    base_asset_code, counter_asset_code = pair.split('/')
    logging.info(f"Base asset: {base_asset_code}, Counter asset: {counter_asset_code}")

    # Fetch base and counter assets (with issuer for non-native assets)
    base_asset = Asset.native() if base_asset_code == "XLM" else Asset(base_asset_code, config['asset_issuers'].get(base_asset_code))
    counter_asset = Asset.native() if counter_asset_code == "XLM" else Asset(counter_asset_code, config['asset_issuers'].get(counter_asset_code))

    # Error handling for missing issuers
    if base_asset.code != "XLM" and not config['asset_issuers'].get(base_asset_code):
        logging.error(f"Missing issuer for base asset: {base_asset_code}")
        raise ValueError(f"Missing issuer for base asset: {base_asset_code}")
    if counter_asset.code != "XLM" and not config['asset_issuers'].get(counter_asset_code):
        logging.error(f"Missing issuer for counter asset: {counter_asset_code}")
        raise ValueError(f"Missing issuer for counter asset: {counter_asset_code}")

    try:
        # Fetch trades for the asset pair
        logging.info(f"Fetching trades for {base_asset_code}/{counter_asset_code}")
        trades = server.trades().for_asset_pair(base=base_asset, counter=counter_asset).limit(limit).order(desc=True).call()
        
        trade_data = []
        for trade in trades['_embedded']['records']:
            # Convert ledger close time to datetime
            timestamp = datetime.strptime(trade['ledger_close_time'], "%Y-%m-%dT%H:%M:%SZ")
            price = float(trade['price']['n']) / float(trade['price']['d'])
            amount = float(trade['base_amount'])
            trade_data.append({'timestamp': timestamp, 'price': price, 'amount': amount})
            # print(trade)

        # If no trades found, return an empty DataFrame
        if not trade_data:
            logging.warning("No trades found.")
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close'])

        # Create a DataFrame from trade data
        logging.info(f"Processing {len(trade_data)} trades.")
        df = pd.DataFrame(trade_data)
        df.set_index('timestamp', inplace=True)

        # Resample the trade data to OHLC (Open, High, Low, Close) using the specified interval
        ohlc = df['price'].resample(interval).ohlc()
        logging.info(f"OHLC data generated for {pair}.")
        print(ohlc)

        return ohlc.reset_index()

    except Exception as e:
        logging.error(f"Error fetching price data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error


def fetch_trading_history(trading_bot):
    """
    Fetch trading history for the given Stellar key.
    """
    server = Server("https://horizon.stellar.org")
    account_id = trading_bot.keypair.public_key  # Use the public key from the TradingBot instance

    try:
        # Fetch all transactions for the account
        transactions = server.transactions().for_account(account_id).limit(200).order(desc=True).call()

        # Extract relevant data from transactions
        trades = []
        for transaction in transactions['_embedded']['records']:
            if 'operations' in transaction:
                for operation in transaction['operations']:
                    if operation['type'] == 'manage_buy_offer' or operation['type'] == 'manage_sell_offer':
                        trades.append({
                            "Date": transaction['created_at'],
                            "Action": "Buy" if operation['type'] == 'manage_buy_offer' else "Sell",
                            "Amount": float(operation['amount']),  # Convert to float
                            "Price": float(operation.get('price', 0))  # Convert to float, default to 0
                        })

        # Convert list of trades into a DataFrame
        trades_df = pd.DataFrame(trades)
        return trades_df

    except Exception as e:
        print(f"Error fetching trading history: {e}")
        return pd.DataFrame(columns=["Date", "Action", "Amount", "Price"])
