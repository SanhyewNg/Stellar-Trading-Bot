import unittest
import pandas as pd
from engine.strategy.simple_strategy import SimpleStrategy

class TestSimpleStrategy(unittest.TestCase):

    def setUp(self):
        # Sample price data for testing
        self.price_data_uptrend = pd.DataFrame({
            'close': [100, 105, 110, 115, 120]
        })

        self.price_data_downtrend = pd.DataFrame({
            'close': [120, 115, 110, 105, 100]
        })

        # Mock trading bot (if needed for initialization, otherwise you can just pass None or a mock object)
        self.mock_bot = None
        self.strategy = SimpleStrategy(self.mock_bot)

    def test_decide_trade_buy(self):
        result = self.strategy.decide_trade(self.price_data_uptrend)
        expected = {"action": "Buy", "amount": 10, "price": 120}
        self.assertEqual(result, expected, "The strategy should decide to Buy when the price is in an uptrend.")

    def test_decide_trade_sell(self):
        result = self.strategy.decide_trade(self.price_data_downtrend)
        expected = {"action": "Sell", "amount": 10, "price": 100}
        self.assertEqual(result, expected, "The strategy should decide to Sell when the price is in a downtrend.")

if __name__ == '__main__':
    unittest.main()
