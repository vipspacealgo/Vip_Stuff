from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils
import numpy as np

class adaptivetrend(Strategy):
    
    @property
    def adaptive_period(self):
        """Find the period with strongest trend correlation"""
        periods = [20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200]
        best_period = 50
        best_correlation = 0
        
        for period in periods:
            if len(self.candles) < period + 5:
                continue
            
            # Calculate correlation between price and time for trend strength
            closes = self.candles[-period:, 2]  # Close prices
            x_values = np.arange(len(closes))
            
            if len(closes) > 10:
                # Calculate Pearson correlation coefficient
                correlation_matrix = np.corrcoef(x_values, closes)
                correlation = abs(correlation_matrix[0, 1])
                
                if not np.isnan(correlation) and correlation > best_correlation:
                    best_correlation = correlation
                    best_period = period
        
        return best_period

    @property
    def trend_data(self):
        """Calculate adaptive trend channel data"""
        period = self.adaptive_period
        
        # Linear regression trend line
        trend_line = ta.linearreg(self.candles, period)
        trend_slope = ta.linearreg_slope(self.candles, period)
        
        # Channel bounds using standard deviation
        std_dev = ta.stddev(self.candles, period)
        multiplier = 2.0  # Similar to Pine Script's deviation multiplier
        
        upper_bound = trend_line + (std_dev * multiplier)
        lower_bound = trend_line - (std_dev * multiplier)
        channel_width = upper_bound - lower_bound
        
        return {
            'period': period,
            'trend_line': trend_line,
            'slope': trend_slope,
            'upper_bound': upper_bound,
            'lower_bound': lower_bound,
            'channel_width': channel_width,
            'std_dev': std_dev
        }

    @property
    def trend_direction(self):
        """Determine trend direction"""
        data = self.trend_data
        if data['slope'] > 0.001:
            return 1  # Uptrend
        elif data['slope'] < -0.001:
            return -1  # Downtrend
        else:
            return 0  # Sideways

    @property
    def entry_zone_width(self):
        """Configurable entry zone width (5-10% of channel)"""
        return 0.08  # 8% of channel width

    def should_long(self) -> bool:
        """Enter long near bottom of trend channel in uptrend"""
        data = self.trend_data
        
        # Only trade longs in uptrends or sideways markets
        if self.trend_direction == -1:
            return False
        
        # Calculate entry zone near lower bound
        entry_threshold = data['lower_bound'] + (data['channel_width'] * self.entry_zone_width)
        
        # Enter when price is in the lower entry zone
        return self.price <= entry_threshold

    def should_short(self) -> bool:
        """Enter short near top of trend channel in downtrend"""
        data = self.trend_data
        
        # Only trade shorts in downtrends or sideways markets  
        if self.trend_direction == 1:
            return False
        
        # Calculate entry zone near upper bound
        entry_threshold = data['upper_bound'] - (data['channel_width'] * self.entry_zone_width)
        
        # Enter when price is in the upper entry zone
        return self.price >= entry_threshold

    def go_long(self):
        entry = self.price
        # Use ATR-based stop loss for better risk management
        atr_stop = entry - ta.atr(self.candles) * 2
        qty = utils.risk_to_qty(self.available_margin, 2, entry, atr_stop, fee_rate=self.fee_rate)
        self.buy = qty, entry

    def go_short(self):
        entry = self.price
        # Use ATR-based stop loss for better risk management  
        atr_stop = entry + ta.atr(self.candles) * 2
        qty = utils.risk_to_qty(self.available_margin, 2, entry, atr_stop, fee_rate=self.fee_rate)
        self.sell = qty, entry

    def update_position(self):
        """Exit near opposite channel bound with trailing stop protection"""
        data = self.trend_data
        
        if self.is_long:
            # Primary exit: when price reaches near upper bound (95% of way to upper bound)
            exit_threshold = data['upper_bound'] - (data['channel_width'] * 0.05)
            if self.price >= exit_threshold:
                self.liquidate()
            
            # Trailing stop to protect profits
            trailing_stop = self.price - ta.atr(self.candles) * 2
            if trailing_stop > self.average_stop_loss:
                self.stop_loss = self.position.qty, trailing_stop
        
        elif self.is_short:
            # Primary exit: when price reaches near lower bound (95% of way to lower bound)
            exit_threshold = data['lower_bound'] + (data['channel_width'] * 0.05)
            if self.price <= exit_threshold:
                self.liquidate()
            
            # Trailing stop to protect profits
            trailing_stop = self.price + ta.atr(self.candles) * 2
            if trailing_stop < self.average_stop_loss:
                self.stop_loss = self.position.qty, trailing_stop

    def on_open_position(self, order):
        # Use ATR-based stops for better risk management
        if self.is_long:
            self.stop_loss = self.position.qty, self.price - ta.atr(self.candles) * 2
        elif self.is_short:
            self.stop_loss = self.position.qty, self.price + ta.atr(self.candles) * 2

    def should_cancel_entry(self) -> bool:
        return True

    def watch_list(self):
        data = self.trend_data
        trend_names = {1: 'UPTREND', -1: 'DOWNTREND', 0: 'SIDEWAYS'}
        
        # Calculate exit thresholds for monitoring
        long_exit = data['upper_bound'] - (data['channel_width'] * 0.05)
        short_exit = data['lower_bound'] + (data['channel_width'] * 0.05)
        
        return [
            ('Adaptive Period', data['period']),
            ('Trend', trend_names[self.trend_direction]),
            ('Upper Bound', round(data['upper_bound'], 2)),
            ('Long Exit Target', round(long_exit, 2)),
            ('Current Price', round(self.price, 2)),
            ('Short Exit Target', round(short_exit, 2)),
            ('Lower Bound', round(data['lower_bound'], 2)),
            ('Channel Width', round(data['channel_width'], 2))
        ]

    def after(self):
        """Add trend lines to chart for visualization"""
        data = self.trend_data
        self.add_line_to_candle_chart('Trend Line', data['trend_line'])
        self.add_line_to_candle_chart('Upper Bound', data['upper_bound'])
        self.add_line_to_candle_chart('Lower Bound', data['lower_bound'])