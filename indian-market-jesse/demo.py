#!/usr/bin/env python3
"""
Demo script for Indian Market Trading System

This script demonstrates:
1. Loading Indian market data (NIFTY 50)
2. Running a moving average crossover strategy
3. Displaying results with Indian market considerations
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from indian_market_jesse.services.backtest_engine import BacktestEngine
from indian_market_jesse.strategies.ma_crossover import MovingAverageCrossover
from indian_market_jesse.services.data_importer import DataImporter
import indian_market_jesse.helpers as jh

def demo_data_import():
    """Demonstrate data import functionality"""
    print("=" * 60)
    print("DEMO: DATA IMPORT FOR INDIAN MARKETS")
    print("=" * 60)
    
    data_file = "data/NIFTY50_minute_data.csv"
    
    if not os.path.exists(data_file):
        print(f"Error: Data file {data_file} not found!")
        print("Please ensure you have the NIFTY 50 data file in the data directory.")
        return None
    
    print(f"Loading data from: {data_file}")
    
    # Load and display basic info about the data
    try:
        df = DataImporter.load_csv_as_dataframe(data_file)
        print(f"Total records in file: {len(df)}")
        print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
        
        # Show market hours filtering
        raw_candles = DataImporter.load_csv(data_file, 'NIFTY50')
        filtered_candles = DataImporter.filter_market_hours(raw_candles)
        
        print(f"Records after market hours filtering: {len(filtered_candles)}")
        print(f"Removed {len(raw_candles) - len(filtered_candles)} records outside market hours")
        
        return data_file
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def demo_strategy_backtest(data_file):
    """Demonstrate strategy backtesting"""
    print("\n" + "=" * 60)
    print("DEMO: MOVING AVERAGE CROSSOVER STRATEGY BACKTEST")
    print("=" * 60)
    
    # Initialize backtest engine
    engine = BacktestEngine(
        strategy_class=MovingAverageCrossover,
        symbol='NIFTY50',
        timeframe='5m',  # Use 5-minute timeframe for faster demo
        start_date='2022-01-01',
        finish_date='2022-03-31',  # 3 months for demo
        initial_capital=500000  # 5 lakh INR
    )
    
    try:
        # Load data
        engine.load_data(data_file)
        
        if len(engine.candles) == 0:
            print("No data available for the specified date range!")
            return
        
        # Run backtest
        results = engine.run()
        
        # Display results
        engine.print_results()
        
        # Save results
        print("\nSaving results to CSV...")
        engine.save_results("demo_backtest_results.csv")
        
        return results
        
    except Exception as e:
        print(f"Error running backtest: {e}")
        import traceback
        traceback.print_exc()
        return None

def demo_indicators():
    """Demonstrate technical indicators"""
    print("\n" + "=" * 60)
    print("DEMO: TECHNICAL INDICATORS")
    print("=" * 60)
    
    # Create sample price data
    np.random.seed(42)
    prices = 15000 + np.cumsum(np.random.randn(100) * 10)  # NIFTY-like prices
    
    from indian_market_jesse.indicators import sma, ema, rsi, bollinger_bands
    
    # Calculate indicators
    sma_10 = sma(prices, 10)
    ema_10 = ema(prices, 10)
    rsi_14 = rsi(prices, 14)
    bb_upper, bb_middle, bb_lower = bollinger_bands(prices, 20, 2)
    
    print("Sample Technical Indicators Calculation:")
    print(f"Last 5 prices: {prices[-5:]}")
    print(f"SMA(10): {sma_10[-5:]}")
    print(f"EMA(10): {ema_10[-5:]}")
    print(f"RSI(14): {rsi_14[-5:]}")
    print(f"Bollinger Upper: {bb_upper[-5:]}")
    print(f"Bollinger Lower: {bb_lower[-5:]}")

def demo_market_hours():
    """Demonstrate market hours handling"""
    print("\n" + "=" * 60)
    print("DEMO: INDIAN MARKET HOURS HANDLING")
    print("=" * 60)
    
    # Test different timestamps
    test_dates = [
        "2023-01-16 10:30:00",  # Monday during market hours
        "2023-01-16 08:00:00",  # Monday before market hours
        "2023-01-16 16:00:00",  # Monday after market hours
        "2023-01-14 11:00:00",  # Saturday
        "2023-01-15 11:00:00",  # Sunday
    ]
    
    print("Testing market hours logic:")
    for date_str in test_dates:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        timestamp = jh.datetime_to_timestamp(dt)
        is_open = jh.is_market_open(timestamp)
        day_name = dt.strftime("%A")
        
        print(f"{date_str} ({day_name}): {'OPEN' if is_open else 'CLOSED'}")

def main():
    """Main demo function"""
    print("🇮🇳 INDIAN MARKET TRADING SYSTEM DEMO 🇮🇳")
    print("A Jesse-inspired framework for Indian stock markets")
    print("Features: Market hours handling, gap management, Indian holidays")
    
    # Demo 1: Data Import
    data_file = demo_data_import()
    
    if data_file is None:
        print("\nDemo cannot continue without data file.")
        return
    
    # Demo 2: Market Hours
    demo_market_hours()
    
    # Demo 3: Indicators
    demo_indicators()
    
    # Demo 4: Strategy Backtest
    results = demo_strategy_backtest(data_file)
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETED!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Modify strategy parameters in strategies/ma_crossover.py")
    print("2. Create your own strategy using: python -m indian_market_jesse create-strategy your_strategy")
    print("3. Run backtests using: python -m indian_market_jesse backtest --help")
    print("4. Add your own data files to the data/ directory")
    print("\nHappy trading! 📈")

if __name__ == "__main__":
    main()
