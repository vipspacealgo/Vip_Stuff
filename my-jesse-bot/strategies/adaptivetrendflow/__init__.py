from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils

class adaptivetrendflow(Strategy):
    def __init__(self):
        super().__init__()
        self.current_trend = None
        self.prev_trend = None
        self.prev_level = None
        
    @property
    def length(self):
        return 10
        
    @property
    def sensitivity(self):
        return 2.0
    
    @property
    def trend_levels(self):
        # Calculate basis using dual EMAs
        fast_ema = ta.ema(self.candles, self.length, source_type='hlc3')
        slow_ema = ta.ema(self.candles, self.length * 2, source_type='hlc3')
        basis = (fast_ema + slow_ema) / 2
        
        # Use ATR for volatility (already smoothed)
        volatility = ta.atr(self.candles, self.length)
        
        upper = basis + (volatility * self.sensitivity)
        lower = basis - (volatility * self.sensitivity)
        
        return basis, upper, lower
    
    def before(self):
        # Update trend state once per candle
        basis, upper, lower = self.trend_levels
        
        # Store previous trend
        self.prev_trend = self.current_trend
        
        # Initialize trend on first run
        if self.current_trend is None:
            if self.close > basis:
                self.current_trend = 1
                self.prev_level = lower
            else:
                self.current_trend = -1
                self.prev_level = upper
            return
        
        # Update trend based on crossovers
        if self.current_trend == 1:  # Currently bullish
            if self.close < lower:
                self.current_trend = -1
                self.prev_level = upper
            else:
                self.prev_level = lower
        else:  # Currently bearish
            if self.close > upper:
                self.current_trend = 1
                self.prev_level = lower
            else:
                self.prev_level = upper
    
    def should_long(self) -> bool:
        # Enter long when trend changes from bearish to bullish
        return self.current_trend == 1 and self.prev_trend == -1
    
    def should_short(self) -> bool:
        # Enter short when trend changes from bullish to bearish  
        return self.current_trend == -1 and self.prev_trend == 1
    
    def go_long(self):
        entry = self.price
        stop = entry - ta.atr(self.candles) * 2
        qty = 1
        self.buy = qty*2, entry
    
    def go_short(self):
        entry = self.price
        stop = entry + ta.atr(self.candles) * 2
        qty = 1
        self.sell = qty*2, entry
    
    def should_cancel_entry(self) -> bool:
        return True
    
    def on_open_position(self, order):
        if self.is_long:
            self.stop_loss = self.position.qty, self.price - ta.atr(self.candles) * 2
        elif self.is_short:
            self.stop_loss = self.position.qty, self.price + ta.atr(self.candles) * 2
    
    def update_position(self):
        # Exit when trend reverses
        if self.is_long and self.current_trend == -1:
            self.liquidate()
        elif self.is_short and self.current_trend == 1:
            self.liquidate()