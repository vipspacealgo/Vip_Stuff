"""
Generic Futures Mean Reversion Strategy

This strategy automatically adapts to any futures instrument using the
Instrument Registry. Users just specify the symbol and the strategy
automatically uses correct lot sizes, margins, etc.

Supports: NIFTY, BANKNIFTY, FINNIFTY and any custom futures instrument
"""

import numpy as np
from indian_market_jesse.strategies.strategy import Strategy
from indian_market_jesse.indicators import sma, ema, rsi
from indian_market_jesse.models.instrument import InstrumentRegistry, Instrument, InstrumentType

class FuturesMeanReversion(Strategy):
    """
    Universal Futures Mean Reversion Strategy
    
    Features:
    - Auto-detects instrument specifications (lot size, margin, etc.)
    - Works with NIFTY, BANKNIFTY, FINNIFTY out of the box
    - Users can add custom instruments easily
    - Proper leverage and risk management
    
    Strategy Logic:
    - Long when RSI < oversold level
    - Short when RSI > overbought level  
    - Exit when RSI crosses back to neutral
    - Uses proper futures position sizing
    """
    
    def __init__(self, symbol: str = "NIFTY"):
        super().__init__()
        
        # Get instrument configuration
        self.instrument = InstrumentRegistry.get(symbol.upper())
        if self.instrument is None:
            # Create default futures instrument if not found
            print(f"Warning: Instrument {symbol} not found. Using default futures config.")
            self.instrument = Instrument(
                symbol=symbol.upper(),
                instrument_type=InstrumentType.FUTURES,
                lot_size=50,  # Default lot size
                margin_rate=0.15,  # 15% default margin
                tick_size=0.05
            )
        
        print(f"Using instrument: {self.instrument}")
        
        # Strategy hyperparameters
        self.hp = {
            'rsi_period': 14,
            'rsi_oversold': 40,
            'rsi_overbought': 60,
            'rsi_neutral': 50,
            'sma_period': 20,
            'stop_loss_percent': 0.015,     # 1.5%
            'take_profit_percent': 0.025,   # 2.5%
            'risk_percent': 0.8,            # Use 80% of capital for margin
            'max_lots_per_trade': 3         # Maximum lots per trade
        }
        
        # Strategy variables
        self.vars = {
            'rsi_values': [],
            'sma_values': [],
            'current_lots': 0,
            'margin_used': 0
        }
    
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
        max_lots = self.instrument.calculate_max_lots(
            self.current_capital, 
            current_price, 
            self.hp['risk_percent']
        )
        max_lots = min(max_lots, self.hp['max_lots_per_trade'])
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
        max_lots = self.instrument.calculate_max_lots(
            self.current_capital, 
            current_price, 
            self.hp['risk_percent']
        )
        max_lots = min(max_lots, self.hp['max_lots_per_trade'])
        has_margin = max_lots >= 1
        
        return (rsi_overbought and no_position and has_margin)
    
    def should_cancel_entry(self) -> bool:
        """Cancel entry if conditions change rapidly"""
        return False
    
    def should_exit_position(self) -> bool:
        """Exit position when RSI returns to neutral"""
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
        max_lots = self.instrument.calculate_max_lots(
            self.current_capital, 
            price, 
            self.hp['risk_percent']
        )
        lots_to_trade = min(max_lots, self.hp['max_lots_per_trade'], 1)  # Conservative: 1 lot
        
        if lots_to_trade < 1:
            return  # Not enough margin
        
        # Calculate actual quantity using instrument lot size
        actual_quantity = self.instrument.calculate_quantity(lots_to_trade)
        
        # Calculate required margin
        margin_used = self.instrument.calculate_margin_required(price, lots_to_trade)
        
        # Call parent method with proper quantity
        super().go_long(actual_quantity, price)
        
        # Update tracking variables
        self.vars['current_lots'] = lots_to_trade
        self.vars['margin_used'] = margin_used
        
        # Adjust current capital to reflect margin usage (leveraged trading)
        self.current_capital -= margin_used
        
        print(f"LONG: {lots_to_trade} lot(s) ({actual_quantity} shares) of {self.instrument.symbol} "
              f"at ₹{price:.2f}, Margin used: ₹{margin_used:,.2f}")
    
    def go_short(self, quantity: float = None, price: float = None) -> None:
        """Override to implement futures lot sizing"""
        if price is None:
            price = self.current_candle[4]
        
        # Calculate lots to trade
        max_lots = self.instrument.calculate_max_lots(
            self.current_capital, 
            price, 
            self.hp['risk_percent']
        )
        lots_to_trade = min(max_lots, self.hp['max_lots_per_trade'], 1)  # Conservative: 1 lot
        
        if lots_to_trade < 1:
            return  # Not enough margin
        
        # Calculate actual quantity using instrument lot size
        actual_quantity = self.instrument.calculate_quantity(lots_to_trade)
        
        # Calculate required margin
        margin_used = self.instrument.calculate_margin_required(price, lots_to_trade)
        
        # Call parent method with proper quantity
        super().go_short(actual_quantity, price)
        
        # Update tracking variables
        self.vars['current_lots'] = lots_to_trade
        self.vars['margin_used'] = margin_used
        
        # Adjust current capital to reflect margin usage (leveraged trading)
        self.current_capital -= margin_used
        
        print(f"SHORT: {lots_to_trade} lot(s) ({actual_quantity} shares) of {self.instrument.symbol} "
              f"at ₹{price:.2f}, Margin used: ₹{margin_used:,.2f}")
    
    def liquidate(self, price: float = None) -> None:
        """Override to properly handle margin release"""
        if self.position_type is None:
            return
            
        if price is None:
            price = self.current_candle[4]  # Close price
        
        # Calculate P&L
        if self.position_type == 'long':
            pnl = (price - self.entry_price) * self.position_size
        else:
            pnl = (self.entry_price - price) * self.position_size
        
        # Calculate transaction costs
        contract_value = self.instrument.calculate_contract_value(price, self.vars['current_lots'])
        transaction_cost = self.instrument.calculate_transaction_cost(contract_value)
        pnl -= transaction_cost  # Deduct transaction costs
        
        # Release margin back to available capital
        self.current_capital += self.vars['margin_used']
        
        # Add P&L to capital
        self.pnl += pnl
        self.current_capital += pnl
        
        # Log the exit with lot information
        print(f"Position closed: {self.vars['current_lots']} lot(s) of {self.instrument.symbol} "
              f"at ₹{price:.2f}, P&L: ₹{pnl:,.2f} (after costs: ₹{transaction_cost:.2f}), "
              f"Margin released: ₹{self.vars['margin_used']:,.2f}")
        
        # Add to trades history
        self.trades.append({
            'type': self.position_type,
            'entry_price': self.entry_price,
            'exit_price': price,
            'quantity': self.position_size,
            'lots': self.vars['current_lots'],
            'pnl': pnl,
            'margin_used': self.vars['margin_used'],
            'transaction_cost': transaction_cost,
            'instrument': self.instrument.symbol,
            'entry_time': self.current_candle[0] - 60000,
            'exit_time': self.current_candle[0]
        })
        
        # Reset position and tracking
        self.position_type = None
        self.position_size = 0
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.vars['current_lots'] = 0
        self.vars['margin_used'] = 0