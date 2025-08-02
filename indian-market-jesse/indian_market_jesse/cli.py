"""
Command Line Interface for Indian Market Trading System
"""

import click
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indian_market_jesse.services.backtest_engine import BacktestEngine
from indian_market_jesse.strategies.ma_crossover import MovingAverageCrossover
from indian_market_jesse.strategies.rsi_mean_reversion import RSIMeanReversion
from indian_market_jesse.strategies.aggressive_mean_reversion import AggressiveMeanReversion
from indian_market_jesse.strategies.nifty_futures_mean_reversion import NiftyFuturesMeanReversion
from indian_market_jesse.strategies.futures_mean_reversion import FuturesMeanReversion
from indian_market_jesse.services.data_importer import DataImporter
from indian_market_jesse.models.instrument import InstrumentRegistry

@click.group()
def cli():
    """Indian Market Trading System - A Jesse-inspired framework for Indian markets"""
    pass

@cli.command()
@click.option('--strategy', '-s', default='ma_crossover', 
              help='Strategy to run (default: ma_crossover)')
@click.option('--symbol', default='NIFTY50', 
              help='Symbol to trade (default: NIFTY50)')
@click.option('--instrument', '-i', default='NIFTY',
              help='Instrument type for futures strategy (NIFTY, BANKNIFTY, FINNIFTY)')
@click.option('--timeframe', '-t', default='1m', 
              help='Timeframe for trading (default: 1m)')
@click.option('--start-date', '-sd', 
              help='Start date for backtest (YYYY-MM-DD)')
@click.option('--finish-date', '-fd', 
              help='Finish date for backtest (YYYY-MM-DD)')
@click.option('--capital', '-c', default=100000, type=float,
              help='Initial capital in INR (default: 100000)')
@click.option('--data-file', '-df', 
              help='Path to data CSV file')
@click.option('--save-results', '-sr', is_flag=True,
              help='Save results to CSV file')
def backtest(strategy, symbol, instrument, timeframe, start_date, finish_date, capital, data_file, save_results):
    """Run a backtest with the specified parameters"""
    
    # Strategy mapping
    strategies = {
        'ma_crossover': MovingAverageCrossover,
        'rsi_mean_reversion': RSIMeanReversion,
        'aggressive_mean_reversion': AggressiveMeanReversion,
        'nifty_futures_mean_reversion': NiftyFuturesMeanReversion,
        'futures_mean_reversion': FuturesMeanReversion
    }
    
    if strategy not in strategies:
        click.echo(f"Unknown strategy: {strategy}")
        click.echo(f"Available strategies: {', '.join(strategies.keys())}")
        return
    
    try:
        # Initialize strategy with instrument if it's futures_mean_reversion
        if strategy == 'futures_mean_reversion':
            strategy_instance = strategies[strategy](instrument)
        else:
            strategy_instance = strategies[strategy]()
        
        # Initialize backtest engine
        engine = BacktestEngine(
            strategy_instance=strategy_instance,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            finish_date=finish_date,
            initial_capital=capital
        )
        
        # Load data
        engine.load_data(data_file)
        
        # Run backtest
        results = engine.run()
        
        # Print results
        engine.print_results()
        
        # Save results if requested
        if save_results:
            engine.save_results()
            
    except Exception as e:
        click.echo(f"Error running backtest: {str(e)}")
        import traceback
        traceback.print_exc()

@cli.command()
@click.option('--input-file', '-i', required=True,
              help='Path to input CSV file')
@click.option('--output-file', '-o',
              help='Path to output CSV file (optional)')
@click.option('--symbol', '-s', required=True,
              help='Symbol name')
@click.option('--timeframe', '-t', default='1m',
              help='Target timeframe (default: 1m)')
