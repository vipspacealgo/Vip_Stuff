from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils

class niftaw(Strategy):
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
    def cmo(self):
        return ta.cmo(self.candles, 14)
    
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
        # Debug logging every 100 candles
        if self.index % 100 == 0:
            self.log(f'CMO: {self.cmo:.2f}, Trend: {self.current_trend}, Price: {self.price:.2f}')
        
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
        # Enter long when trend changes from bearish to bullish AND momentum is positive
        return (self.current_trend == 1 and 
                self.prev_trend == -1 and 
                self.cmo > -20)  # CMO filter to avoid weak momentum
    
    def should_short(self) -> bool:
        # Enter short when trend changes from bullish to bearish AND momentum is negative
        return (self.current_trend == -1 and 
                self.prev_trend == 1 and 
                self.cmo < 20)  # CMO filter to avoid weak momentum
    
    def go_long(self):
        entry = self.price
        stop = entry - ta.atr(self.candles) * 2
        qty = 1
        self.buy = qty*2, entry
        self.log(f'Going LONG - CMO: {self.cmo:.2f}, Entry: {entry:.2f}')
    
    def go_short(self):
        entry = self.price
        stop = entry + ta.atr(self.candles) * 2
        qty = 1
        self.sell = qty*2, entry
        self.log(f'Going SHORT - CMO: {self.cmo:.2f}, Entry: {entry:.2f}')
    
    def should_cancel_entry(self) -> bool:
        return True
    
    def on_open_position(self, order):
        if self.is_long:
            self.stop_loss = self.position.qty, self.price - ta.atr(self.candles) * 2
            self.log(f'Position opened LONG - CMO: {self.cmo:.2f}')
        elif self.is_short:
            self.stop_loss = self.position.qty, self.price + ta.atr(self.candles) * 2
            self.log(f'Position opened SHORT - CMO: {self.cmo:.2f}')
    
    def update_position(self):
        # Exit when trend reverses OR momentum becomes too weak
        if self.is_long:
            if self.current_trend == -1 or self.cmo < -50:
                self.log(f'Closing LONG - Trend: {self.current_trend}, CMO: {self.cmo:.2f}')
                self.liquidate()
        elif self.is_short:
            if self.current_trend == 1 or self.cmo > 50:
                self.log(f'Closing SHORT - Trend: {self.current_trend}, CMO: {self.cmo:.2f}')
                self.liquidate()
    
    def watch_list(self):
        return [
            ('CMO', self.cmo),
            ('Current Trend', self.current_trend if self.current_trend else 0),
            ('Basis', self.trend_levels[0]),
            ('Position PNL%', self.position.pnl_percentage if self.is_open else 0)
        ]
    
    def after(self):
        # Add CMO to extra chart for visualization
        self.add_extra_line_chart('CMO', 'CMO14', self.cmo)
        self.add_horizontal_line_to_extra_chart('CMO', 'Overbought', 50, 'red')
        self.add_horizontal_line_to_extra_chart('CMO', 'Oversold', -50, 'green')
        self.add_horizontal_line_to_extra_chart('CMO', 'Zero Line', 0, 'gray')
        
        # Add trend levels to main chart
        basis, upper, lower = self.trend_levels
        self.add_line_to_candle_chart('Basis', basis, 'blue')
        self.add_line_to_candle_chart('Upper', upper, 'red')
        self.add_line_to_candle_chart('Lower', lower, 'green')