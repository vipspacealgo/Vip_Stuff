from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils

class tema(Strategy):
    @property
    def ema_fast(self):
        return ta.ema(self.candles, 12)
    
    @property
    def ema_slow(self):
        return ta.ema(self.candles, 26)
    
    @property
    def regression_angle(self):
        # Linear regression angle to determine trend bias
        return ta.linearreg_angle(self.candles, 20)
    
    @property
    def trend_bias(self):
        # Positive angle = long bias, negative/zero = short bias
        return 1 if self.regression_angle > 0 else -1
    
    @property
    def atr(self):
        return ta.atr(self.candles)
    
    def should_long(self) -> bool:
        # EMA crossover + positive regression angle for long bias
        return (self.ema_fast > self.ema_slow and 
                self.trend_bias == 1)
    
    def should_short(self) -> bool:
        # EMA crossover + negative regression angle for short bias
        return (self.ema_fast < self.ema_slow and 
                self.trend_bias == -1)
    
    def go_long(self):
        entry = self.price
        stop = entry - self.atr * 2
        qty = utils.risk_to_qty(self.available_margin, 2, entry, stop, fee_rate=self.fee_rate)
        self.buy = qty, entry
    
    def go_short(self):
        entry = self.price
        stop = entry + self.atr * 2
        qty = utils.risk_to_qty(self.available_margin, 2, entry, stop, fee_rate=self.fee_rate)
        self.sell = qty, entry
    
    def on_open_position(self, order):
        if self.is_long:
            self.stop_loss = self.position.qty, self.price - self.atr * 2
        elif self.is_short:
            self.stop_loss = self.position.qty, self.price + self.atr * 2
    
    def update_position(self):
        # Exit when EMA crossover reverses or trend bias changes
        if self.is_long and (self.ema_fast < self.ema_slow or self.trend_bias == -1):
            self.liquidate()
        elif self.is_short and (self.ema_fast > self.ema_slow or self.trend_bias == 1):
            self.liquidate()
    
    def should_cancel_entry(self) -> bool:
        return True