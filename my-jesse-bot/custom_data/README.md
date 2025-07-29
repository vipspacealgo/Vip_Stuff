# Custom Data Import

This directory is for custom trading data files that can be imported into Jesse Bot.

## File Format

Your custom data files should be in CSV or JSON format with the following columns:

### Required Columns:
- `timestamp`: Unix timestamp in milliseconds (or ISO date string)
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price  
- `close`: Closing price
- `volume`: Trading volume

### CSV Example (BTC-USDT.csv):
```csv
timestamp,open,high,low,close,volume
1640995200000,46500.00,47200.00,46300.00,46800.00,125.45
1640995260000,46800.00,46900.00,46650.00,46700.00,98.32
1640995320000,46700.00,46850.00,46600.00,46750.00,76.89
```

### JSON Example (BTC-USDT.json):
```json
[
  {
    "timestamp": 1640995200000,
    "open": 46500.00,
    "high": 47200.00,
    "low": 46300.00,
    "close": 46800.00,
    "volume": 125.45
  },
  {
    "timestamp": 1640995260000,
    "open": 46800.00,
    "high": 46900.00,
    "low": 46650.00,
    "close": 46700.00,
    "volume": 98.32
  }
]
```

## How to Use:

1. **File Naming**: Name your files with the symbol you want to use (e.g., `BTC-USDT.csv`, `ETH-USDT.json`)

2. **Upload via GUI**: Use the web interface to upload files through the custom data section

3. **Import Data**: In the import candles section, select "Custom" as the exchange and your symbol

4. **Backtesting**: When creating a backtest, "Custom" will appear in the exchange dropdown along with your symbols

## Notes:

- Timestamps can be in milliseconds (Unix timestamp) or ISO date strings
- If timestamps are in seconds, they will be automatically converted to milliseconds
- Data should be sorted by timestamp (oldest first)
- Missing data points will be filled automatically
- All price values should be numeric (float/decimal)