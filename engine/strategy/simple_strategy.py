class SimpleStrategy:
    def __init__(self, trading_bot):
        self.bot = trading_bot

    def decide_trade(self, price_data):
        """
        Simple strategy to decide when to buy or sell.
        """
        latest_close = price_data['close'].iloc[-1]
        previous_close = price_data['close'].iloc[-2]

        if latest_close > previous_close:
            return {"action": "Buy", "amount": 10, "price": latest_close}
        else:
            return {"action": "Sell", "amount": 10, "price": latest_close}
