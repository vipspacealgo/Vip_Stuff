"""
Sample Moving Average Crossover Strategy for Indian Markets

This strategy demonstrates:
1. Using multiple timeframes
2. Moving average crossover signals
3. Risk management with stop loss
4. Position sizing
"""

import numpy as np
from indian_market_jesse.strategies.strategy import Strategy
from indian_market_jesse.indicators import sma, ema, rsi

class MovingAverageCrossover(Strategy):
    """
    A simple moving average crossover strategy
    
    Strategy Logic:
    - Long when fast MA crosses above slow MA and RSI < 70
    - Short when fast MA crosses below slow MA and RSI > 30
    - Stop loss at 2% from entry price
    - Take profit at 3% from entry price
    """
    
    def __init__(self):
        super().__init__()
        
        # Strategy hyperparameters
        self.hp = {
            'fast_ma_period': 10,
            'slow_ma_period': 20,
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'stop_loss_percent': 0.02,  # 2%
            'take_profit_percent': 0.03,  # 3%
            'risk_percent': 0.02  # Risk 2% of capital per trade
        }
        
        # Strategy variables
        self.vars = {
            'fast_ma': [],
            'slow_ma': [],
            'rsi_values': [],
            'prev_fast_ma': None,
            'prev_slow_ma': None
        }
    
    def should_long(self) -> bool:
        """
        Long condition: Fast MA crosses above Slow MA and RSI < overbought level
        """
        if len(self.vars['fast_ma']) < 2 or len(self.vars['slow_ma']) < 2:
            return False
        
        # Current and previous values
        current_fast = self.vars['fast_ma'][-1]
        current_slow = self.vars['slow_ma'][-1]
        prev_fast = self.vars['fast_ma'][-2]
        prev_slow = self.vars['slow_ma'][-2]
        
        # Check for crossover
        crossover = (prev_fast <= prev_slow and current_fast > current_slow)
        
        # Check RSI condition
        rsi_condition = True
        if len(self.vars['rsi_values']) > 0:
            current_rsi = self.vars['rsi_values'][-1]
            if not np.isnan(current_rsi):
                rsi_condition = current_rsi < self.hp['rsi_overbought']
        
        return crossover and rsi_condition and self.position_type is None
    
    def should_short(self) -> bool:
        """
        Short condition: Fast MA crosses below Slow MA and RSI > oversold level
        """
        if len(self.vars['fast_ma']) < 2 or len(self.vars['slow_ma']) < 2:
            return False
        
        # Current and previous values
        current_fast = self.vars['fast_ma'][-1]
        current_slow = self.vars['slow_ma'][-1]
        prev_fast = self.vars['fast_ma'][-2]
        prev_slow = self.vars['slow_ma'][-2]
        
        # Check for crossover
        crossover = (prev_fast >= prev_slow and current_fast < current_slow)
        
        # Check RSI condition
        rsi_condition = True
        if len(self.vars['rsi_values']) > 0:
            current_rsi = self.vars['rsi_values'][-1]
            if not np.isnan(current_rsi):
                rsi_condition = current_rsi > self.hp['rsi_oversold']
        
        return crossover and rsi_condition and self.position_type is None
    
    def should_cancel_entry(self) -> bool:
        """
        Cancel entry if market conditions change
        """
        return False
    
    def before(self):
        """
        Called before strategy execution - calculate indicators
        """
        # Get candle data up to current index
        if self.index < self.hp['slow_ma_period']:
            return
        
        # Extract price data
        closes = [candle[4] for candle in self.candles[:self.index + 1]]
        highs = [candle[2] for candle in self.candles[:self.index + 1]]
        lows = [candle[3] for candle in self.candles[:self.index + 1]]
        
        # Calculate indicators
        fast_ma_values = sma(np.array(closes), self.hp['fast_ma_period'])
        slow_ma_values = sma(np.array(closes), self.hp['slow_ma_period'])
        rsi_values = rsi(np.array(closes), self.hp['rsi_period'])
        
        # Store current values
        if not np.isnan(fast_ma_values[-1]):
            self.vars['fast_ma'].append(fast_ma_values[-1])
        if not np.isnan(slow_ma_values[-1]):
            self.vars['slow_ma'].append(slow_ma_values[-1])
        if not np.isnan(rsi_values[-1]):
            self.vars['rsi_values'].append(rsi_values[-1])
    
    def after(self):
        """
        Called after strategy execution - manage positions
        """
        if self.position_type is None:
            return
        
        # Update stop loss and take profit if not set
        if self.stop_loss is None and self.take_profit is None:
            if self.position_type == 'long':
                self.set_stop_loss(self.entry_price * (1 - self.hp['stop_loss_percent']))
                self.set_take_profit(self.entry_price * (1 + self.hp['take_profit_percent']))
            else:  # short
                self.set_stop_loss(self.entry_price * (1 + self.hp['stop_loss_percent']))
                self.set_take_profit(self.entry_price * (1 - self.hp['take_profit_percent']))
        
        # Update position (check stop loss and take profit)
        self.update_position()
    
    def calculate_position_size(self) -> float:
        """
        Calculate position size based on risk management
        """
        if self.position_type is None:
            return 0
        
        # Risk amount in currency
        risk_amount = self.current_capital * self.hp['risk_percent']
        
        # Price difference for stop loss
        if self.position_type == 'long':
            price_diff = self.entry_price * self.hp['stop_loss_percent']
        else:
            price_diff = self.entry_price * self.hp['stop_loss_percent']
        
        # Position size
        position_size = risk_amount / price_diff if price_diff > 0 else 0
        
        return min(position_size, self.current_capital / self.entry_price)
    
    def go_long(self, quantity: float = None, price: float = None) -> None:
        """
        Override to implement custom position sizing
        """
        if price is None:
            price = self.current_candle[4]
        
        # Call parent method first
        super().go_long(quantity, price)
        
        # Recalculate position size based on risk management
        if quantity is None:
            self.position_size = self.calculate_position_size()
    
    def go_short(self, quantity: float = None, price: float = None) -> None:
        """
        Override to implement custom position sizing
        """
        if price is None:
            price = self.current_candle[4]
        
        # Call parent method first
        super().go_short(quantity, price)
        
        # Recalculate position size based on risk management
        if quantity is None:
            self.position_size = self.calculate_position_size()