def import_data(input_file, output_file, symbol, timeframe):
    """Import and process market data from CSV"""
    
    try:
        # Load and process data
        candles = DataImporter.import_candles_from_csv(
            input_file, symbol, 'NSE', timeframe
        )
        
        click.echo(f"Successfully processed {len(candles)} candles")
        
        if output_file:
            # Save processed data
            import pandas as pd
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.to_csv(output_file, index=False)
            click.echo(f"Processed data saved to: {output_file}")
            
    except Exception as e:
        click.echo(f"Error importing data: {str(e)}")

@cli.command()
def strategies():
    """List available strategies"""
    strategies_list = [
        'ma_crossover - Moving Average Crossover Strategy',
        'rsi_mean_reversion - RSI Mean Reversion Strategy',
        'aggressive_mean_reversion - Aggressive RSI Mean Reversion Strategy (15m optimized)',
        'nifty_futures_mean_reversion - NIFTY Futures Mean Reversion (Proper lot sizing & margin)',
        'futures_mean_reversion - Universal Futures Strategy (NIFTY, BANKNIFTY, FINNIFTY)'
    ]
    
    click.echo("Available Strategies:")
    click.echo("-" * 30)
    for strategy in strategies_list:
        click.echo(f"  {strategy}")

@cli.command()
def instruments():
    """List available instrument configurations"""
    instruments = InstrumentRegistry.list_instruments()
    
    click.echo("Available Instruments:")
    click.echo("-" * 50)
    click.echo(f"{'Symbol':<12} {'Type':<8} {'Lot Size':<8} {'Margin':<8} {'Leverage':<8}")
    click.echo("-" * 50)
    
    for symbol, instrument in instruments.items():
        leverage = f"{instrument.max_leverage:.1f}x"
        margin = f"{instrument.margin_rate:.1%}"
        click.echo(f"{symbol:<12} {instrument.instrument_type.value:<8} "
                  f"{instrument.lot_size:<8} {margin:<8} {leverage:<8}")
    
    click.echo("-" * 50)
    click.echo("Usage: --instrument NIFTY (for futures_mean_reversion strategy)")

@cli.command()
@click.option('--name', '-n', required=True,
              help='Name for the new strategy')
def create_strategy(name):
    """Create a new strategy template"""
    
    strategy_template = f'''"""
{name} Strategy for Indian Markets

Created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import numpy as np
from indian_market_jesse.strategies.strategy import Strategy
from indian_market_jesse.indicators import sma, ema, rsi

class {name.replace('_', '').title()}(Strategy):
    """
    {name} strategy implementation
    """
    
    def __init__(self):
        super().__init__()
        
        # Strategy hyperparameters
        self.hp = {{
            'parameter1': 10,
            'parameter2': 20,
            # Add your parameters here
        }}
        
        # Strategy variables
        self.vars = {{
            'indicator1': [],
            'indicator2': [],
            # Add your variables here
        }}
    
    def should_long(self) -> bool:
        """
        Define long entry conditions
        """
        # Implement your long logic here
        return False
    
    def should_short(self) -> bool:
        """
        Define short entry conditions
        """
        # Implement your short logic here
        return False
    
    def should_cancel_entry(self) -> bool:
        """
        Define entry cancellation conditions
        """
        return False
    
    def before(self):
        """
        Called before strategy execution - calculate indicators
        """
        # Calculate your indicators here
        pass
    
    def after(self):
        """
        Called after strategy execution - manage positions
        """
        # Implement position management logic here
        self.update_position()
'''
    
    # Create strategy file
    strategy_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'indian_market_jesse', 'strategies'
    )
    
    filename = f"{name}.py"
    filepath = os.path.join(strategy_dir, filename)
    
    try:
        with open(filepath, 'w') as f:
            f.write(strategy_template)
        
        click.echo(f"Strategy template created: {filepath}")
        click.echo(f"You can now edit this file to implement your strategy logic.")
        
    except Exception as e:
        click.echo(f"Error creating strategy: {str(e)}")

if __name__ == '__main__':
    cli()
