import yaml
import pandas as pd
from datetime import datetime, timedelta
from stellar_sdk import Server, Asset
import logging
import pytz

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
with open("config/config.yaml", "r") as file:
    config = yaml.safe_load(file)


def fetch_exchange_data(network_url="https://horizon.stellar.org", 
                     crypto_pair="XLM/USDC", 
                     interval="1min", 
                     num_points=20):
    """
    Fetch historical trade data from Stellar Horizon API and aggregate into OHLC.

    Parameters:
    - network_url: URL of the Stellar Horizon API
    - crypto_pair: Trading pair in the format "BASE/QUOTE"
    - interval: Time interval for resampling (e.g., "1m", "5m", "15m", "1h", "1d", "1w")
    - num_points: Number of intervals (candlesticks) to display

    Returns:
    - DataFrame with OHLC data
    """
    server = Server(network_url)

    logging.info(f"Fetching trade data for pair: {crypto_pair}, interval: {interval}, num_points: {num_points}")

    base_asset_code, counter_asset_code = crypto_pair.split('/')
    logging.info(f"Base asset: {base_asset_code}, Counter asset: {counter_asset_code}")

    base_asset = Asset.native() if base_asset_code == "XLM" else Asset(base_asset_code, config['asset_issuers'].get(base_asset_code))
    print(counter_asset_code)
    counter_asset = Asset.native() if counter_asset_code == "XLM" else Asset(counter_asset_code, config['asset_issuers'].get(counter_asset_code))

    try:
        interval_duration = pd.to_timedelta(interval)
        end_time = datetime.utcnow().replace(tzinfo=pytz.utc)
        start_time = end_time - interval_duration * num_points

        logging.info(f"Fetching trades for {base_asset_code}/{counter_asset_code} from {start_time} to {end_time}")

        all_trade_data = []
        cursor = None
        stop_fetching = False  # Flag to stop fetching once we go beyond the start time
        while not stop_fetching:
            # Fetch a maximum of 200 trades per request (API limit)
            trades_request = server.trades().for_asset_pair(base=base_asset, counter=counter_asset).order(desc=True).limit(200)
            if cursor:
                trades_request = trades_request.cursor(cursor)

            trades = trades_request.call()

            trade_data = []
            for trade in trades['_embedded']['records']:
                timestamp = datetime.strptime(trade['ledger_close_time'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
                
                if timestamp < start_time:  # Stop if the trade is older than the start time
                    stop_fetching = True
                    break  # Break the inner loop, but outer loop will terminate due to flag
                
                price = float(trade['price']['n']) / float(trade['price']['d'])
                amount = float(trade.get('base_amount', 0))
                volume = float(trade.get('base_amount', 0))
                trade_data.append({'timestamp': timestamp, 'price': price, 'amount': amount, 'volume': volume})

            all_trade_data.extend(trade_data)
            
            if len(trades['_embedded']['records']) < 200:  # Break if fewer than 200 trades returned
                break
            
            cursor = trades['_embedded']['records'][-1]['paging_token']  # Update the cursor for the next request

        if not all_trade_data:
            logging.warning("No trades found.")
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        logging.info(f"Processing {len(all_trade_data)} trades.")
        df = pd.DataFrame(all_trade_data)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)

        ohlc = df['price'].resample(interval).ohlc()
        volume = df['volume'].resample(interval).sum()
        ohlc['volume'] = volume

        ohlc['open'] = ohlc['close'].shift(1)
        ohlc['open'] = ohlc['open'].ffill()
        ohlc['open'] = ohlc['open'].fillna(ohlc['close'])

        if len(ohlc) > num_points:
            ohlc = ohlc.iloc[-num_points:]

        logging.info(f"OHLC data generated for {crypto_pair}.")
        return ohlc.reset_index()

    except Exception as e:
        logging.error(f"Error fetching price data: {e}")
        return pd.DataFrame()
