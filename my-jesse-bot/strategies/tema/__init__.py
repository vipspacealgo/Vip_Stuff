from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils

class tema(Strategy):

    def __init__(self):
        super().__init__()
        # Initialize internal state variable for tracking initial stop loss
        self.entry_stop_loss = 0

    @property
    def bb(self):
        # Bollinger Bands with default period (20) and 2 standard deviations
        # Using 'close' price as source
        return ta.bollinger_bands(self.candles)

    @property
    def rsi(self):
        # RSI with default period (14)
        return ta.rsi(self.candles)

    @property
    def atr(self):
        # Average True Range for dynamic stop loss calculation
        return ta.atr(self.candles)

    def should_long(self) -> bool:
        # Check if no position is open
        # Price closes below the lower Bollinger Band
        # RSI is oversold (e.g., below 30)
        return self.is_close and self.close < self.bb.lowerband and self.rsi < 30

    def should_short(self) -> bool:
        # Check if no position is open
        # Price closes above the upper Bollinger Band
        # RSI is overbought (e.g., above 70)
        return self.is_close and self.close > self.bb.upperband and self.rsi > 70

    def go_long(self):
        entry_price = self.price
        # Set initial stop loss 1.5 ATR below entry
        # Store this value to use for position sizing
        self.entry_stop_loss = entry_price - (self.atr * 1.5)
        
        # Calculate quantity risking 1% of available capital
        qty = utils.risk_to_qty(
            capital=self.available_margin,
            risk_per_capital=1, # Risk 1% of available margin
            entry_price=entry_price,
            stop_loss_price=self.entry_stop_loss,
            fee_rate=self.fee_rate
        )
        
        # Place a market buy order
        self.buy = qty, entry_price

    def go_short(self):
        entry_price = self.price
        # Set initial stop loss 1.5 ATR above entry
        # Store this value to use for position sizing
        self.entry_stop_loss = entry_price + (self.atr * 1.5)

        # Calculate quantity risking 1% of available capital
        qty = utils.risk_to_qty(
            capital=self.available_margin,
            risk_per_capital=1, # Risk 1% of available margin
            entry_price=entry_price,
            stop_loss_price=self.entry_stop_loss,
            fee_rate=self.fee_rate
        )

        # Place a market sell order
        self.sell = qty, entry_price

    def on_open_position(self, order):
        # Set the actual stop loss and take profit after the position is opened
        if self.is_long:
            self.stop_loss = self.position.qty, self.entry_stop_loss
            # Target is the middle band (2 standard deviations profit)
            self.take_profit = self.position.qty, self.bb.middleband
        elif self.is_short:
            self.stop_loss = self.position.qty, self.entry_stop_loss
            # Target is the middle band (2 standard deviations profit)
            self.take_profit = self.position.qty, self.bb.middleband

    def update_position(self):
        # Manual exit when price closes at or beyond the middle band
        if self.is_long and self.close >= self.bb.middleband:
            self.liquidate()
        elif self.is_short and self.close <= self.bb.middleband:
            self.liquidate()

        # You can add a trailing stop here if desired, but for mean reversion,
        # often the target (middle band) is enough.
        # Example:
        # if self.is_long and self.close > self.position.entry_price + (self.atr * 0.5): # if in slight profit
        #     self.stop_loss = self.position.qty, max(self.average_stop_loss, self.position.entry_price)
        # elif self.is_short and self.close < self.position.entry_price - (self.atr * 0.5):
        #     self.stop_loss = self.position.qty, min(self.average_stop_loss, self.position.entry_price)

    def should_cancel_entry(self) -> bool:
        # Cancel pending entry orders if conditions reverse
        # For a market order entry, this is less critical as `go_long`/`go_short` are called exactly once.
        # But good practice for limit order entries.
        return True

    def terminate(self):
        # Add indicators to the chart for visualization during backtesting
        self.add_line_to_candle_chart('BB Upper', self.bb.upperband)
        self.add_line_to_candle_chart('BB Middle', self.bb.middleband)
        self.add_line_to_candle_chart('BB Lower', self.bb.lowerband)
        self.add_extra_line_chart('RSI', 'RSI', self.rsi)
        self.add_horizontal_line_to_extra_chart('RSI', 'RSI 70', 70, 'red')
        self.add_horizontal_line_to_extra_chart('RSI', 'RSI 30', 30, 'green')