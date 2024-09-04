from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset, ManageBuyOffer, ManageSellOffer

class TradingBot:
    def __init__(self, stellar_key):
        self.server = Server("https://horizon.stellar.org")
        self.keypair = Keypair.from_secret(stellar_key)
        self.account = self.server.load_account(self.keypair.public_key)
        
    def get_balance(self, asset_code="XLM", asset_issuer=None):
        """
        Get the balance of the specified asset.
        """
        balances = self.account.balances
        for balance in balances:
            if balance['asset_type'] == 'native' and asset_code == 'XLM':
                return float(balance['balance'])
            elif balance['asset_code'] == asset_code and balance['asset_issuer'] == asset_issuer:
                return float(balance['balance'])
        return 0.0

    def place_order(self, base_asset_code, counter_asset_code, amount, price, buy=True):
        """
        Place a buy or sell order.
        """
        base_asset = Asset.native() if base_asset_code == "XLM" else Asset(base_asset_code, self.keypair.public_key)
        counter_asset = Asset.native() if counter_asset_code == "XLM" else Asset(counter_asset_code, self.keypair.public_key)

        # Build the transaction
        transaction = (
            TransactionBuilder(
                source_account=self.account,
                network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,  # Change to Network.PUBLIC_NETWORK_PASSPHRASE for Mainnet
                base_fee=10000
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

    def fetch_trades(self, base_asset_code="XLM", counter_asset_code="USD"):
        """
        Fetch trades made by the bot.
        """
        base_asset = Asset.native() if base_asset_code == "XLM" else Asset(base_asset_code, self.keypair.public_key)
        counter_asset = Asset.native() if counter_asset_code == "XLM" else Asset(counter_asset_code, self.keypair.public_key)

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
