import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Union, Tuple

import indian_market_jesse.helpers as jh
from indian_market_jesse.config import config

class DataImporter:
    """
    Handles importing and processing market data for the Indian Market
    """
    
    @staticmethod
    def load_csv(file_path: str, symbol: str = None) -> np.ndarray:
        """
        Load candle data from CSV file
        
        Args:
            file_path: Path to the CSV file
            symbol: Symbol name, if not provided, will be extracted from the filename
        
        Returns:
            numpy array of candle data with format [timestamp, open, high, low, close, volume]
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # If symbol not provided, extract from filename
        if symbol is None:
            symbol = os.path.basename(file_path).split('_')[0]
        
        # Read CSV data
        df = pd.read_csv(file_path)
        
        # Ensure required columns exist
        required_columns = ['date', 'open', 'high', 'low', 'close']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in CSV file")
        
        # Add volume column if not exists
        if 'volume' not in df.columns:
            df['volume'] = 0
        
        # Convert date to timestamp
        df['timestamp'] = pd.to_datetime(df['date']).apply(lambda x: int(x.timestamp() * 1000))
        
        # Create candles array
        candles = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].values
        
        return candles
    
    @staticmethod
    def filter_market_hours(candles: np.ndarray) -> np.ndarray:
        """
        Filter candles to include only market hours
        
        Args:
            candles: Numpy array of candle data
        
        Returns:
            Filtered numpy array
        """
        return np.array([c for c in candles if jh.is_market_open(c[0]) and not jh.is_holiday(c[0])])
    
    @staticmethod
    def resample_timeframe(candles: np.ndarray, timeframe: str) -> np.ndarray:
        """
        Resample 1-minute candles to the desired timeframe
        
        Args:
            candles: Numpy array of 1-minute candle data
            timeframe: Target timeframe (e.g. '5m', '1h')
        
        Returns:
            Resampled candle data
        """
        if timeframe == '1m':
            return candles
            
        # Convert to DataFrame for easier resampling
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('datetime', inplace=True)
        
        # Determine the resampling rule
        if timeframe.endswith('m'):
            minutes = int(timeframe[:-1])
            rule = f'{minutes}min'
        elif timeframe.endswith('h'):
            hours = int(timeframe[:-1])
            rule = f'{hours}H'
        elif timeframe == '1D':
            rule = 'D'
        elif timeframe == '1W':
            rule = 'W'
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        # Resample the data
        resampled = df.resample(rule).agg({
            'timestamp': 'first',
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        # Remove rows with NaN values (possible for time periods with no data)
        resampled = resampled.dropna()
        
        return resampled[['timestamp', 'open', 'high', 'low', 'close', 'volume']].values
    
    @staticmethod
    def load_csv_as_dataframe(file_path: str) -> pd.DataFrame:
        """
        Load CSV file as a pandas DataFrame with proper datetime conversion
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        df = pd.read_csv(file_path)
        
        # Ensure date column exists
        if 'date' not in df.columns:
            raise ValueError("Required column 'date' not found in CSV file")
            
        # Convert date to datetime
        df['datetime'] = pd.to_datetime(df['date'])
        
        # Add volume column if not exists
        if 'volume' not in df.columns:
            df['volume'] = 0
            
        return df
        
    @staticmethod
    def import_candles_from_csv(file_path: str, symbol: str, exchange: str, timeframe: str) -> np.ndarray:
        """
        Import candle data from CSV and prepare it for backtest
        
        Args:
            file_path: Path to CSV file
            symbol: Symbol name
            exchange: Exchange name
            timeframe: Target timeframe
        
        Returns:
            Processed candle data
        """
        # Load raw data
        raw_candles = DataImporter.load_csv(file_path, symbol)
        
        # Filter market hours
        filtered_candles = DataImporter.filter_market_hours(raw_candles)
        
        # Resample if necessary
        resampled_candles = DataImporter.resample_timeframe(filtered_candles, timeframe)
        
        return resampled_candles
