# Indian Market Trading System

A trading framework for Indian stock markets based on Jesse concepts. This framework allows for backtesting and strategy development specifically optimized for Indian markets.

## Features

- Designed specifically for Indian stock market trading hours (9:15-15:30 weekdays)
- Handles market gaps (overnight, weekends, and holidays)
- Import data from CSV files
- Comprehensive indicator library
- Strategy backtesting
- Performance metrics

## Getting Started

### Installation

```bash
pip install -r requirements.txt
```

### Importing Data

Place your CSV data files in the `data` directory. The system accepts CSV files with the following columns:
- date: in YYYY-MM-DD HH:MM:SS format
- open: open price
- high: high price
- low: low price
- close: close price
- volume: volume

### Running a Backtest

```bash
python -m indian_market_jesse backtest --start-date "2023-01-01" --finish-date "2023-02-01"
```

### Creating a Strategy

Create your strategy in the `strategies` directory. See the example strategy for reference.
