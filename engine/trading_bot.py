import yaml
import requests
import logging
import numpy as np
import pandas as pd
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset, ManageBuyOffer, ManageSellOffer
from stellar_sdk.exceptions import BadRequestError, ConnectionError, NotFoundError

import engine.utils as utils
from engine.strategies import apply_moving_average_strategy
from engine.strategies import strategy_names, TradingStrategy

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
with open("config/config.yaml", "r") as file:
    config = yaml.safe_load(file)

class TradingBot:
    def __init__(self, stellar_key, network="testnet"):
        self.keypair = Keypair.from_secret(stellar_key)
        self.config = config  # Use the loaded config

        # Initialize the server and network passphrase
        if network == "testnet":
            self.server = Server(horizon_url="https://horizon-testnet.stellar.org")
            self.network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE
        elif network == "mainnet":
            self.server = Server(horizon_url="https://horizon.stellar.org")
            self.network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE
        else:
            raise ValueError("Unsupported network. Please choose 'testnet' or 'mainnet'.")

        try:
            self.account = self.server.load_account(self.keypair.public_key)
            logging.info("Successfully loaded account.")
        except NotFoundError as e:
            logging.error("The Stellar account was not found. Check the Stellar Key or the network.")
            raise e
    
    def get_balances(self):
        try:
            account = self.server.accounts().account_id(self.keypair.public_key).call()
            balances = account['balances']

            balance_data = []
            asset_issuers = self.config.get('asset_issuers', {})

            for asset_code, asset_issuer in asset_issuers.items():
                for balance in balances:
                    # print(balance)
                    current_asset_code = "XLM" if balance['asset_type'] == 'native' else balance.get('asset_code', 'Unknown')
                    current_asset_issuer = balance.get('asset_issuer', 'Stellar Foundation')

                    if current_asset_code == asset_code and current_asset_issuer == asset_issuer:
                        # price, change_24h = utils.get_asset_price_and_change(current_asset_code.lower())
                        # value_usd = float(balance['balance']) * price

                        balance_data.append({
                            'Asset': current_asset_code,
                            # 'Issuer': current_asset_issuer[:8]+".."+current_asset_issuer[-8:] if len(current_asset_issuer)>16 else current_asset_issuer,
                            # 'Issuer': current_asset_issuer,
                            'Balance': float(balance['balance']),
                            # 'Value (USD)': value_usd,
                            # 'Change (24h)': change_24h
                        })

            logging.info(f"Fetched balances: {pd.DataFrame(balance_data)}")
            return balance_data

        except Exception as e:
            logging.error(f"Error fetching balances: {e}")
            return pd.DataFrame()

    def fetch_trading_history(self):
        try:
            transactions = self.server.transactions().for_account(self.keypair.public_key).limit(200).order(desc=True).call()
            trades = []

            for transaction in transactions['_embedded']['records']:
                operations = self.server.operations().for_transaction(transaction['id']).call()['_embedded']['records']
                
                for operation in operations:
                    if operation['type'] in ['manage_buy_offer', 'manage_sell_offer']:
                        action = "Buy" if operation['type'] == 'manage_buy_offer' else "Sell"
                        buy_asset = operation.get('buying_asset_code', 'XLM')
                        sell_asset = operation.get('selling_asset_code', 'XLM')
                        amount = float(operation.get('amount', 0))
                        price = float(operation.get('price', 0))
                        total = amount * price

                        trades.append({
                            "Time": transaction['created_at'],
                            "Sell": sell_asset,
                            "Buy": buy_asset,
                            "Amount": amount,
                            "Price": price,
                            "Total": total
                        })

            trades_df = pd.DataFrame(trades) if trades else pd.DataFrame(columns=["Time", "Sell", "Buy", "Amount", "Price", "Total"])
            logging.info(f"Fetched trades: {trades_df}")
            return trades_df

        except Exception as e:
            logging.error(f"Error fetching trading history: {e}")
            return pd.DataFrame(columns=["Time", "Sell", "Buy", "Amount", "Price", "Total"])


    def place_order(self, base_asset_code, counter_asset_code, amount, price, buy=True, base_fee=10000):
        try:
            base_issuer = self.config['asset_issuers'].get(base_asset_code)
            counter_issuer = self.config['asset_issuers'].get(counter_asset_code)

            base_asset = Asset.native() if base_asset_code == "XLM" else Asset(base_asset_code, base_issuer)
            counter_asset = Asset.native() if counter_asset_code == "XLM" else Asset(counter_asset_code, counter_issuer)

            transaction = (
                TransactionBuilder(
                    source_account=self.account,
                    network_passphrase=self.network_passphrase,
                    base_fee=base_fee
                )
                .append_operation(
                    ManageBuyOffer(
                        selling=base_asset,
                        buying=counter_asset,
                        amount=str(amount),
                        price=str(price)
                    ) if buy else ManageSellOffer(
                        selling=counter_asset,
                        buying=base_asset,
                        amount=str(amount),
                        price=str(price)
                    )
                )
                .set_timeout(30)
                .build()
            )

            transaction.sign(self.keypair)
            response = self.server.submit_transaction(transaction)
            logging.info(f"Order placed: {response}")
            return response

        except Exception as e:
            logging.error(f"Error placing order: {e}")
            return None

    def do_exchange(self, base_asset_code, counter_asset_code, price_df, balances, trading_strategy):
        try:
            # Ensure price_df is a DataFrame
            if not isinstance(price_df, pd.DataFrame):
                raise ValueError("price_df should be a pandas DataFrame")

            # Apply the moving average strategy
            price_df = trading_strategy.apply(price_df)

            # Get the latest trading signal
            latest_signal = price_df.iloc[-1]['Signal']
            latest_price = price_df.iloc[-1]['close']

            # Fetch the available balance for the base asset
            base_balance = next((item['Balance'] for item in balances if item['Asset'] == base_asset_code), 0)
            counter_balance = next((item['Balance'] for item in balances if item['Asset'] == counter_asset_code), 0)

            # Define the trade amount and price
            amount = min(float(base_balance) * 0.1, 100)  # Example: Use 10% of the balance or a maximum of 100
            if amount <= 0:
                logging.warning("Insufficient balance to trade.")
                return

            # Execute the trade based on the signal
            if latest_signal == 'Buy':
                # Buy counter_asset using base_asset
                if base_balance > 0:
                    response = self.place_order(
                        base_asset_code=base_asset_code,
                        counter_asset_code=counter_asset_code,
                        amount=amount,
                        price=latest_price,
                        buy=True
                    )
                    if response:
                        logging.info(f"Buy order placed: {response}")
            elif latest_signal == 'Sell':
                # Sell base_asset to get counter_asset
                if counter_balance > 0:
                    response = self.place_order(
                        base_asset_code=base_asset_code,
                        counter_asset_code=counter_asset_code,
                        amount=amount,
                        price=latest_price,
                        buy=False
                    )
                    if response:
                        logging.info(f"Sell order placed: {response}")

            # Update trading history
            trades_df = self.fetch_trading_history()
            logging.info(f"Updated trading history: {trades_df}")

        except Exception as e:
            logging.error(f"Error in do_exchange: {e}")