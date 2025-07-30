# Indian Market Trading System Documentation

## Overview

This is a comprehensive trading framework designed specifically for Indian stock markets, inspired by the Jesse crypto trading framework. It handles the unique characteristics of Indian markets including:

- **Market Hours**: 9:15 AM to 3:30 PM on weekdays
- **Market Gaps**: Proper handling of overnight gaps, weekends, and holidays
- **Data Import**: Manual CSV data import for backtesting
- **Risk Management**: Built-in position sizing and risk controls
- **Multiple Timeframes**: Support for 1m, 5m, 15m, 1h, 1D, and more

## Architecture

```
indian-market-jesse/
├── indian_market_jesse/          # Main package
│   ├── config.py                 # Configuration and market hours
│   ├── helpers.py                # Utility functions
│   ├── indicators/               # Technical indicators
│   │   └── __init__.py          # SMA, EMA, RSI, Bollinger Bands, etc.
│   ├── strategies/               # Trading strategies
│   │   ├── strategy.py          # Base strategy class
│   │   ├── ma_crossover.py      # Moving average crossover
│   │   └── rsi_mean_reversion.py # RSI mean reversion
│   ├── services/                 # Core services
│   │   ├── data_importer.py     # CSV data import
│   │   └── backtest_engine.py   # Backtesting engine
│   └── cli.py                   # Command line interface
├── data/                        # Data directory
│   └── NIFTY50_minute_data.csv # Sample NIFTY 50 data
├── demo.py                      # Demonstration script
└── requirements.txt             # Dependencies
```

## Key Features

### 1. Market Hours Handling

The system automatically filters data to include only Indian market hours:

```python
def is_market_open(timestamp: int) -> bool:
    """Check if market is open at given timestamp"""
    dt = timestamp_to_datetime(timestamp)
    weekday = dt.weekday()
    
    # Check if it's a weekend
    if weekday not in [0, 1, 2, 3, 4]:  # Monday to Friday
        return False
    
    # Check trading hours (9:15 - 15:30)
    return time(9, 15) <= dt.time() <= time(15, 30)
```

### 2. Data Import System

Supports CSV files with the following format:
```csv
date,open,high,low,close,volume
2015-01-09 09:15:00,8285.45,8295.9,8285.45,8292.1,0
```

Usage:
```python
from indian_market_jesse.services.data_importer import DataImporter

candles = DataImporter.import_candles_from_csv(
    'data/NIFTY50_minute_data.csv',
    'NIFTY50',
    'NSE',
    '5m'
)
```

### 3. Strategy Development

Create strategies by inheriting from the base `Strategy` class:

```python
from indian_market_jesse.strategies.strategy import Strategy

class MyStrategy(Strategy):
    def should_long(self) -> bool:
        # Define long entry conditions
        return False
    
    def should_short(self) -> bool:
        # Define short entry conditions
        return False
    
    def before(self):
        # Calculate indicators before each candle
        pass
    
    def after(self):
        # Manage positions after each candle
        self.update_position()
```

### 4. Technical Indicators

Available indicators:
- **SMA** (Simple Moving Average)
- **EMA** (Exponential Moving Average)
- **RSI** (Relative Strength Index)
- **Bollinger Bands**
- **MACD**
- **Stochastic Oscillator**
- **ATR** (Average True Range)
- **ADX** (Average Directional Index)

Example usage:
```python
from indian_market_jesse.indicators import sma, rsi, bollinger_bands

# Calculate indicators
ma_20 = sma(prices, 20)
rsi_14 = rsi(prices, 14)
bb_upper, bb_middle, bb_lower = bollinger_bands(prices, 20, 2)
```

### 5. Risk Management

Built-in risk management features:
- Position sizing based on risk percentage
- Stop loss and take profit levels
- Maximum position size limits
- Capital preservation rules

```python
def calculate_position_size(self) -> float:
    risk_amount = self.current_capital * self.hp['risk_percent']
    price_diff = self.entry_price * self.hp['stop_loss_percent']
    return risk_amount / price_diff
```

