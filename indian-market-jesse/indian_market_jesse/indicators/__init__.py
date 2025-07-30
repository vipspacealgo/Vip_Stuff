"""
Common technical indicators for Indian market trading
"""
import numpy as np
from typing import Union

def sma(source: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Simple Moving Average
    
    Args:
        source: Array of price values
        period: Period for the moving average
        
    Returns:
        Array of SMA values
    """
    if len(source) < period:
        return np.full(len(source), np.nan)
    
    result = np.full(len(source), np.nan)
    for i in range(period - 1, len(source)):
        result[i] = np.mean(source[i - period + 1:i + 1])
    
    return result

def ema(source: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Exponential Moving Average
    
    Args:
        source: Array of price values
        period: Period for the moving average
        
    Returns:
        Array of EMA values
    """
    if len(source) == 0:
        return np.array([])
    
    alpha = 2 / (period + 1)
    result = np.full(len(source), np.nan)
    result[0] = source[0]
    
    for i in range(1, len(source)):
        result[i] = alpha * source[i] + (1 - alpha) * result[i - 1]
    
    return result

def rsi(source: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Relative Strength Index
    
    Args:
        source: Array of price values
        period: Period for RSI calculation
        
    Returns:
        Array of RSI values
    """
    if len(source) < period + 1:
        return np.full(len(source), np.nan)
    
    # Calculate price changes
    changes = np.diff(source)
    
    # Separate gains and losses
    gains = np.where(changes > 0, changes, 0)
    losses = np.where(changes < 0, -changes, 0)
    
    # Calculate average gains and losses
    avg_gains = np.full(len(changes), np.nan)
    avg_losses = np.full(len(changes), np.nan)
    
    # First average
    avg_gains[period - 1] = np.mean(gains[:period])
    avg_losses[period - 1] = np.mean(losses[:period])
    
    # Smoothed averages
    for i in range(period, len(changes)):
        avg_gains[i] = (avg_gains[i - 1] * (period - 1) + gains[i]) / period
        avg_losses[i] = (avg_losses[i - 1] * (period - 1) + losses[i]) / period
    
    # Calculate RSI
    rs = avg_gains / avg_losses
    rsi_values = 100 - (100 / (1 + rs))
    
    # Prepend NaN for the first value (no change for first price)
    result = np.full(len(source), np.nan)
    result[period:] = rsi_values[period - 1:]
    
    return result

def bollinger_bands(source: np.ndarray, period: int = 20, std: float = 2) -> tuple:
    """
    Bollinger Bands
    
    Args:
        source: Array of price values
        period: Period for the moving average
        std: Standard deviation multiplier
        
    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    middle_band = sma(source, period)
    
    if len(source) < period:
        return (np.full(len(source), np.nan), 
                middle_band, 
                np.full(len(source), np.nan))
    
    upper_band = np.full(len(source), np.nan)
    lower_band = np.full(len(source), np.nan)
    
    for i in range(period - 1, len(source)):
        std_dev = np.std(source[i - period + 1:i + 1])
        upper_band[i] = middle_band[i] + std * std_dev
        lower_band[i] = middle_band[i] - std * std_dev
    
    return upper_band, middle_band, lower_band

def macd(source: np.ndarray, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> tuple:
    """
    MACD (Moving Average Convergence Divergence)
    
    Args:
        source: Array of price values
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        signal_period: Signal line EMA period
        
    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    fast_ema = ema(source, fast_period)
    slow_ema = ema(source, slow_period)
    
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def stochastic(high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int = 14, d_period: int = 3) -> tuple:
    """
    Stochastic Oscillator
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of close prices
        k_period: %K period
        d_period: %D period
        
    Returns:
        Tuple of (%K, %D)
    """
    if len(high) < k_period:
        return (np.full(len(high), np.nan), np.full(len(high), np.nan))
    
    k_values = np.full(len(high), np.nan)
    
    for i in range(k_period - 1, len(high)):
        highest_high = np.max(high[i - k_period + 1:i + 1])
        lowest_low = np.min(low[i - k_period + 1:i + 1])
        
        if highest_high != lowest_low:
            k_values[i] = ((close[i] - lowest_low) / (highest_high - lowest_low)) * 100
        else:
            k_values[i] = 50
    
    d_values = sma(k_values, d_period)
    
    return k_values, d_values

def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Average True Range
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of close prices
        period: Period for ATR calculation
        
    Returns:
        Array of ATR values
    """
    if len(high) < 2:
        return np.full(len(high), np.nan)
    
    # Calculate True Range
    tr = np.full(len(high), np.nan)
    tr[0] = high[0] - low[0]
    
    for i in range(1, len(high)):
        tr1 = high[i] - low[i]
        tr2 = abs(high[i] - close[i - 1])
        tr3 = abs(low[i] - close[i - 1])
        tr[i] = max(tr1, tr2, tr3)
    
    # Calculate ATR using EMA
    return ema(tr, period)

def adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Average Directional Index
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of close prices
        period: Period for ADX calculation
        
    Returns:
        Array of ADX values
    """
    if len(high) < period + 1:
        return np.full(len(high), np.nan)
    
    # Calculate directional movements
    plus_dm = np.full(len(high), 0.0)
    minus_dm = np.full(len(high), 0.0)
    
    for i in range(1, len(high)):
        move_up = high[i] - high[i - 1]
        move_down = low[i - 1] - low[i]
        
        if move_up > move_down and move_up > 0:
            plus_dm[i] = move_up
        
        if move_down > move_up and move_down > 0:
            minus_dm[i] = move_down
    
    # Calculate ATR
    atr_values = atr(high, low, close, period)
    
    # Calculate DI+ and DI-
    plus_di = 100 * ema(plus_dm, period) / atr_values
    minus_di = 100 * ema(minus_dm, period) / atr_values
    
    # Calculate DX
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    
    # Calculate ADX
    adx_values = ema(dx, period)
    
    return adx_values
