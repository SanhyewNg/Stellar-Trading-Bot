import yaml
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset, ManageBuyOffer, ManageSellOffer
from stellar_sdk.exceptions import BadRequestError, ConnectionError, NotFoundError
import logging
import pandas as pd

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Load configuration
with open("config/config.yaml", "r") as file:
    config = yaml.safe_load(file)

class TradingBot:
    def __init__(self, stellar_key, network="testnet"):
        self.keypair = Keypair.from_secret(stellar_key)
        print(self.keypair)

        if network == "testnet":
            self.server = Server(horizon_url="https://horizon-testnet.stellar.org")
            self.network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE
        elif network == "mainnet":
            self.server = Server(horizon_url="https://horizon.stellar.org")
            self.network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE

        try:
            self.account = self.server.load_account(self.keypair.public_key)
        except NotFoundError as e:
            raise ValueError("The Stellar account was not found. Check the Stellar Key or the network.") from e

    def get_balance(self, asset_code="XLM", asset_issuer=None):
        try:
            # Fetch account details from the server
            account = self.server.accounts().account_id(self.keypair.public_key).call()
            balances = account['balances']

            # Iterate over the balances and find the required asset
            for balance in balances:
                if balance['asset_type'] == 'native' and asset_code == 'XLM':
                    return float(balance['balance'])
                elif balance['asset_code'] == asset_code and balance['asset_issuer'] == asset_issuer:
                    return float(balance['balance'])
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return 0.0

        return 0.0

    def fetch_trades(self):
        """
        Fetch trading history for the given Stellar key.
        """
        server = self.server
        account_id = self.keypair.public_key  # Use the public key from the TradingBot instance

        try:
            # Fetch all transactions for the account
            transactions = server.transactions().for_account(account_id).limit(200).order(desc=True).call()

            # Extract relevant data from transactions
            trades = []
            for transaction in transactions['_embedded']['records']:
                # Fetch operations for the current transaction
                operations = server.operations().for_transaction(transaction['id']).call()['_embedded']['records']
                for operation in operations:
                    if operation['type'] == 'manage_buy_offer' or operation['type'] == 'manage_sell_offer':
                        trades.append({
                            "Date": transaction['created_at'],
                            "Action": "Buy" if operation['type'] == 'manage_buy_offer' else "Sell",
                            "Amount": float(operation.get('amount', 0)),  # Convert to float, default to 0
                            "Price": float(operation.get('price', 0))  # Convert to float, default to 0
                        })

            # Convert list of trades into a DataFrame
            trades_df = pd.DataFrame(trades)
            return trades_df

        except Exception as e:
            logging.error(f"Error fetching trading history: {e}")
            return pd.DataFrame(columns=["Date", "Action", "Amount", "Price"])
    

    def place_order(self, base_asset_code, counter_asset_code, amount, price, buy=True, base_fee=10000):
        try:
            base_issuer = config['asset_issuers'].get(base_asset_code)
            counter_issuer = config['asset_issuers'].get(counter_asset_code)

            base_asset = Asset.native() if base_asset_code == "XLM" else Asset(base_asset_code, base_issuer)
            counter_asset = Asset.native() if counter_asset_code == "XLM" else Asset(counter_asset_code, counter_issuer)

            transaction = (
                TransactionBuilder(
                    source_account=self.account,
                    network_passphrase=self.network_passphrase,
                    base_fee=base_fee
                )
                .add_operation(
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
            return response

        except Exception as e:
            print(f"Error placing order: {e}")
            return None

    