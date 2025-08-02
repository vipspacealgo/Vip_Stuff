"""
NIFTY Futures Mean Reversion Strategy

This strategy is specifically designed for NIFTY 50 futures trading with:
- Proper lot size handling (75 shares per lot)
- Margin-based position sizing
- Realistic leverage calculations
"""

import numpy as np
from indian_market_jesse.strategies.strategy import Strategy
from indian_market_jesse.indicators import sma, ema, rsi

class NiftyFuturesMeanReversion(Strategy):
    """
    NIFTY Futures Mean Reversion Strategy
    
    Strategy Logic:
    - Long when RSI < 40 and price above 20-SMA
    - Short when RSI > 60 and price below 20-SMA
    - Exit when RSI crosses back to 50 (neutral)
    - Proper futures lot sizing (75 shares per lot)
    - Margin-based position sizing with leverage
    """
    
    def __init__(self):
        super().__init__()
        
        # NIFTY Futures specifications
        self.hp = {
            'lot_size': 75,                 # NIFTY futures lot size
            'margin_rate': 0.11,            # 11% margin requirement
            'max_lots': 3,                  # Maximum lots per trade
            'rsi_period': 14,
            'rsi_oversold': 40,
            'rsi_overbought': 60,
            'rsi_neutral': 50,
            'sma_period': 20,
            'stop_loss_percent': 0.015,     # 1.5%
            'take_profit_percent': 0.025,   # 2.5%
            'risk_percent': 0.9             # Risk 90% of available capital for margin
        }
        
        # Strategy variables
        self.vars = {
            'rsi_values': [],
            'sma_values': [],
            'available_margin': 0,
            'used_margin': 0,
            'lots_traded': 0
        }
    
    def calculate_contract_value(self, price: float) -> float:
        """Calculate total contract value for one lot"""
        return price * self.hp['lot_size']
    
    def calculate_margin_required(self, price: float, lots: int = 1) -> float:
        """Calculate margin required for given lots"""
        contract_value = self.calculate_contract_value(price)
        return contract_value * self.hp['margin_rate'] * lots
    
    def calculate_max_lots(self, price: float) -> int:
        """Calculate maximum lots that can be traded with available capital"""
        margin_per_lot = self.calculate_margin_required(price, 1)
        available_for_trading = self.current_capital * self.hp['risk_percent']
        max_affordable_lots = int(available_for_trading // margin_per_lot)
        return min(max_affordable_lots, self.hp['max_lots'])
    
    def should_long(self) -> bool:
        """Long condition: RSI oversold + sufficient margin"""
        if len(self.vars['rsi_values']) < 1:
            return False
        
        current_rsi = self.vars['rsi_values'][-1]
        current_price = self.current_candle[4]  # Close price
        
        # Check conditions
        rsi_oversold = current_rsi < self.hp['rsi_oversold']
        no_position = self.position_type is None
        
        # Check if we have enough margin
        max_lots = self.calculate_max_lots(current_price)
        has_margin = max_lots >= 1
        
        return (rsi_oversold and no_position and has_margin)
    
    def should_short(self) -> bool:
        """Short condition: RSI overbought + sufficient margin"""
        if len(self.vars['rsi_values']) < 1:
            return False
        
        current_rsi = self.vars['rsi_values'][-1]
        current_price = self.current_candle[4]  # Close price
        
        # Check conditions
        rsi_overbought = current_rsi > self.hp['rsi_overbought']
        no_position = self.position_type is None
        
        # Check if we have enough margin
        max_lots = self.calculate_max_lots(current_price)
        has_margin = max_lots >= 1
        
        return (rsi_overbought and no_position and has_margin)
    
    def should_cancel_entry(self) -> bool:
        """Cancel entry if conditions change rapidly"""
        return False
    
    def should_exit_position(self) -> bool:
        """Exit position when RSI returns to neutral (50)"""
        if self.position_type is None or len(self.vars['rsi_values']) < 1:
            return False
        
        current_rsi = self.vars['rsi_values'][-1]
        
        if self.position_type == 'long':
            return current_rsi > self.hp['rsi_neutral']
        elif self.position_type == 'short':
            return current_rsi < self.hp['rsi_neutral']
        
        return False
    
    def before(self):
        """Calculate indicators before strategy execution"""
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
                if len(self.vars['rsi_values']) > 5:
                    self.vars['rsi_values'].pop(0)
        
        if len(closes) >= self.hp['sma_period']:
            sma_values = sma(np.array(closes), self.hp['sma_period'])
            if not np.isnan(sma_values[-1]):
                self.vars['sma_values'].append(sma_values[-1])
                if len(self.vars['sma_values']) > 3:
                    self.vars['sma_values'].pop(0)
    
    def after(self):
        """Manage positions after strategy execution"""
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
    
    def go_long(self, quantity: float = None, price: float = None) -> None:
        """Override to implement futures lot sizing"""
        if price is None:
            price = self.current_candle[4]
        
        # Calculate lots to trade
        max_lots = self.calculate_max_lots(price)
        lots_to_trade = min(max_lots, 1)  # Trade 1 lot at a time for conservative approach
        
        if lots_to_trade < 1:
            return  # Not enough margin
        
        # Calculate actual quantity (lots * lot_size)
        actual_quantity = lots_to_trade * self.hp['lot_size']
        
        # Calculate required margin
        margin_used = self.calculate_margin_required(price, lots_to_trade)
        
        # Call parent method with proper quantity
        super().go_long(actual_quantity, price)
        
        # Update margin tracking
        self.vars['used_margin'] = margin_used
        self.vars['lots_traded'] = lots_to_trade
        
        # Adjust current capital to reflect margin usage (not full contract value)
        # This simulates leveraged trading
        self.current_capital -= margin_used
        
        print(f"Long: {lots_to_trade} lot(s) ({actual_quantity} shares) at ₹{price:.2f}, Margin used: ₹{margin_used:,.2f}")
    
    def go_short(self, quantity: float = None, price: float = None) -> None:
        """Override to implement futures lot sizing"""
        if price is None:
            price = self.current_candle[4]
        
        # Calculate lots to trade
        max_lots = self.calculate_max_lots(price)
        lots_to_trade = min(max_lots, 1)  # Trade 1 lot at a time for conservative approach
        
        if lots_to_trade < 1:
            return  # Not enough margin
        
        # Calculate actual quantity (lots * lot_size)
        actual_quantity = lots_to_trade * self.hp['lot_size']
        
        # Calculate required margin
        margin_used = self.calculate_margin_required(price, lots_to_trade)
        
        # Call parent method with proper quantity
        super().go_short(actual_quantity, price)
        
        # Update margin tracking
        self.vars['used_margin'] = margin_used
        self.vars['lots_traded'] = lots_to_trade
        
        # Adjust current capital to reflect margin usage (not full contract value)
        self.current_capital -= margin_used
        
        print(f"Short: {lots_to_trade} lot(s) ({actual_quantity} shares) at ₹{price:.2f}, Margin used: ₹{margin_used:,.2f}")
    
    def liquidate(self, price: float = None) -> None:
        """Override to properly handle margin release and P&L calculation"""
        if self.position_type is None:
            return
            
        if price is None:
            price = self.current_candle[4]  # Close price
        
        # Calculate P&L (this is the actual profit/loss, not margin)
        if self.position_type == 'long':
            pnl = (price - self.entry_price) * self.position_size
        else:
            pnl = (self.entry_price - price) * self.position_size
            
        # Release margin back to available capital
        self.current_capital += self.vars['used_margin']
        
        # Add P&L to capital
        self.pnl += pnl
        self.current_capital += pnl
        
        # Log the exit with lot information
        print(f"Position closed: {self.vars['lots_traded']} lot(s) at ₹{price:.2f}, "
              f"P&L: ₹{pnl:,.2f}, Margin released: ₹{self.vars['used_margin']:,.2f}")
        
        # Add to trades history
        self.trades.append({
            'type': self.position_type,
            'entry_price': self.entry_price,
            'exit_price': price,
            'quantity': self.position_size,
            'lots': self.vars['lots_traded'],
            'pnl': pnl,
            'margin_used': self.vars['used_margin'],
            'entry_time': self.current_candle[0] - 60000,  # Approximate entry time
            'exit_time': self.current_candle[0]
        })
        
        # Reset position and margin tracking
        self.position_type = None
        self.position_size = 0
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.vars['used_margin'] = 0
        self.vars['lots_traded'] = 0