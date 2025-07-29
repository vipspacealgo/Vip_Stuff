from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils
import numpy as np

class chandelierexit(Strategy):
    def __init__(self):
        super().__init__()
        self.direction = 1  
        self.prev_direction = 1
        self.long_stop_prev = 0
        self.short_stop_prev = 0
    
    def before(self):
        if len(self.candles) < 20:
            return
            
        # Store previous direction before updating
        self.prev_direction = self.direction
            
        # Calculate Chandelier Exit levels
        atr_val = ta.atr(self.candles, 20) * 3.0
        
        # Get highest and lowest close over last 20 periods
        period = 20
        closes = self.candles[-period:, 2]  
        highest_close = np.max(closes)
        lowest_close = np.min(closes)
        
        # Calculate stops
        long_stop = highest_close - atr_val
        short_stop = lowest_close + atr_val
        
        # Chandelier Exit logic: stops can only move in favorable direction
        if len(self.candles) > 20:
            prev_close = self.candles[-2, 2]  
            
            if prev_close > self.long_stop_prev:
                long_stop = max(long_stop, self.long_stop_prev)
                
            if prev_close < self.short_stop_prev:
                short_stop = min(short_stop, self.short_stop_prev)
        
        self.long_stop_prev = long_stop
        self.short_stop_prev = short_stop
        
        # Update direction - only changes on stop breaks
        if self.close > self.short_stop_prev:
            self.direction = 1
        elif self.close < self.long_stop_prev:
            self.direction = -1
        # Otherwise direction stays the same

    @property
    def long_stop(self):
        return self.long_stop_prev
    
    @property  
    def short_stop(self):
        return self.short_stop_prev

    def should_long(self):
        # Only enter long when direction changes from -1 to 1
        return (len(self.candles) >= 20 and 
                self.direction == 1 and 
                self.prev_direction == -1)

    def should_short(self):
        # Only enter short when direction changes from 1 to -1  
        return (len(self.candles) >= 20 and 
                self.direction == -1 and 
                self.prev_direction == 1)
        
    def go_long(self):
        entry = self.price
        stop = self.long_stop
        qty = utils.risk_to_qty(self.available_margin, 2, entry, stop, fee_rate=self.fee_rate)
        self.buy = qty, entry
    
    def go_short(self):
        entry = self.price  
        stop = self.short_stop
        qty = utils.risk_to_qty(self.available_margin, 2, entry, stop, fee_rate=self.fee_rate)
        self.sell = qty, entry
    
    def on_open_position(self, order):
        if self.is_long:
            self.stop_loss = self.position.qty, self.long_stop
        elif self.is_short:
            self.stop_loss = self.position.qty, self.short_stop
    
    def update_position(self):
        # Exit when direction changes against position
        if self.is_long and self.direction == -1:
            self.liquidate()
        elif self.is_short and self.direction == 1:
            self.liquidate()
    
    def should_cancel_entry(self):
        return True
        
    def watch_list(self):
        return [
            ('Direction', self.direction),
            ('Prev Direction', self.prev_direction),
            ('Long Stop', self.long_stop),
            ('Short Stop', self.short_stop)
        ]