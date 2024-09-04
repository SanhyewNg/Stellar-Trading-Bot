import pandas as pd
from stellar_sdk import Server, Asset
from datetime import datetime

def fetch_price_data(pair, interval="1h", limit=100):
    """
    Fetch historical trade data from Stellar Horizon API and aggregate into OHLC.
    """
    server = Server("https://horizon.stellar.org")

    base_asset_code, counter_asset_code = pair.split('/')
    if base_asset_code == "XLM":
        base_asset = Asset.native()
    else:
        base_asset = Asset(base_asset_code, "ISSUER_ADDRESS")  # Replace with actual issuer

    if counter_asset_code == "USD":
        counter_asset = Asset(counter_asset_code, "GAOHRNEIAIWX42ONJ5R25X3C4R45GGPWPSHODW4ZWNMUJYFXVATF7PWL")  # Example issuer
    else:
        counter_asset = Asset(counter_asset_code, "ISSUER_ADDRESS")  # Replace with actual issuer

    trades = server.trades().for_asset_pair(base=base_asset, counter=counter_asset).limit(limit).order(desc=True).call()

    trade_data = []
    for trade in trades['_embedded']['records']:
        timestamp = datetime.strptime(trade['ledger_close_time'], "%Y-%m-%dT%H:%M:%SZ")
        price = float(trade['price']['n']) / float(trade['price']['d'])
        amount = float(trade['base_amount'])
        trade_data.append({'timestamp': timestamp, 'price': price, 'amount': amount})

    df = pd.DataFrame(trade_data)
    df.set_index('timestamp', inplace=True)

    # Resample to OHLC
    ohlc = df['price'].resample(interval).ohlc()

    return ohlc.reset_index()

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
    
# Example usage:
# trading_bot = TradingBot(stellar_key)
# trading_history = fetch_trading_history(trading_bot)