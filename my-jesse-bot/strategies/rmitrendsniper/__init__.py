from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils

class rmitrendsniper(Strategy):
    # Strategy state variables  
    positive_momentum = False
    negative_momentum = False
    prev_positive = False
    prev_negative = False
    
    # Pullback entry states
    waiting_long_pullback = False
    waiting_short_pullback = False
    
    @property
    def rmi(self):
        """Combined RSI and MFI indicator (RMI)"""
        rsi = ta.rsi(self.candles, 14)
        mfi = ta.mfi(self.candles, 14) 
        return (rsi + mfi) / 2
    
    @property
    def prev_rmi(self):
        """Previous RMI value"""
        if len(self.candles) < 2:
            return 50
        rsi = ta.rsi(self.candles[:-1], 14)
        mfi = ta.mfi(self.candles[:-1], 14)
        return (rsi + mfi) / 2
    
    @property
    def ema5_rising(self):
        """Check if EMA5 is rising"""
        ema5 = ta.ema(self.candles, 5, sequential=True)
        if len(ema5) < 2:
            return False
        return ema5[-1] > ema5[-2]
    
    @property
    def ema5_falling(self):
        """Check if EMA5 is falling"""  
        ema5 = ta.ema(self.candles, 5, sequential=True)
        if len(ema5) < 2:
            return False
        return ema5[-1] < ema5[-2]
    
    @property
    def range_weighted_ma(self):
        """Range-weighted moving average"""
        period = 20
        if len(self.candles) < period:
            return self.price
            
        recent_candles = self.candles[-period:]
        ranges = [candle[3] - candle[4] for candle in recent_candles]  # high - low
        closes = [candle[2] for candle in recent_candles]  # close
        
        total_range = sum(ranges)
        if total_range == 0:
            return self.price
            
        weighted_sum = sum(closes[i] * ranges[i] / total_range for i in range(len(ranges)))
        total_weight = sum(ranges[i] / total_range for i in range(len(ranges)))
        
        return weighted_sum / total_weight if total_weight > 0 else self.price
    
    @property
    def dynamic_band(self):
        """Dynamic band calculation"""
        atr = ta.atr(self.candles, 30)
        return min(atr * 0.3, self.price * 0.003) / 2 * 8
    
    @property
    def upper_band(self):
        """Upper channel band"""
        return self.range_weighted_ma + self.dynamic_band
    
    @property
    def lower_band(self):
        """Lower channel band"""
        return self.range_weighted_ma - self.dynamic_band
    
    @property
    def cmo(self):
        """Chande Momentum Oscillator for debugging"""
        return ta.cmo(self.candles, 14)
    
    @property
    def minute_candles(self):
        """Get 1-minute candles for pullback detection"""
        return self.get_candles(self.exchange, self.symbol, '1m')
    
    @property
    def minute_price(self):
        """Current price from 1-minute timeframe"""
        if len(self.minute_candles) > 0:
            return self.minute_candles[-1][2]  # close price
        return self.price
    
    def check_pullback_entry(self):
        """Check if price touches bands on 1-minute timeframe for entry"""
        if self.waiting_long_pullback:
            # For long: wait for price to touch lower band
            if self.minute_price <= self.lower_band:
                return 'long'
        
        if self.waiting_short_pullback:
            # For short: wait for price to touch upper band  
            if self.minute_price >= self.upper_band:
                return 'short'
                
        return None
    
    def before(self):
        """Update momentum states"""
        # Store previous states
        self.prev_positive = self.positive_momentum
        self.prev_negative = self.negative_momentum
        
        # Positive momentum: RMI crosses above 66 with rising EMA5 and CMO > 40
        if (self.prev_rmi < 66 and self.rmi > 66 and 
            self.rmi > 30 and self.ema5_rising and self.cmo > 40):
            self.positive_momentum = True
            self.negative_momentum = False
            # Start waiting for pullback instead of immediate entry
            if not self.prev_positive:
                self.waiting_long_pullback = True
                self.waiting_short_pullback = False
        
        # Negative momentum: RMI below 30 with falling EMA5 and CMO < -40
        elif self.rmi < 30 and self.ema5_falling and self.cmo < -40:
            self.positive_momentum = False  
            self.negative_momentum = True
            # Start waiting for pullback instead of immediate entry
            if not self.prev_negative:
                self.waiting_short_pullback = True
                self.waiting_long_pullback = False
    
    def should_long(self) -> bool:
        # Enter long when waiting for pullback and price touches lower band
        pullback_entry = self.check_pullback_entry()
        return pullback_entry == 'long'
    
    def should_short(self) -> bool:
        # Enter short when waiting for pullback and price touches upper band
        pullback_entry = self.check_pullback_entry()
        return pullback_entry == 'short'
    
    def go_long(self):
        entry = self.price
        stop = entry - ta.atr(self.candles) * 2
        qty = utils.risk_to_qty(self.available_margin, 2, entry, stop, fee_rate=self.fee_rate)
        self.buy = qty, entry
        # Reset pullback state after entry
        self.waiting_long_pullback = False
    
    def go_short(self):
        entry = self.price
        stop = entry + ta.atr(self.candles) * 2  
        qty = utils.risk_to_qty(self.available_margin, 2, entry, stop, fee_rate=self.fee_rate)
        self.sell = qty, entry
        # Reset pullback state after entry
        self.waiting_short_pullback = False
    
    def on_open_position(self, order):
        if self.is_long:
            self.stop_loss = self.position.qty, self.price - ta.atr(self.candles) * 2
        elif self.is_short:
            self.stop_loss = self.position.qty, self.price + ta.atr(self.candles) * 2
    
    def update_position(self):
        # Exit on momentum reversal
        if self.is_long and self.negative_momentum and not self.prev_negative:
            self.liquidate()
        elif self.is_short and self.positive_momentum and not self.prev_positive:
            self.liquidate()
        
        # Reset pullback states if momentum changes while waiting
        if not self.positive_momentum:
            self.waiting_long_pullback = False
        if not self.negative_momentum:
            self.waiting_short_pullback = False
        
        # Dynamic trailing stop using range-weighted MA and bands
        if self.is_long:
            trail_stop = self.range_weighted_ma - self.dynamic_band
            self.stop_loss = self.position.qty, max(self.average_stop_loss, trail_stop)
        elif self.is_short:
            trail_stop = self.range_weighted_ma + self.dynamic_band
            self.stop_loss = self.position.qty, min(self.average_stop_loss, trail_stop)
    
    def should_cancel_entry(self) -> bool:
        return True
    
    def after(self):
        """Add main indicators to the chart for debugging"""
        # Main chart indicators
        self.add_line_to_candle_chart('RWMA', self.range_weighted_ma, '#00bcd4' if self.positive_momentum else '#ff5252')
        self.add_line_to_candle_chart('EMA5', ta.ema(self.candles, 5), '#ffa726')
        
        # Dynamic bands around RWMA
        self.add_line_to_candle_chart('Upper Band', self.upper_band, '#00bcd4' if self.positive_momentum else '#ff5252')
        self.add_line_to_candle_chart('Lower Band', self.lower_band, '#00bcd4' if self.positive_momentum else '#ff5252')
        
        # RMI oscillator in separate chart
        self.add_extra_line_chart('RMI', 'RMI', self.rmi, '#9c27b0')
        
        # RMI threshold levels
        self.add_horizontal_line_to_extra_chart('RMI', 'Overbought', 66, '#f44336')
        self.add_horizontal_line_to_extra_chart('RMI', 'Oversold', 30, '#4caf50')
        self.add_horizontal_line_to_extra_chart('RMI', 'Midline', 50, '#757575')
        
        # Chande Momentum Oscillator for debugging
        self.add_extra_line_chart('CMO', 'CMO', self.cmo, '#e91e63')
        self.add_horizontal_line_to_extra_chart('CMO', 'CMO +40', 40, '#f44336')
        self.add_horizontal_line_to_extra_chart('CMO', 'CMO -40', -40, '#4caf50')
        self.add_horizontal_line_to_extra_chart('CMO', 'CMO Zero', 0, '#757575')
        
        # Momentum signals in separate chart
        momentum_value = 80 if self.positive_momentum else 20 if self.negative_momentum else 50
        self.add_extra_line_chart('Momentum', 'State', momentum_value, '#ff9800')
        
        # Pullback waiting states
        pullback_value = 80 if self.waiting_long_pullback else 20 if self.waiting_short_pullback else 50
        self.add_extra_line_chart('Pullback', 'Waiting', pullback_value, '#795548')

    def watch_list(self):
        return [
            ('RMI', round(self.rmi, 2)),
            ('CMO', round(self.cmo, 2)),
            ('Positive Momentum', self.positive_momentum),
            ('Negative Momentum', self.negative_momentum), 
            ('Waiting Long Pullback', self.waiting_long_pullback),
            ('Waiting Short Pullback', self.waiting_short_pullback),
            ('RWMA', round(self.range_weighted_ma, 2)),
            ('Upper Band', round(self.upper_band, 2)),
            ('Lower Band', round(self.lower_band, 2)),
            ('1m Price', round(self.minute_price, 2))
        ]