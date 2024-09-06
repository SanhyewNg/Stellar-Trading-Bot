import yaml
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset, ManageBuyOffer, ManageSellOffer
from stellar_sdk.exceptions import BadRequestError, ConnectionError, NotFoundError

# Load configuration
with open("config/config.yaml", "r") as file:
    config = yaml.safe_load(file)

class TradingBot:
    def __init__(self, stellar_key, network="testnet"):
        self.keypair = Keypair.from_secret(stellar_key)

        # Choose between testnet and mainnet
        if network == "testnet":
            self.server = Server(horizon_url="https://horizon-testnet.stellar.org")
            self.network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE
        elif network == "mainnet":
            self.server = Server(horizon_url="https://horizon.stellar.org")
            self.network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE

        # Load account from the Stellar network
        try:
            self.account = self.server.load_account(self.keypair.public_key)
        except NotFoundError as e:
            raise ValueError("The Stellar account was not found. Check the Stellar Key or the network.") from e

    def get_balance(self, asset_code="XLM", asset_issuer=None):
        """
        Get the balance of the specified asset.
        """
        try:
            balances = self.account.balances
            for balance in balances:
                if balance['asset_type'] == 'native' and asset_code == 'XLM':
                    return float(balance['balance'])
                elif balance['asset_code'] == asset_code and balance['asset_issuer'] == asset_issuer:
                    return float(balance['balance'])
        except KeyError:
            return 0.0
        return 0.0

    def place_order(self, base_asset_code, counter_asset_code, amount, price, buy=True, base_fee=10000):
        """
        Place a buy or sell order with error handling.
        """
        try:
            base_issuer = config['asset_issuers'].get(base_asset_code)
            counter_issuer = config['asset_issuers'].get(counter_asset_code)

            base_asset = Asset.native() if base_asset_code == "XLM" else Asset(base_asset_code, base_issuer)
            counter_asset = Asset.native() if counter_asset_code == "XLM" else Asset(counter_asset_code, counter_issuer)

            # Build the transaction
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

            # Sign the transaction
            transaction.sign(self.keypair)

            # Submit the transaction
            response = self.server.submit_transaction(transaction)
            return response

        except (BadRequestError, ConnectionError) as e:
            print(f"Error placing order: {e}")
            return None

    def fetch_trades(self, base_asset_code="XLM", counter_asset_code="USD"):
        """
        Fetch trades made by the bot with error handling.
        """
        try:
            base_issuer = config['asset_issuers'].get(base_asset_code)
            counter_issuer = config['asset_issuers'].get(counter_asset_code)

            base_asset = Asset.native() if base_asset_code == "XLM" else Asset(base_asset_code, base_issuer)
            counter_asset = Asset.native() if counter_asset_code == "XLM" else Asset(counter_asset_code, counter_issuer)

            trades = self.server.trades().for_asset_pair(base_asset, counter_asset).limit(200).order(desc=True).call()

            # Process and return trades
            trade_list = []
            for trade in trades['_embedded']['records']:
                trade_list.append({
                    "Date": trade['created_at'],
                    "Base Asset": base_asset_code,
                    "Counter Asset": counter_asset_code,
                    "Amount": float(trade['amount']),
                    "Price": float(trade['price'])
                })

            return trade_list

        except ConnectionError as e:
            print(f"Error fetching trades: {e}")
            return []
