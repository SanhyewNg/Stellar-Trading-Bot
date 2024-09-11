import numpy as np
import pandas as pd

def apply_moving_average_strategy(df):
    """
    Apply a moving average strategy to decide when to buy or sell.
    """
    # Ensure the DataFrame contains the necessary columns
    required_columns = ['timestamp', 'open', 'high', 'low', 'close']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"DataFrame must contain columns: {required_columns}")

    # Example strategy: Buy if the current price is lower than the moving average, sell if higher
    df['SMA'] = df['close'].rolling(window=20).mean()  # 20-period Simple Moving Average
    df['Signal'] = np.where(df['close'] > df['SMA'], 'Sell', 'Buy')
    
    return df
