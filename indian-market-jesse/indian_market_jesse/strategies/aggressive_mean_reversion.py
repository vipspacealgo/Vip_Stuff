"""
Aggressive Mean Reversion Strategy for NIFTY 15m timeframe

This strategy uses more aggressive RSI levels and shorter periods
to generate more trading opportunities on 15-minute timeframe.
"""

import numpy as np
from indian_market_jesse.strategies.strategy import Strategy
from indian_market_jesse.indicators import sma, ema, rsi

class AggressiveMeanReversion(Strategy):
    """
    Aggressive Mean Reversion Strategy
    
    Strategy Logic:
    - Long when RSI < 40 (more aggressive than 30)
    - Short when RSI > 60 (more aggressive than 70)
    - Exit when RSI crosses back to 50 (neutral)
    - Shorter RSI period (10 instead of 14) for faster signals
    - Stop loss at 2% from entry price
    - Take profit at 3% from entry price
    """
    
    def __init__(self):
        super().__init__()
        
        # More aggressive hyperparameters for 15m timeframe
        self.hp = {
            'rsi_period': 10,           # Shorter for faster signals
            'rsi_oversold': 40,         # Less extreme than 30
            'rsi_overbought': 60,       # Less extreme than 70
            'rsi_neutral': 50,          # Single neutral level
            'sma_period': 10,           # Shorter SMA for trend
            'stop_loss_percent': 0.02,  # 2%
            'take_profit_percent': 0.03, # 3%
            'risk_percent': 0.02        # Risk 2% of capital per trade
        }
        
        # Strategy variables
        self.vars = {
            'rsi_values': [],
            'sma_values': [],
            'entry_rsi': None,
            'trades_today': 0,
            'max_trades_per_day': 3
        }
    
    def should_long(self) -> bool:
        """
        Long condition: RSI oversold + price above SMA
        """
        if len(self.vars['rsi_values']) < 2 or len(self.vars['sma_values']) < 1:
            return False
        
        current_rsi = self.vars['rsi_values'][-1]
        previous_rsi = self.vars['rsi_values'][-2]
        current_sma = self.vars['sma_values'][-1]
        current_price = self.current_candle[4]  # Close price
        
        # Check conditions
        rsi_oversold = current_rsi < self.hp['rsi_oversold']
        rsi_turning_up = current_rsi > previous_rsi  # RSI starting to turn up
        price_above_sma = current_price > current_sma
        no_position = self.position_type is None
        trades_limit_ok = self.vars['trades_today'] < self.vars['max_trades_per_day']
        
        if rsi_oversold and rsi_turning_up and price_above_sma and no_position and trades_limit_ok:
            self.vars['entry_rsi'] = current_rsi
            return True
        
        return False
    
    def should_short(self) -> bool:
        """
        Short condition: RSI overbought + price below SMA
        """
        if len(self.vars['rsi_values']) < 2 or len(self.vars['sma_values']) < 1:
            return False
        
        current_rsi = self.vars['rsi_values'][-1]
        previous_rsi = self.vars['rsi_values'][-2]
        current_sma = self.vars['sma_values'][-1]
        current_price = self.current_candle[4]  # Close price
        
        # Check conditions
        rsi_overbought = current_rsi > self.hp['rsi_overbought']
        rsi_turning_down = current_rsi < previous_rsi  # RSI starting to turn down
        price_below_sma = current_price < current_sma
        no_position = self.position_type is None
        trades_limit_ok = self.vars['trades_today'] < self.vars['max_trades_per_day']
        
        if rsi_overbought and rsi_turning_down and price_below_sma and no_position and trades_limit_ok:
            self.vars['entry_rsi'] = current_rsi
            return True
        
        return False
    
    def should_cancel_entry(self) -> bool:
        """
        Cancel entry if conditions change rapidly
        """
        return False
    
    def should_exit_position(self) -> bool:
        """
        Exit position when RSI returns to neutral (50)
        """
        if self.position_type is None or len(self.vars['rsi_values']) < 1:
            return False
        
        current_rsi = self.vars['rsi_values'][-1]
        
        if self.position_type == 'long':
            # Exit long when RSI goes above 50 or turns down from high levels
            return (current_rsi > self.hp['rsi_neutral'] or 
                   (current_rsi > 65 and len(self.vars['rsi_values']) >= 2 and 
                    current_rsi < self.vars['rsi_values'][-2]))
        elif self.position_type == 'short':
            # Exit short when RSI goes below 50 or turns up from low levels
            return (current_rsi < self.hp['rsi_neutral'] or
                   (current_rsi < 35 and len(self.vars['rsi_values']) >= 2 and 
                    current_rsi > self.vars['rsi_values'][-2]))
        
        return False
    
    def before(self):
        """
        Called before strategy execution - calculate indicators
        """
        # Get candle data up to current index
        if self.index < max(self.hp['rsi_period'], self.hp['sma_period']):
            return
        
        # Extract price data
        closes = [candle[4] for candle in self.candles[:self.index + 1]]
        
        # Calculate indicators
        if len(closes) >= self.hp['rsi_period']:
            rsi_values = rsi(np.array(closes), self.hp['rsi_period'])
            if not np.isnan(rsi_values[-1]):
                self.vars['rsi_values'].append(rsi_values[-1])
                if len(self.vars['rsi_values']) > 5:  # Keep last 5 values
                    self.vars['rsi_values'].pop(0)
        
        if len(closes) >= self.hp['sma_period']:
            sma_values = sma(np.array(closes), self.hp['sma_period'])
            if not np.isnan(sma_values[-1]):
                self.vars['sma_values'].append(sma_values[-1])
                if len(self.vars['sma_values']) > 3:  # Keep last 3 values
                    self.vars['sma_values'].pop(0)
        
        # Reset daily trade count at start of new day
        current_time = self.candles[self.index][0]  # timestamp in ms
        if hasattr(self, '_last_day'):
            current_day = int(current_time / (24 * 60 * 60 * 1000))
            if current_day != self._last_day:
                self.vars['trades_today'] = 0
            self._last_day = current_day
        else:
            self._last_day = int(current_time / (24 * 60 * 60 * 1000))
    
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
        
        # Don't risk more than 20% of capital on a single trade
        max_position_value = self.current_capital * 0.2
        max_position_size = max_position_value / self.entry_price
        
        return min(position_size, max_position_size)
    
    def go_long(self, quantity: float = None, price: float = None) -> None:
        """
        Override to implement custom position sizing and tracking
        """
        if price is None:
            price = self.current_candle[4]
        
        # Call parent method first
        super().go_long(quantity, price)
        
        # Recalculate position size based on risk management
        if quantity is None:
            self.position_size = self.calculate_position_size()
        
        # Increment trade count
        self.vars['trades_today'] += 1
    
    def go_short(self, quantity: float = None, price: float = None) -> None:
        """
        Override to implement custom position sizing and tracking
        """
        if price is None:
            price = self.current_candle[4]
        
        # Call parent method first
        super().go_short(quantity, price)
        
        # Recalculate position size based on risk management
        if quantity is None:
            self.position_size = self.calculate_position_size()
        
        # Increment trade count
        self.vars['trades_today'] += 1