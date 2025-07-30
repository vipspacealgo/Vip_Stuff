"""
Backtest Engine for Indian Market Trading System
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Type
from tqdm import tqdm

import indian_market_jesse.helpers as jh
from indian_market_jesse.config import config
from indian_market_jesse.strategies.strategy import Strategy
from indian_market_jesse.services.data_importer import DataImporter

class BacktestEngine:
    """
    Main backtest engine that runs strategies against historical data
    """
    
    def __init__(self, 
                 strategy_class: Type[Strategy],
                 symbol: str,
                 exchange: str = 'NSE',
                 timeframe: str = '1m',
                 start_date: str = None,
                 finish_date: str = None,
                 initial_capital: float = 100000):
        """
        Initialize the backtest engine
        
        Args:
            strategy_class: The strategy class to test
            symbol: Symbol to trade
            exchange: Exchange name (default: NSE)
            timeframe: Timeframe for trading
            start_date: Start date for backtest (YYYY-MM-DD)
            finish_date: Finish date for backtest (YYYY-MM-DD)
            initial_capital: Initial capital in INR
        """
        self.strategy_class = strategy_class
        self.symbol = symbol
        self.exchange = exchange
        self.timeframe = timeframe
        self.start_date = start_date
        self.finish_date = finish_date
        self.initial_capital = initial_capital
        
        # Initialize strategy instance
        self.strategy = strategy_class()
        self.strategy.symbol = symbol
        self.strategy.exchange = exchange
        self.strategy.timeframe = timeframe
        self.strategy.initial_capital = initial_capital
        self.strategy.current_capital = initial_capital
        
        # Data storage
        self.candles = None
        self.results = {}
        
    def load_data(self, data_file: str = None) -> None:
        """
        Load historical data for backtesting
        
        Args:
            data_file: Path to CSV data file (if None, will look in data directory)
        """
        if data_file is None:
            # Look for data file in data directory
            data_dir = config['env']['data']['data_path']
            data_file = f"{data_dir}/{self.symbol}_minute_data.csv"
        
        print(f"Loading data from: {data_file}")
        
        # Import and process data
        self.candles = DataImporter.import_candles_from_csv(
            data_file, 
            self.symbol, 
            self.exchange, 
            self.timeframe
        )
        
        # Filter by date range if specified
        if self.start_date or self.finish_date:
            self.candles = self._filter_by_date_range(self.candles)
        
        print(f"Loaded {len(self.candles)} candles for backtesting")
        
        # Store candles in strategy
        self.strategy.candles = self.candles
    
    def _filter_by_date_range(self, candles: np.ndarray) -> np.ndarray:
        """
        Filter candles by date range
        """
        filtered_candles = []
        
        start_timestamp = jh.date_to_timestamp(self.start_date) if self.start_date else 0
        finish_timestamp = jh.date_to_timestamp(self.finish_date) if self.finish_date else float('inf')
        
        for candle in candles:
            if start_timestamp <= candle[0] <= finish_timestamp:
                filtered_candles.append(candle)
        
        return np.array(filtered_candles)
    
    def run(self) -> Dict:
        """
        Run the backtest
        
        Returns:
            Dictionary containing backtest results
        """
        if self.candles is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        print(f"Running backtest for {self.strategy.__class__.__name__}")
        print(f"Symbol: {self.symbol}")
        print(f"Timeframe: {self.timeframe}")
        print(f"Period: {self.start_date} to {self.finish_date}")
        print(f"Initial Capital: ₹{self.initial_capital:,.2f}")
        print("-" * 50)
        
        # Initialize progress bar
        progress_bar = tqdm(total=len(self.candles), desc="Backtesting")
        
        # Run strategy on each candle
        for i, candle in enumerate(self.candles):
            self.strategy.index = i
            self.strategy.current_candle = candle
            
            # Execute strategy logic
            self.strategy.before()
            
            # Check for entry signals
            if self.strategy.should_long():
                self.strategy.go_long()
            elif self.strategy.should_short():
                self.strategy.go_short()
            
            # Update position management
            self.strategy.after()
            
            # Update progress
            progress_bar.update(1)
        
        progress_bar.close()
        
        # Close any remaining position
        if self.strategy.position_type is not None:
            self.strategy.liquidate()
        
        # Calculate final metrics
        metrics = self.strategy.calculate_metrics()
        
        # Compile results
        self.results = {
            'strategy': self.strategy.__class__.__name__,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'start_date': self.start_date,
            'finish_date': self.finish_date,
            'initial_capital': self.initial_capital,
            'final_capital': self.strategy.current_capital,
            'total_return': self.strategy.current_capital - self.initial_capital,
            'total_return_percentage': ((self.strategy.current_capital - self.initial_capital) / self.initial_capital) * 100,
            'trades': self.strategy.trades,
            'metrics': metrics
        }
        
        return self.results
    
    def print_results(self) -> None:
        """
        Print backtest results in a formatted way
        """
        if not self.results:
            print("No results to display. Run backtest first.")
            return
        
        print("\n" + "=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        print(f"Strategy: {self.results['strategy']}")
        print(f"Symbol: {self.results['symbol']}")
        print(f"Timeframe: {self.results['timeframe']}")
        print(f"Period: {self.results['start_date']} to {self.results['finish_date']}")
        print("-" * 60)
        print(f"Initial Capital: ₹{self.results['initial_capital']:,.2f}")
        print(f"Final Capital: ₹{self.results['final_capital']:,.2f}")
        print(f"Total Return: ₹{self.results['total_return']:,.2f}")
        print(f"Total Return %: {self.results['total_return_percentage']:.2f}%")
        print("-" * 60)
        print("TRADE STATISTICS:")
        print(f"Total Trades: {self.results['metrics']['total_trades']}")
        print(f"Win Rate: {self.results['metrics']['win_rate']:.2%}")
        print(f"Profit Factor: {self.results['metrics']['profit_factor']:.2f}")
        print("=" * 60)
        
        # Print individual trades if there are any
        if len(self.results['trades']) > 0:
            print("\nTRADE DETAILS:")
            print("-" * 60)
            for i, trade in enumerate(self.results['trades'][:10]):  # Show first 10 trades
                entry_time = jh.timestamp_to_datetime(trade['entry_time'])
                exit_time = jh.timestamp_to_datetime(trade['exit_time'])
                print(f"Trade {i+1}: {trade['type'].upper()} | "
                      f"Entry: ₹{trade['entry_price']:.2f} ({entry_time.strftime('%Y-%m-%d %H:%M')}) | "
                      f"Exit: ₹{trade['exit_price']:.2f} ({exit_time.strftime('%Y-%m-%d %H:%M')}) | "
                      f"P&L: ₹{trade['pnl']:.2f}")
            
            if len(self.results['trades']) > 10:
                print(f"... and {len(self.results['trades']) - 10} more trades")
    
    def save_results(self, filename: str = None) -> None:
        """
        Save backtest results to a CSV file
        """
        if not self.results:
            print("No results to save. Run backtest first.")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_results_{self.symbol}_{timestamp}.csv"
        
        # Convert trades to DataFrame
        if len(self.results['trades']) > 0:
            trades_df = pd.DataFrame(self.results['trades'])
            
            # Add datetime columns
            trades_df['entry_datetime'] = trades_df['entry_time'].apply(
                lambda x: jh.timestamp_to_datetime(x)
            )
            trades_df['exit_datetime'] = trades_df['exit_time'].apply(
                lambda x: jh.timestamp_to_datetime(x)
            )
            
            # Save to CSV
            trades_df.to_csv(filename, index=False)
            print(f"Results saved to: {filename}")
        else:
            print("No trades to save.")
