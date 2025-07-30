from abc import ABC, abstractmethod
from typing import List, Dict, Union, Optional
import numpy as np

import indian_market_jesse.helpers as jh
from indian_market_jesse.config import config

class Strategy(ABC):
    """
    Base Strategy class that all strategies must inherit from
    """
    
    def __init__(self) -> None:
        """
        Initialize the strategy
        """
        self.id = jh.generate_unique_id()
        self.name = None
        self.symbol = None
        self.exchange = None
        self.timeframe = None
        self.hp = {}  # Hyperparameters
        
        self.index = 0
        self.position = None
        self.trades = []
        self.current_candle = None
        
        # Variables for position management
        self.position_size = 0
        self.position_type = None  # 'long' or 'short'
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        
        # Performance tracking
        self.initial_capital = 0
        self.current_capital = 0
        self.pnl = 0
        self.metrics = {}
        
        # Variables to store custom values or state
        self.vars = {}
    
    @abstractmethod
    def should_long(self) -> bool:
        """
        Return True if strategy wants to go long
        """
        pass
    
    @abstractmethod
    def should_short(self) -> bool:
        """
        Return True if strategy wants to go short
        """
        pass
    
    @abstractmethod
    def should_cancel_entry(self) -> bool:
        """
        Return True if strategy wants to cancel the entry order
        """
        pass
        
    def go_long(self, quantity: float = None, price: float = None) -> None:
        """
        Open a long position
        
        Args:
            quantity: The quantity to buy
            price: The price to buy at (default is current close price)
        """
        if self.position_type == 'long':
            return
        
        if price is None:
            price = self.current_candle[4]  # Close price
            
        if quantity is None:
            # Use all available capital by default
            quantity = self.current_capital / price
            
        self.position_type = 'long'
        self.position_size = quantity
        self.entry_price = price
        
        # Log the entry
        print(f"Long position opened at {self.current_candle[0]} - Price: {price}, Quantity: {quantity}")
    
    def go_short(self, quantity: float = None, price: float = None) -> None:
        """
        Open a short position
        
        Args:
            quantity: The quantity to sell
            price: The price to sell at (default is current close price)
        """
        if self.position_type == 'short':
            return
        
        if price is None:
            price = self.current_candle[4]  # Close price
            
        if quantity is None:
            # Use all available capital by default
            quantity = self.current_capital / price
            
        self.position_type = 'short'
        self.position_size = quantity
        self.entry_price = price
        
        # Log the entry
        print(f"Short position opened at {self.current_candle[0]} - Price: {price}, Quantity: {quantity}")
    
    def liquidate(self, price: float = None) -> None:
        """
        Close the current position
        
        Args:
            price: The price to close at (default is current close price)
        """
        if self.position_type is None:
            return
            
        if price is None:
            price = self.current_candle[4]  # Close price
        
        # Calculate P&L
        if self.position_type == 'long':
            pnl = (price - self.entry_price) * self.position_size
        else:
            pnl = (self.entry_price - price) * self.position_size
            
        self.pnl += pnl
        self.current_capital += pnl
        
        # Log the exit
        print(f"Position closed at {self.current_candle[0]} - Price: {price}, PnL: {pnl}")
        
        # Add to trades history
        self.trades.append({
            'type': self.position_type,
            'entry_price': self.entry_price,
            'exit_price': price,
            'quantity': self.position_size,
            'pnl': pnl,
            'entry_time': self.current_candle[0] - 60000,  # Approximate entry time
            'exit_time': self.current_candle[0]
        })
        
        # Reset position
        self.position_type = None
        self.position_size = 0
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
    
    def set_stop_loss(self, price: float) -> None:
        """
        Set stop loss price
        """
        self.stop_loss = price
    
    def set_take_profit(self, price: float) -> None:
        """
        Set take profit price
        """
        self.take_profit = price
    
    def check_stop_loss(self) -> bool:
        """
        Check if stop loss has been triggered
        """
        if self.stop_loss is None or self.position_type is None:
            return False
            
        if self.position_type == 'long':
            # Stop loss is triggered when price is below stop loss
            return self.current_candle[3] <= self.stop_loss  # Low price
        else:
            # Stop loss is triggered when price is above stop loss
            return self.current_candle[2] >= self.stop_loss  # High price
    
    def check_take_profit(self) -> bool:
        """
        Check if take profit has been triggered
        """
        if self.take_profit is None or self.position_type is None:
            return False
            
        if self.position_type == 'long':
            # Take profit is triggered when price is above take profit
            return self.current_candle[2] >= self.take_profit  # High price
        else:
            # Take profit is triggered when price is below take profit
            return self.current_candle[3] <= self.take_profit  # Low price
            
    def before(self) -> None:
        """
        Called before strategy execution. Can be overridden by strategies.
        """
        pass
        
    def after(self) -> None:
        """
        Called after strategy execution. Can be overridden by strategies.
        """
        pass
        
    def update_position(self) -> None:
        """
        Update position based on stop loss and take profit
        """
        if self.position_type is None:
            return
            
        # Check stop loss and take profit
        if self.check_stop_loss():
            self.liquidate(self.stop_loss)
        elif self.check_take_profit():
            self.liquidate(self.take_profit)
            
    def calculate_metrics(self) -> Dict:
        """
        Calculate performance metrics after backtest
        """
        if len(self.trades) == 0:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_profit': 0,
                'total_profit_percentage': 0
            }
            
        wins = [t for t in self.trades if t['pnl'] > 0]
        losses = [t for t in self.trades if t['pnl'] <= 0]
        
        win_rate = len(wins) / len(self.trades) if len(self.trades) > 0 else 0
        
        total_profit = sum(t['pnl'] for t in self.trades)
        total_profit_percentage = (total_profit / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        
        total_wins = sum(t['pnl'] for t in wins) if len(wins) > 0 else 0
        total_losses = abs(sum(t['pnl'] for t in losses)) if len(losses) > 0 else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0 if total_wins == 0 else float('inf')
        
        metrics = {
            'total_trades': len(self.trades),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_profit': total_profit,
            'total_profit_percentage': total_profit_percentage
        }
        
        self.metrics = metrics
        return metrics
