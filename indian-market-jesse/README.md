# Indian Market Trading System

A comprehensive trading framework for Indian stock markets based on Jesse concepts. This framework allows for backtesting and strategy development specifically optimized for Indian markets, with full support for **Futures, Options, Equity MTF, and regular Equity trading**.

## 🚀 Features

- **🎯 Futures Trading**: Proper lot sizing, margin calculations for NIFTY, BANKNIFTY, FINNIFTY
- **📈 Leverage Support**: Margin Trading Facility (MTF) for equity with up to 4x leverage
- **⏰ Market Hours**: Designed for Indian trading hours (9:15-15:30 weekdays)
- **📊 Advanced Strategies**: Mean reversion, moving averages with risk management
- **💰 Realistic P&L**: Includes transaction costs, proper margin calculations
- **🔧 Configurable Instruments**: Easy setup for any futures/options contract
- **📈 Performance Metrics**: Comprehensive backtesting with detailed trade analysis

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🎯 Quick Start - Futures Trading

### 1. List Available Instruments
```bash
python -m indian_market_jesse instruments
```

Output:
```
Available Instruments:
--------------------------------------------------
Symbol       Type     Lot Size Margin   Leverage
--------------------------------------------------
NIFTY        futures  75       11.0%    9.0x    
BANKNIFTY    futures  25       12.0%    8.3x    
FINNIFTY     futures  50       12.0%    8.3x    
EQUITY_MTF   equity   1        25.0%    4.0x    
EQUITY       equity   1        100.0%   1.0x    
--------------------------------------------------
```

### 2. Run NIFTY Futures Strategy

```bash
# NIFTY Futures with ₹5 lakh capital
python -m indian_market_jesse backtest \
  --strategy futures_mean_reversion \
  --instrument NIFTY \
  --timeframe 15m \
  --start-date "2024-01-01" \
  --finish-date "2024-12-31" \
  --capital 500000 \
  --data-file data/NIFTY50_minute_data.csv \
  --save-results
```

### 3. Run BANKNIFTY Futures Strategy

```bash
# BANKNIFTY Futures (smaller lot size = 25)
python -m indian_market_jesse backtest \
  --strategy futures_mean_reversion \
  --instrument BANKNIFTY \
  --timeframe 15m \
  --capital 300000 \
  --data-file data/BANKNIFTY_data.csv
```

## 📊 Supported Instruments & Capital Requirements

| Instrument | Type | Lot Size | Margin | Min Capital* | Contract Value** |
|------------|------|----------|--------|--------------|------------------|
| **NIFTY** | Futures | 75 | 11% | ₹2.5L | ₹17.6L |
| **BANKNIFTY** | Futures | 25 | 12% | ₹2L | ₹15L |
| **FINNIFTY** | Futures | 50 | 12% | ₹1.5L | ₹10L |
| **Equity MTF** | Equity | 1 | 25% | ₹10K | Variable |
| **Regular Equity** | Equity | 1 | 100% | ₹5K | Variable |

*Recommended minimum capital for comfortable trading  
**Approximate values as of 2024

## 🛠️ Data Format

Place your CSV data files in the `data` directory with these columns:

```csv
date,open,high,low,close,volume
2024-01-01 09:15:00,21727.75,21737.35,21701.8,21712.0,0
2024-01-01 09:16:00,21711.5,21720.0,21695.35,21695.65,0
```

## 📈 Available Strategies

### List All Strategies
```bash
python -m indian_market_jesse strategies
```

### 1. **Universal Futures Strategy** (Recommended)
- **Strategy**: `futures_mean_reversion`
- **Works with**: Any futures instrument (NIFTY, BANKNIFTY, FINNIFTY)
- **Features**: Auto lot sizing, proper margin calculations, transaction costs
- **Parameters**: Configurable RSI levels, risk management

```bash
python -m indian_market_jesse backtest \
  --strategy futures_mean_reversion \
  --instrument NIFTY \
  --timeframe 15m \
  --capital 500000
```

