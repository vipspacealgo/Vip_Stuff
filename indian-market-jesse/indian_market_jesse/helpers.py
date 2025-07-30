import datetime
import os
import time
import uuid
from typing import Union, Dict, List

import numpy as np
import pandas as pd
from indian_market_jesse.config import config, timeframes

def generate_unique_id() -> str:
    """
    Generates a unique ID
    """
    return str(uuid.uuid4())

def timestamp_to_datetime(timestamp: int) -> datetime.datetime:
    """
    Convert timestamp to datetime object
    """
    return datetime.datetime.fromtimestamp(timestamp / 1000)

def datetime_to_timestamp(dt: datetime.datetime) -> int:
    """
    Convert datetime to timestamp in milliseconds
    """
    return int(dt.timestamp() * 1000)

def date_to_timestamp(date_str: str) -> int:
    """
    Convert date string to timestamp
    Format: 'YYYY-MM-DD'
    """
    if date_str is None:
        return None
    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    return datetime_to_timestamp(dt)

def timeframe_to_minutes(timeframe: str) -> int:
    """
    Convert timeframe string to minutes
    """
    if timeframe == '1m':
        return 1
    elif timeframe == '3m':
        return 3
    elif timeframe == '5m':
        return 5
    elif timeframe == '15m':
        return 15
    elif timeframe == '30m':
        return 30
    elif timeframe == '1h':
        return 60
    elif timeframe == '2h':
        return 60 * 2
    elif timeframe == '4h':
        return 60 * 4
    elif timeframe == '1D':
        return 60 * 24
    elif timeframe == '1W':
        return 60 * 24 * 7
    else:
        raise ValueError(f'Invalid timeframe: {timeframe}')

def is_market_open(timestamp: int) -> bool:
    """
    Check if the market is open at the given timestamp
    """
    dt = timestamp_to_datetime(timestamp)
    weekday = dt.weekday()
    
    # Check if it's a weekend
    if weekday not in config['env']['exchanges']['NSE']['market_hours']['trading_days']:
        return False
    
    # Check if it's within trading hours
    open_time = datetime.datetime.strptime(
        config['env']['exchanges']['NSE']['market_hours']['open'], 
        '%H:%M'
    ).time()
    close_time = datetime.datetime.strptime(
        config['env']['exchanges']['NSE']['market_hours']['close'], 
        '%H:%M'
    ).time()
    
    current_time = dt.time()
    return open_time <= current_time <= close_time

def is_holiday(timestamp: int) -> bool:
    """
    Check if the day is a market holiday
    Simple implementation - in a production system, you would maintain a list of holidays
    """
    # Placeholder for holiday check logic
    # TODO: Implement a proper holiday calendar
    return False

def get_candle_source(candle: np.ndarray, source_type: str = "close") -> float:
    """
    Return the desired price from a candle
    """
    if source_type == "close":
        return candle[4]
    elif source_type == "open":
        return candle[1]
    elif source_type == "high":
        return candle[2]
    elif source_type == "low":
        return candle[3]
    elif source_type == "hl2":
        return (candle[2] + candle[3]) / 2
    elif source_type == "hlc3":
        return (candle[2] + candle[3] + candle[4]) / 3
    elif source_type == "ohlc4":
        return (candle[1] + candle[2] + candle[3] + candle[4]) / 4
    else:
        raise ValueError(f'Invalid source_type: {source_type}')

def skip_market_closed_candles(candles: np.ndarray) -> np.ndarray:
    """
    Skip candles when market is closed (weekends, holidays, outside trading hours)
    """
    valid_candles = []
    for candle in candles:
        if is_market_open(candle[0]) and not is_holiday(candle[0]):
            valid_candles.append(candle)
    
    if len(valid_candles) == 0:
        return np.array([])
    return np.array(valid_candles)

def get_strategy_dir() -> str:
    """
    Returns the path to the strategies directory
    """
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'strategies'
    )

def get_config(key: str, default=None):
    """
    Access config values with dot notation support
    """
    keys = key.split('.')
    temp = config
    
    for k in keys:
        if k in temp:
            temp = temp[k]
        else:
            return default
            
    return temp