## Usage Examples

### Command Line Interface

1. **List available strategies**:
```bash
python -m indian_market_jesse strategies
```

2. **Run a backtest**:
```bash
python -m indian_market_jesse backtest \
    --strategy ma_crossover \
    --timeframe 5m \
    --start-date 2021-01-01 \
    --finish-date 2021-12-31 \
    --capital 500000 \
    --save-results
```

3. **Create a new strategy**:
```bash
python -m indian_market_jesse create-strategy my_new_strategy
```

4. **Import data**:
```bash
python -m indian_market_jesse import-data \
    --input-file data/raw_data.csv \
    --output-file data/processed_data.csv \
    --symbol NIFTY50 \
    --timeframe 5m
```

### Programmatic Usage

```python
from indian_market_jesse.services.backtest_engine import BacktestEngine
from indian_market_jesse.strategies.ma_crossover import MovingAverageCrossover

# Initialize backtest
engine = BacktestEngine(
    strategy_class=MovingAverageCrossover,
    symbol='NIFTY50',
    timeframe='5m',
    start_date='2021-01-01',
    finish_date='2021-12-31',
    initial_capital=500000
)

# Load data and run backtest
engine.load_data('data/NIFTY50_minute_data.csv')
results = engine.run()

# Display results
engine.print_results()
```

## Sample Strategies

### 1. Moving Average Crossover

A simple trend-following strategy:
- **Long**: Fast MA crosses above Slow MA + RSI < 70
- **Short**: Fast MA crosses below Slow MA + RSI > 30
- **Exit**: Stop loss at 2% or take profit at 3%

### 2. RSI Mean Reversion

A contrarian strategy:
- **Long**: RSI < 30 + Price above 20-day SMA
- **Short**: RSI > 70 + Price below 20-day SMA
- **Exit**: RSI returns to neutral zone (45-55)

## Configuration

Market configuration in `config.py`:

```python
config = {
    'env': {
        'exchanges': {
            'NSE': {
                'fee': 0.0003,  # 0.03% fee
                'type': 'spot',
                'balance': 100000,
                'market_hours': {
                    'open': '09:15',
                    'close': '15:30',
                    'timezone': 'Asia/Kolkata',
                    'trading_days': [0, 1, 2, 3, 4]  # Mon-Fri
                }
            }
        }
    }
}
```

## Performance Metrics

The system calculates comprehensive performance metrics:

- **Total Return**: Absolute and percentage returns
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profits to gross losses
- **Total Trades**: Number of completed trades
- **Average Win/Loss**: Average profit per winning/losing trade

## Demo Results

Sample backtest results on NIFTY 50 data:

```
Strategy: Moving Average Crossover
Period: 2021-01-01 to 2021-03-31
Initial Capital: ₹200,000.00
Final Capital: ₹215,907.49
Total Return: 7.95%
Total Trades: 8
Win Rate: 62.50%
```

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Place your data files in the `data/` directory
4. Run the demo: `python demo.py`

## Data Requirements

Your CSV data should have the following columns:
- `date`: DateTime in YYYY-MM-DD HH:MM:SS format
- `open`: Opening price
- `high`: High price
- `low`: Low price
- `close`: Closing price
- `volume`: Volume (optional, will default to 0)

## Future Enhancements

Potential improvements:
1. **Live Trading**: Integration with broker APIs
2. **More Indicators**: Additional technical indicators
3. **Portfolio Management**: Multi-symbol strategies
4. **Options Trading**: Support for derivatives
5. **Holiday Calendar**: Indian market holiday integration
6. **Advanced Backtesting**: Walk-forward analysis, Monte Carlo simulations
7. **Web Interface**: GUI for strategy development and backtesting

## Contributing

To add a new strategy:
1. Create a new file in `strategies/`
2. Inherit from the `Strategy` base class
3. Implement the required methods
4. Add to the CLI strategy mapping
5. Test with backtesting

## License

This project is for educational and research purposes. Always test strategies thoroughly before using with real money.

---

**Happy Trading! 📈🇮🇳**
