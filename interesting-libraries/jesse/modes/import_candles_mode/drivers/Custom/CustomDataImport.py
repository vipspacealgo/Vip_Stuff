import os
import pandas as pd
import jesse.helpers as jh
from jesse.modes.import_candles_mode.drivers.interface import CandleExchange
from typing import List, Dict, Any


class CustomDataImport(CandleExchange):
    def __init__(self):
        super().__init__(
            name='Custom Data Import',
            count=1000,  # Number of candles to process at once
            rate_limit_per_second=10,  # No rate limit for local files
            backup_exchange_class=None
        )
        self.custom_data_path = os.path.join(os.getcwd(), 'custom_data')
        if not os.path.exists(self.custom_data_path):
            os.makedirs(self.custom_data_path)

    def fetch(self, symbol: str, start_timestamp: int, timeframe: str = '1m') -> List[Dict[str, Any]]:
        """
        Fetch candles from custom CSV/JSON files
        Expected CSV format: timestamp,open,high,low,close,volume
        """
        candles = []
        
        # Look for CSV file with symbol name
        csv_file = os.path.join(self.custom_data_path, f'{symbol}.csv')
        json_file = os.path.join(self.custom_data_path, f'{symbol}.json')
        
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            candles = self._process_dataframe(df, symbol)
        elif os.path.exists(json_file):
            df = pd.read_json(json_file)
            candles = self._process_dataframe(df, symbol)
        else:
            # If no file found, return empty list
            return []
        
        # Filter candles based on start_timestamp
        filtered_candles = [
            candle for candle in candles 
            if candle['timestamp'] >= start_timestamp
        ]
        
        return filtered_candles[:self.count]  # Return up to count candles

    def _process_dataframe(self, df: pd.DataFrame, symbol: str) -> List[Dict[str, Any]]:
        """Process pandas dataframe into Jesse candle format"""
        candles = []
        
        # Ensure required columns exist
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Convert timestamp to milliseconds if needed
        if df['timestamp'].dtype == 'object':
            # Try to parse datetime strings
            df['timestamp'] = pd.to_datetime(df['timestamp']).astype('int64') // 10**6
        elif df['timestamp'].max() < 10**12:  # If timestamp is in seconds
            df['timestamp'] = df['timestamp'] * 1000
        
        for _, row in df.iterrows():
            candle = {
                'id': jh.generate_unique_id(),
                'exchange': 'Custom',
                'symbol': symbol,
                'timeframe': '1m',
                'timestamp': int(row['timestamp']),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            }
            candles.append(candle)
        
        return sorted(candles, key=lambda x: x['timestamp'])

    def get_starting_time(self, symbol: str) -> int:
        """Get the earliest timestamp available for a symbol"""
        csv_file = os.path.join(self.custom_data_path, f'{symbol}.csv')
        json_file = os.path.join(self.custom_data_path, f'{symbol}.json')
        
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
        elif os.path.exists(json_file):
            df = pd.read_json(json_file)
        else:
            return None
        
        if 'timestamp' not in df.columns:
            return None
        
        # Convert timestamp to milliseconds if needed
        if df['timestamp'].dtype == 'object':
            df['timestamp'] = pd.to_datetime(df['timestamp']).astype('int64') // 10**6
        elif df['timestamp'].max() < 10**12:
            df['timestamp'] = df['timestamp'] * 1000
        
        return int(df['timestamp'].min())

    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols from custom data files"""
        symbols = []
        
        if not os.path.exists(self.custom_data_path):
            return symbols
        
        for filename in os.listdir(self.custom_data_path):
            if filename.endswith('.csv') or filename.endswith('.json'):
                symbol = filename.rsplit('.', 1)[0]  # Remove extension
                symbols.append(symbol)
        
        return symbols