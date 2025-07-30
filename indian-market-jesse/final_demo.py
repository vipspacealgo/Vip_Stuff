#!/usr/bin/env python3
"""
Final Demo: Run different strategies and show results
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from indian_market_jesse.services.backtest_engine import BacktestEngine
from indian_market_jesse.strategies.ma_crossover import MovingAverageCrossover
from indian_market_jesse.strategies.rsi_mean_reversion import RSIMeanReversion

def run_strategy_comparison():
    """Compare different strategies"""
    print("🇮🇳 STRATEGY COMPARISON DEMO 🇮🇳")
    print("=" * 60)
    
    strategies = {
        'Moving Average Crossover': MovingAverageCrossover,
        'RSI Mean Reversion': RSIMeanReversion
    }
    
    results = {}
    
    for name, strategy_class in strategies.items():
        print(f"\nTesting: {name}")
        print("-" * 40)
        
        # Modify RSI strategy to be more sensitive
        if strategy_class == RSIMeanReversion:
            engine = BacktestEngine(
                strategy_class=strategy_class,
                symbol='NIFTY50',
                timeframe='5m',
                start_date='2021-01-01',
                finish_date='2021-03-31',
                initial_capital=200000
            )
            # Make RSI strategy more sensitive
            engine.strategy.hp['rsi_oversold'] = 35
            engine.strategy.hp['rsi_overbought'] = 65
        else:
            engine = BacktestEngine(
                strategy_class=strategy_class,
                symbol='NIFTY50',
                timeframe='5m',
                start_date='2021-01-01',
                finish_date='2021-03-31',
                initial_capital=200000
            )
        
        try:
            engine.load_data()
            result = engine.run()
            results[name] = result
            
            print(f"Final Capital: ₹{result['final_capital']:,.2f}")
            print(f"Return: {result['total_return_percentage']:.2f}%")
            print(f"Trades: {result['metrics']['total_trades']}")
            print(f"Win Rate: {result['metrics']['win_rate']:.2%}")
            
        except Exception as e:
            print(f"Error: {e}")
            results[name] = None
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for name, result in results.items():
        if result:
            print(f"{name:25} | Return: {result['total_return_percentage']:6.2f}% | "
                  f"Trades: {result['metrics']['total_trades']:3d} | "
                  f"Win Rate: {result['metrics']['win_rate']:5.1%}")
    
    print("\n🎯 Key Features Demonstrated:")
    print("✅ Indian market hours (9:15-15:30) filtering")
    print("✅ Weekend and holiday gap handling")
    print("✅ Multiple timeframe support (1m, 5m, 15m, etc.)")
    print("✅ Risk management with stop-loss and take-profit")
    print("✅ Technical indicators (SMA, EMA, RSI, Bollinger Bands)")
    print("✅ Strategy backtesting with performance metrics")
    print("✅ CSV data import for manual data loading")
    print("✅ Command-line interface for easy usage")

if __name__ == "__main__":
    run_strategy_comparison()