### 2. **NIFTY-Specific Strategy** 
- **Strategy**: `nifty_futures_mean_reversion`
- **Fixed for**: NIFTY only (75 lot size, 11% margin)

### 3. **Aggressive Mean Reversion**
- **Strategy**: `aggressive_mean_reversion`
- **Best for**: 15-minute timeframe, more frequent trades

### 4. **Moving Average Crossover**
- **Strategy**: `ma_crossover`
- **Type**: Trend following strategy

## 💡 Creating Custom Instruments

Add your own futures/options contracts:

```python
from indian_market_jesse.models.instrument import Instrument, InstrumentType, InstrumentRegistry

# Add custom futures contract
custom_futures = Instrument(
    symbol="CUSTOM_FUT",
    instrument_type=InstrumentType.FUTURES,
    lot_size=100,           # Your lot size
    margin_rate=0.15,       # 15% margin
    tick_size=0.05,
    max_leverage=6.7,       # ~1/0.15
    transaction_cost=0.0003
)

InstrumentRegistry.register(custom_futures)
```

## 📋 Strategy Development

### Creating a New Strategy

```bash
python -m indian_market_jesse create-strategy --name my_custom_strategy
```

### Example Custom Strategy

```python
from indian_market_jesse.strategies.strategy import Strategy
from indian_market_jesse.models.instrument import InstrumentRegistry

class MyStrategy(Strategy):
    def __init__(self, symbol="NIFTY"):
        super().__init__()
        self.instrument = InstrumentRegistry.get(symbol)
        
        self.hp = {
            'rsi_period': 14,
            'risk_percent': 0.5  # Use 50% capital for margin
        }
    
    def should_long(self) -> bool:
        # Your long logic here
        return False
    
    def should_short(self) -> bool:
        # Your short logic here  
        return False
```

## 🎯 Real Trading Examples

### Conservative NIFTY Trading (₹5L Capital)
```bash
# 1 lot NIFTY, conservative risk
python -m indian_market_jesse backtest \
  --strategy futures_mean_reversion \
  --instrument NIFTY \
  --capital 500000 \
  --timeframe 15m
```

### Aggressive BANKNIFTY Trading (₹3L Capital)
```bash
# Multiple BANKNIFTY lots, higher frequency
python -m indian_market_jesse backtest \
  --strategy futures_mean_reversion \
  --instrument BANKNIFTY \
  --capital 300000 \
  --timeframe 5m
```

### Equity MTF Trading (₹50K Capital)
```bash
# 4x leverage equity trading
python -m indian_market_jesse backtest \
  --strategy futures_mean_reversion \
  --instrument EQUITY_MTF \
  --capital 50000 \
  --timeframe 1h
```

## ⚠️ Risk Management Features

1. **Automatic Position Sizing**: Based on available margin
2. **Stop Loss/Take Profit**: Configurable percentage-based exits  
3. **Maximum Lots Per Trade**: Prevents over-leveraging
4. **Transaction Costs**: Realistic cost calculations
5. **Margin Tracking**: Proper leverage monitoring

## 🔧 Configuration

All instrument configurations are in `indian_market_jesse/models/instrument.py`. You can modify:
- Lot sizes
- Margin requirements  
- Transaction costs
- Leverage limits

## 📊 Performance Analysis

After running a backtest, you get:
- **Total Return %**: Overall performance
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss
- **Individual Trades**: Detailed trade-by-trade analysis
- **Margin Usage**: Capital efficiency metrics

## 🚨 Important Notes

1. **Capital Requirements**: Ensure sufficient capital for futures trading (₹2-5L minimum)
2. **Lot Sizes**: All quantities are automatically rounded to valid lot sizes
3. **Margin Calls**: System prevents over-leveraging beyond available capital
4. **Market Hours**: Backtests respect Indian market timings
5. **Transaction Costs**: Real-world costs are included in P&L

## 📞 Support

For issues or questions:
- Create an issue in this repository
- Check the `DOCUMENTATION.md` for detailed technical information

---

**⚡ Ready to trade NIFTY futures with proper risk management!**
