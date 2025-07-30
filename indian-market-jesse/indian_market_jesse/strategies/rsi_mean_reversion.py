"""
RSI Mean Reversion Strategy for Indian Markets

This strategy uses RSI oversold/overbought conditions for entry signals
with proper risk management suited for Indian market conditions.
"""

import numpy as np
from indian_market_jesse.strategies.strategy import Strategy
from indian_market_jesse.indicators import sma, ema, rsi

class RSIMeanReversion(Strategy):
    """
    RSI Mean Reversion Strategy
    
    Strategy Logic:
    - Long when RSI < oversold level and price is above 20-day SMA
    - Short when RSI > overbought level and price is below 20-day SMA
    - Exit when RSI crosses back to neutral zone
    - Stop loss at 1.5% from entry price
    - Take profit at 2.5% from entry price
    """
    
    def __init__(self):
        super().__init__()
        
        # Strategy hyperparameters
        self.hp = {
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'rsi_neutral_low': 45,
            'rsi_neutral_high': 55,
            'sma_period': 20,
            'stop_loss_percent': 0.015,  # 1.5%
            'take_profit_percent': 0.025,  # 2.5%
            'risk_percent': 0.01  # Risk 1% of capital per trade
        }
        
        # Strategy variables
        self.vars = {
            'rsi_values': [],
            'sma_values': [],
            'can_long': True,
            'can_short': True
        }
    
    def should_long(self) -> bool:
        """
        Long condition: RSI oversold + price above SMA + no existing position
        """
        if len(self.vars['rsi_values']) < 2 or len(self.vars['sma_values']) < 1:
            return False
        
        current_rsi = self.vars['rsi_values'][-1]
        current_sma = self.vars['sma_values'][-1]
        current_price = self.current_candle[4]  # Close price
        
        # Check conditions
        rsi_oversold = current_rsi < self.hp['rsi_oversold']
        price_above_sma = current_price > current_sma
        no_position = self.position_type is None
        
        # Reset can_long flag when RSI goes above neutral
        if current_rsi > self.hp['rsi_neutral_high']:
            self.vars['can_long'] = True
        
        # Only allow new long if we haven't recently been in oversold
        if rsi_oversold and not self.vars['can_long']:
            return False
        
        if rsi_oversold and price_above_sma and no_position:
            self.vars['can_long'] = False  # Prevent multiple signals
            return True
        
        return False
    
    def should_short(self) -> bool:
        """
        Short condition: RSI overbought + price below SMA + no existing position
        """
        if len(self.vars['rsi_values']) < 2 or len(self.vars['sma_values']) < 1:
            return False
        
        current_rsi = self.vars['rsi_values'][-1]
        current_sma = self.vars['sma_values'][-1]
        current_price = self.current_candle[4]  # Close price
        
        # Check conditions
        rsi_overbought = current_rsi > self.hp['rsi_overbought']
        price_below_sma = current_price < current_sma
        no_position = self.position_type is None
        
        # Reset can_short flag when RSI goes below neutral
        if current_rsi < self.hp['rsi_neutral_low']:
            self.vars['can_short'] = True
        
        # Only allow new short if we haven't recently been in overbought
        if rsi_overbought and not self.vars['can_short']:
            return False
        
        if rsi_overbought and price_below_sma and no_position:
            self.vars['can_short'] = False  # Prevent multiple signals
            return True
        
        return False
    
    def should_cancel_entry(self) -> bool:
        """
        Cancel entry if RSI moves back to neutral quickly
        """
        return False
    
    def should_exit_position(self) -> bool:
        """
        Exit position when RSI returns to neutral zone
        """
        if self.position_type is None or len(self.vars['rsi_values']) < 1:
            return False
        
        current_rsi = self.vars['rsi_values'][-1]
        
        if self.position_type == 'long':
            # Exit long when RSI goes above neutral high
            return current_rsi > self.hp['rsi_neutral_high']
        elif self.position_type == 'short':
            # Exit short when RSI goes below neutral low
            return current_rsi < self.hp['rsi_neutral_low']
        
        return False
    
    def before(self):
        """
        Called before strategy execution - calculate indicators
        """
        # Get candle data up to current index
        if self.index < self.hp['sma_period']:
            return
        
        # Extract price data
        closes = [candle[4] for candle in self.candles[:self.index + 1]]
        
        # Calculate indicators
        rsi_values = rsi(np.array(closes), self.hp['rsi_period'])
        sma_values = sma(np.array(closes), self.hp['sma_period'])
        
        # Store current values
        if not np.isnan(rsi_values[-1]):
            # Keep only last 3 values to save memory
            self.vars['rsi_values'].append(rsi_values[-1])
            if len(self.vars['rsi_values']) > 3:
                self.vars['rsi_values'].pop(0)
        
        if not np.isnan(sma_values[-1]):
            # Keep only last 3 values to save memory
            self.vars['sma_values'].append(sma_values[-1])
            if len(self.vars['sma_values']) > 3:
                self.vars['sma_values'].pop(0)
    
    def after(self):
        """
        Called after strategy execution - manage positions
        """
        if self.position_type is None:
            return
        
        # Set stop loss and take profit if not already set
        if self.stop_loss is None and self.take_profit is None:
            if self.position_type == 'long':
                self.set_stop_loss(self.entry_price * (1 - self.hp['stop_loss_percent']))
                self.set_take_profit(self.entry_price * (1 + self.hp['take_profit_percent']))
            else:  # short
                self.set_stop_loss(self.entry_price * (1 + self.hp['stop_loss_percent']))
                self.set_take_profit(self.entry_price * (1 - self.hp['take_profit_percent']))
        
        # Check for RSI-based exit
        if self.should_exit_position():
            self.liquidate()
        else:
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
        price_diff = self.entry_price * self.hp['stop_loss_percent']
        
        # Position size
        position_size = risk_amount / price_diff if price_diff > 0 else 0
        
        # Don't risk more than 10% of capital on a single trade
        max_position_value = self.current_capital * 0.1
        max_position_size = max_position_value / self.entry_price
        
        return min(position_size, max_position_size)
    
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
