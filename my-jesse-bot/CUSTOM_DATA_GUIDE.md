# Custom Data Integration - Usage Guide

## ✅ Implementation Complete

Your Jesse Bot now has full custom data support! The "Custom" exchange should now appear in both import and backtesting dropdowns.

## ⚠️ Issue Fixed

**Error**: `InvalidConfig: Value for exchange type in your config file in not valid. Supported values are "spot" and "futures". Your value is "custom"`

**Solution**: Changed the Custom exchange type from "custom" to "spot" in the configuration. The Custom exchange now works as a spot exchange for backtesting purposes.

## 🔧 What Was Added:

1. **Custom Data Driver** - Reads CSV/JSON files from `custom_data/` directory
2. **Exchange Integration** - "Custom" added to the exchange drivers list
3. **Backtesting Support** - "Custom" added to backtesting exchanges list
4. **API Endpoints** - Custom data upload/management endpoints
5. **Sample Data** - Ready-to-use example files

## 📋 How to Use:

### Step 1: Prepare Your Data
Place your data files in the `custom_data/` directory with this format:
- **Filename**: `SYMBOL.csv` or `SYMBOL.json` (e.g., `BTC-USDT.csv`, `ETH-USDT.json`)
- **Columns**: `timestamp,open,high,low,close,volume`
- **Timestamp**: Unix timestamp in milliseconds or ISO date string

### Step 2: Import Custom Data
1. Open Jesse GUI at `http://localhost:9001`
2. Go to **Import Candles** section
3. Select **"Custom"** from the exchange dropdown
4. Choose your symbol (e.g., "BTC-USDT", "CUSTOM-USDT")
5. Set start date and click **Import**

### Step 3: Backtest with Custom Data
1. Go to **Backtest** section
2. Select **"Custom"** from the exchange dropdown
3. Choose your imported symbol
4. Configure your strategy and run backtest

## 📁 Sample Files Available:

- `custom_data/BTC-USDT.csv` - Basic sample with 10 candles
- `custom_data/CUSTOM-USDT.csv` - Extended sample with 30 candles
- `custom_data/README.md` - Detailed format instructions

## 🔧 Technical Details:

**Files Modified:**
- `/jesse-env/lib/python3.13/site-packages/jesse/modes/import_candles_mode/drivers/__init__.py`
- `/jesse-env/lib/python3.13/site-packages/jesse/info.py`
- `/jesse-env/lib/python3.13/site-packages/jesse/__init__.py`
- `/jesse-env/lib/python3.13/site-packages/jesse/controllers/custom_data_controller.py`

**Custom Driver Location:**
- `/jesse-env/lib/python3.13/site-packages/jesse/modes/import_candles_mode/drivers/Custom/CustomDataImport.py`

## 🚀 Getting Started:

1. **Verify Setup**: Check that "Custom" appears in the exchange dropdown in the GUI
2. **Test Import**: Try importing the sample `CUSTOM-USDT` data
3. **Run Backtest**: Create a simple backtest using the custom data
4. **Add Your Data**: Replace sample files with your own trading data

## 💡 Tips:

- Jesse service must be restarted after adding new data files
- Data should be sorted by timestamp (oldest first)  
- Missing data points will be automatically filled
- All price values should be numeric (float/decimal)
- Timestamps can be in seconds (will be auto-converted to milliseconds)

## 🎉 Success!

Your Jesse Bot now supports custom data import and backtesting! The "Custom" exchange should be visible in all relevant dropdowns in the GUI.