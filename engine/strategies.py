import numpy as np
import pandas as pd

strategy_names = [
    "Moving Average",
    "Moving Average Crossover",
    "Mean Reversion"
]

class TradingStrategy:
    def __init__(self, strategy_name):
        self.strategy_name = strategy_name

    def apply(self, price_df):
        """
        Apply a defined strategy to decide when to buy or sell.
        """
        if self.strategy_name == "Moving Average":
            return self.apply_moving_average_strategy(price_df)
        elif self.strategy_name == "Moving Average Crossover":
            return self.apply_moving_average_crossover_strategy(price_df)
        elif self.strategy_name == "Mean Reversion":
            return self.apply_mean_reversion_strategy(price_df)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy_name}")

    def apply_moving_average_strategy(self, price_df, window=20):
        """
        Apply a simple moving average strategy to decide when to buy or sell.
        Buy when price is lower than the moving average, sell when it's higher.
        """
        # Ensure the DataFrame contains the necessary columns
        required_columns = ['timestamp', 'open', 'high', 'low', 'close']
        if not all(col in price_df.columns for col in required_columns):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")

        # Apply the moving average (SMA)
        price_df['SMA'] = price_df['close'].rolling(window=window).mean()

        # Generate buy/sell signals: Buy when close < SMA, Sell when close > SMA
        price_df['Signal'] = np.where(price_df['close'] > price_df['SMA'], 'Sell', 'Buy')

        return price_df

    def apply_moving_average_crossover_strategy(self, price_df, short_window=20, long_window=50):
        """
        Apply a moving average crossover strategy.
        Buy when short-term moving average crosses above long-term moving average.
        Sell when short-term moving average crosses below long-term moving average.
        """
        # Ensure the DataFrame contains the necessary columns
        required_columns = ['timestamp', 'open', 'high', 'low', 'close']
        if not all(col in price_df.columns for col in required_columns):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")

        # Short-term and long-term moving averages
        price_df['SMA_short'] = price_df['close'].rolling(window=short_window).mean()  # short-term SMA
        price_df['SMA_long'] = price_df['close'].rolling(window=long_window).mean()  # long-term SMA

        # Generate buy/sell signals
        price_df['Signal'] = np.where(price_df['SMA_short'] > price_df['SMA_long'], 'Buy', 'Sell')

        return price_df

    def apply_mean_reversion_strategy(self, price_df, window=20, z_threshold=1.5):
        """
        Apply a mean reversion strategy.
        Buy when Z-score is below -z_threshold (i.e., price is below mean).
        Sell when Z-score is above z_threshold (i.e., price is above mean).
        """
        # Ensure the DataFrame contains the necessary columns
        required_columns = ['timestamp', 'open', 'high', 'low', 'close']
        if not all(col in price_df.columns for col in required_columns):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")

        # Calculate rolling mean and standard deviation
        price_df['Rolling_Mean'] = price_df['close'].rolling(window=window).mean()
        price_df['Rolling_Std'] = price_df['close'].rolling(window=window).std()

        # Calculate Z-score
        price_df['Z_Score'] = (price_df['close'] - price_df['Rolling_Mean']) / price_df['Rolling_Std']

        # Generate buy/sell signals based on Z-score thresholds
        price_df['Signal'] = np.where(price_df['Z_Score'] > z_threshold, 'Sell',
                                np.where(price_df['Z_Score'] < -z_threshold, 'Buy', 'Hold'))

        return price_df

