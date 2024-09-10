import yaml
import requests
import logging
import pandas as pd
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset, ManageBuyOffer, ManageSellOffer
from stellar_sdk.exceptions import BadRequestError, ConnectionError, NotFoundError

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

    def get_asset_price_and_change(self, asset_code):
        asset_id_mapping = {
            "xlm": "stellar",
            "usdc": "usd-coin",
            "btc": "bitcoin",
            "eth": "ethereum",
            "bnb": "binancecoin",
            "xrp": "ripple",
            "doge": "dogecoin",
            "ada": "cardano",
            "sol": "solana",
            "dot": "polkadot",
            "uni": "uniswap",
            "link": "chainlink",
            "ltc": "litecoin",
            "mkr": "maker",
            "bch": "bitcoin-cash",
            "trx": "tron",
            "matic": "polygon",
            "eos": "eos",
            "ltc": "litecoin",
            "shib": "shiba-inu",
            "avax": "avalanche",
            "xmr": "monero",
            "algo": "algorand",
            "chz": "chiliz",
            "xtz": "tezos",
            "xlm": "stellar",
            "usdt": "tether",
            "celo": "celo",
            "luna": "terra-luna",
            "icp": "internet-computer",
            "doge": "dogecoin",
            "neo": "neo",
            "qtum": "qtum",
            "hbar": "hedera",
            "ren": "ren",
            "1inch": "1inch",
            "sushi": "sushiswap",
            "yfi": "yearn-finance",
            "zrx": "0x",
            "nmr": "numeraire",
            "dcr": "decred",
            "bnt": "bancor",
            "iost": "iost",
            "xsushi": "xsushi",
            "crv": "curve-dao-token",
            "sxp": "swipe",
            "cvc": "civic",
            "stk": "stk",
            "chz": "chiliz",
            "aave": "aave",
            "doge": "dogecoin",
            "fil": "filecoin",
            "bat": "basic-attention-token",
            "sand": "the-sandbox",
            "enj": "enjincoin",
            "hbar": "hedera",
            "elrond": "elrond-erd-2",
            "rune": "thorchain",
            "yfi": "yearn-finance",
            "ftm": "fantom",
            "lrc": "loopring",
            "ltc": "litecoin",
            "zil": "zilliqa"
        }


        try:
            asset_id_mapped = asset_id_mapping.get(asset_code.lower(), asset_code.lower())
            
            if not asset_id_mapped:
                raise ValueError(f"Asset code {asset_code} is not supported")
            
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={asset_id_mapped}&vs_currencies=usd&include_24hr_change=true"
            response = requests.get(url).json()
            
            price = response[asset_id_mapped]['usd']
            change_24h = response[asset_id_mapped]['usd_24h_change']
            
            logging.info(f"Fetched price for {asset_code}: {price} USD, 24h change: {change_24h}%")
            return price, change_24h
        except Exception as e:
            logging.error(f"Error fetching price for {asset_code}: {e}")
            return 0.0, 0.0

    def get_balances(self):
        try:
            account = self.server.accounts().account_id(self.keypair.public_key).call()
            balances = account['balances']

            balance_data = []
            asset_issuers = self.config.get('asset_issuers', {})

            # for asset_code, asset_issuer in asset_issuers.items():
            for balance in balances:
                # print(balance)
                current_asset_code = "XLM" if balance['asset_type'] == 'native' else balance.get('asset_code', 'Unknown')
                current_asset_issuer = balance.get('asset_issuer', 'Stellar Foundation')

                # if current_asset_code == asset_code and current_asset_issuer == asset_issuer:
                price, change_24h = self.get_asset_price_and_change(current_asset_code.lower())
                value_usd = float(balance['balance']) * price

                balance_data.append({
                    'Asset': current_asset_code,
                    # 'Issuer': current_asset_issuer,
                    'Balance': float(balance['balance']),
                    'Value (USD)': value_usd,
                    'Change (24h)': change_24h
                })

            balances_df = pd.DataFrame(balance_data)
            logging.info(f"Fetched balances: {balances_df}")
            return balances_df

        except Exception as e:
            logging.error(f"Error fetching balances: {e}")
            return pd.DataFrame()

    def fetch_trades(self):
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
            logging.info(f"Order placed: {response}")
            return response

        except Exception as e:
            logging.error(f"Error placing order: {e}")
            return None
