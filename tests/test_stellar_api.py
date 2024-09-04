import unittest
from unittest.mock import patch, MagicMock
from engine.stellar_api import fetch_price_data, fetch_trading_history
from stellar_sdk import Asset

class TestStellarAPI(unittest.TestCase):

    @patch('engine.stellar_api.Server')
    def test_fetch_price_data(self, MockServer):
        # Mock the Server and its methods
        mock_server = MockServer.return_value
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'prices': [
                {'timestamp': '2024-01-01T00:00:00Z', 'open': '0.10', 'high': '0.15', 'low': '0.09', 'close': '0.12'}
            ]
        }
        mock_server.requests.get.return_value = mock_response

        # Test fetch_price_data
        crypto_pair = 'XLM/USD'
        price_data = fetch_price_data(crypto_pair)

        # Assertions
        self.assertIsInstance(price_data, pd.DataFrame)
        self.assertEqual(len(price_data), 1)
        self.assertIn('timestamp', price_data.columns)
        self.assertIn('close', price_data.columns)
    
    @patch('engine.stellar_api.Server')
    @patch('engine.stellar_api.TradingBot')  # Mock TradingBot if it's used in fetch_trading_history
    def test_fetch_trading_history(self, MockTradingBot, MockServer):
        # Mock the Server and its methods
        mock_server = MockServer.return_value
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'trades': [
                {'Date': '2024-01-01', 'Action': 'Buy', 'Price': '0.10', 'Amount': '100'}
            ]
        }
        mock_server.requests.get.return_value = mock_response

        # Mock the TradingBot instance
        mock_bot = MockTradingBot.return_value
        
        # Test fetch_trading_history
        trading_history = fetch_trading_history(mock_bot)

        # Assertions
        self.assertIsInstance(trading_history, pd.DataFrame)
        self.assertEqual(len(trading_history), 1)
        self.assertIn('Date', trading_history.columns)
        self.assertIn('Action', trading_history.columns)

if __name__ == '__main__':
    unittest.main()
