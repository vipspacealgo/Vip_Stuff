from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils

class tema(Strategy):
    @property
    def short_term_trend(self):
        # Get short-term trend using TEMA crossover
        tema10 = ta.tema(self.candles, 10)
        tema80 = ta.tema(self.candles, 80)
        
        if tema10 > tema80:
            return 1  # Uptrend
        else:
            return -1  # Downtrend
    
    @property
    def long_term_trend(self):
        # Get long-term trend using TEMA crossover on 4h timeframe
        candles_4h = self.get_candles(self.exchange, self.symbol, '4h')
        tema20 = ta.tema(candles_4h, 20)
        tema70 = ta.tema(candles_4h, 70)
        
        if tema20 > tema70:
            return 1  # Uptrend
        else:
            return -1  # Downtrend
    
    @property
    def tema10(self):
        return ta.tema(self.candles, 10)
    
    @property
    def tema80(self):
        return ta.tema(self.candles, 80)
    
    @property
    def tema20_4h(self):
        candles_4h = self.get_candles(self.exchange, self.symbol, '4h')
        return ta.tema(candles_4h, 20)
    
    @property
    def tema70_4h(self):
        candles_4h = self.get_candles(self.exchange, self.symbol, '4h')
        return ta.tema(candles_4h, 70)
    
    @property
    def atr(self):
        return ta.atr(self.candles)
    
    @property
    def adx(self):
        return ta.adx(self.candles)
    
    @property
    def cmo(self):
        return ta.cmo(self.candles)
    
    def should_long(self) -> bool:
        # Check if all conditions for long trade are met
        return (
            self.short_term_trend == 1 and 
            self.long_term_trend == 1 and 
            self.adx > 40 and 
            self.cmo > 40
        )
    
    def should_short(self) -> bool:
        # Check if all conditions for short trade are met (opposite of long)
        return (
            self.short_term_trend == -1 and 
            self.long_term_trend == -1 and 
            self.adx > 40 and 
            self.cmo < -40
        )
    
    def go_long(self):
        # Calculate entry, stop and position size
        entry_price = self.price - self.atr  # Limit order 1 ATR below current price
        stop_loss_price = entry_price - (self.atr * 4)  # Stop loss 4 ATR below entry
        
        # Risk 3% of available margin
        qty = utils.risk_to_qty(self.available_margin, 3, entry_price, stop_loss_price, fee_rate=self.fee_rate)
        
        # Place the order
        self.buy = qty, entry_price
    
    def go_short(self):
        # Calculate entry, stop and position size
        entry_price = self.price + self.atr  # Limit order 1 ATR above current price
        stop_loss_price = entry_price + (self.atr * 4)  # Stop loss 4 ATR above entry
        
        # Risk 3% of available margin
        qty = utils.risk_to_qty(self.available_margin, 3, entry_price, stop_loss_price, fee_rate=self.fee_rate)
        
        # Place the order
        self.sell = qty, entry_price
    
    def should_cancel_entry(self) -> bool:
        return True
    
    def on_open_position(self, order) -> None:
        if self.is_long:
            # Set stop loss and take profit for long position
            self.stop_loss = self.position.qty, self.position.entry_price - (self.atr * 4)
            self.take_profit = self.position.qty, self.position.entry_price + (self.atr * 3)
        elif self.is_short:
            # Set stop loss and take profit for short position
            self.stop_loss = self.position.qty, self.position.entry_price + (self.atr * 4)
            self.take_profit = self.position.qty, self.position.entry_price - (self.atr * 3)
    
    def after(self) -> None:
    #     # Add main indicators to the chart for debugging
         self.add_line_to_candle_chart('TEMA10', self.tema10)
         self.add_line_to_candle_chart('TEMA80', self.tema80)
         self.add_extra_line_chart('ADX', 'ADX', self.adx)
         self.add_horizontal_line_to_extra_chart('ADX', 'ADX Threshold', 40, 'red')
         self.add_extra_line_chart('CMO', 'CMO', self.cmo)
         self.add_horizontal_line_to_extra_chart('CMO', 'CMO Upper Threshold', 40, 'green')
         self.add_horizontal_line_to_extra_chart('CMO', 'CMO Lower Threshold', -40, 'red')