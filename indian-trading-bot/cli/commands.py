#!/usr/bin/env python3

import click
from datetime import datetime, timedelta
from config.settings import settings
from database.connection import db_manager
from brokers.dhan import DhanBroker
from data_manager.data_manager import DataManager

@click.group()
def cli():
    """Indian Trading Bot CLI"""
    pass

@cli.command()
def setup():
    """Setup database and initialize reference data"""
    click.echo("Setting up database...")
    try:
        db_manager.create_tables()
        click.echo("✅ Database tables created successfully")
        
        data_manager = DataManager()
        click.echo("✅ Reference data initialized")
        
    except Exception as e:
        click.echo(f"❌ Setup failed: {e}")

@cli.command()
def test_db():
    """Test database connection"""
    click.echo("Testing database connection...")
    if db_manager.test_connection():
        click.echo("✅ Database connection successful")
    else:
        click.echo("❌ Database connection failed")

@cli.command()
def test_broker():
    """Test broker connection"""
    click.echo("Testing Dhan broker connection...")
    
    if not settings.DHAN_CLIENT_ID or not settings.DHAN_ACCESS_TOKEN:
        click.echo("❌ Dhan API credentials not found in .env file")
        return
    
    try:
        broker = DhanBroker(settings.DHAN_CLIENT_ID, settings.DHAN_ACCESS_TOKEN)
        if broker.connect():
            click.echo("✅ Broker connection successful")
            
            profile = broker.get_profile()
            if profile and profile.get('status') == 'success':
                click.echo("✅ Profile retrieved successfully")
                click.echo(f"Client ID: {settings.DHAN_CLIENT_ID}")
            else:
                click.echo("⚠️  Connected but profile retrieval failed")
        else:
            click.echo("❌ Broker connection failed")
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
@click.option('--symbol', default='NIFTY50', help='Stock symbol')
@click.option('--exchange', default='NSE', help='Exchange code')
@click.option('--timeframe', default='1D', help='Timeframe (1m, 5m, 15m, 1h, 1D)')
@click.option('--from-date', help='Start date (YYYY-MM-DD) - defaults to start of year')
@click.option('--to-date', help='End date (YYYY-MM-DD) - defaults to today')
@click.option('--days', help='Number of days from today (alternative to date range)')
def download_data(symbol, exchange, timeframe, from_date, to_date, days):
    """Download historical data for a symbol with date range support"""
    
    try:
        # Parse date range
        if days:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=int(days))
        elif from_date and to_date:
            start_date = datetime.strptime(from_date, '%Y-%m-%d')
            end_date = datetime.strptime(to_date, '%Y-%m-%d')
        elif from_date:
            start_date = datetime.strptime(from_date, '%Y-%m-%d')
            end_date = datetime.now()
        else:
            # Default: from start of 2025 to today
            start_date = datetime(2025, 1, 1)
            end_date = datetime.now()
        
        click.echo(f"📥 Downloading {timeframe} data for {symbol} ({exchange})")
        click.echo(f"📅 Date range: {start_date.date()} to {end_date.date()}")
        
        # Initialize components
        broker = DhanBroker(settings.DHAN_CLIENT_ID, settings.DHAN_ACCESS_TOKEN)
        if not broker.connect():
            click.echo("❌ Failed to connect to broker")
            return
        
        data_manager = DataManager()
        
        # Add instrument if not exists
        data_manager.add_instrument(exchange, symbol)
        
        # Check if data already exists
        existing_data = data_manager.get_stored_data(
            exchange_code=exchange,
            symbol=symbol,
            timeframe=timeframe,
            from_date=start_date,
            to_date=end_date
        )
        
        if not existing_data.empty:
            click.echo(f"⚠️  Data already exists for {symbol} ({exchange}) {timeframe}")
            click.echo(f"📊 Found {len(existing_data)} existing records")
            click.echo(f"📅 Existing range: {existing_data['timestamp'].min()} to {existing_data['timestamp'].max()}")
            
            if not click.confirm("Do you want to download and update anyway?", default=False):
                click.echo("❌ Download cancelled by user")
                return
        
        # Download data
        success = data_manager.download_and_store_data(
            broker=broker,
            exchange_code=exchange,
            symbol=symbol,
            timeframe=timeframe,
            from_date=start_date,
            to_date=end_date
        )
        
        if success:
            click.echo("✅ Data downloaded and stored successfully")
            
            # Show updated data summary
            stored_data = data_manager.get_stored_data(
                exchange_code=exchange,
                symbol=symbol,
                timeframe=timeframe,
                from_date=start_date,
                to_date=end_date
            )
            
            if not stored_data.empty:
                click.echo(f"\n📊 Final dataset summary:")
                click.echo(f"  Total records: {len(stored_data)}")
                click.echo(f"  Date range: {stored_data['timestamp'].min()} to {stored_data['timestamp'].max()}")
                click.echo(f"  Latest close: ₹{stored_data['close'].iloc[-1]:.2f}")
                click.echo(f"  Period high: ₹{stored_data['high'].max():.2f}")
                click.echo(f"  Period low: ₹{stored_data['low'].min():.2f}")
                
                click.echo(f"\n📈 Latest 5 records:")
                latest_data = stored_data.tail()
                for _, row in latest_data.iterrows():
                    click.echo(f"  {row['timestamp'].date()}: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f} V={row['volume']:,}")
            else:
                click.echo("⚠️  No data retrieved after download")
        else:
            click.echo("❌ Data download failed")
            
    except ValueError as e:
        click.echo(f"❌ Date format error: {e}")
        click.echo("💡 Use format YYYY-MM-DD for dates")
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
@click.option('--exchange', help='Filter by exchange code')
def list_instruments(exchange):
    """List available instruments"""
    try:
        data_manager = DataManager()
        instruments = data_manager.get_available_instruments(exchange)
        
        if instruments:
            click.echo(f"\n📋 Available instruments:")
            for inst in instruments:
                click.echo(f"  {inst['symbol']} ({inst['exchange']}) - Lot Size: {inst['lot_size']}")
        else:
            click.echo("No instruments found")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
@click.option('--symbol', required=True, help='Stock symbol')
@click.option('--exchange', default='NSE', help='Exchange code') 
@click.option('--timeframe', default='1D', help='Timeframe')
@click.option('--days', default=30, help='Number of days')
def show_data(symbol, exchange, timeframe, days):
    """Show stored data for a symbol"""
    try:
        data_manager = DataManager()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        data = data_manager.get_stored_data(
            exchange_code=exchange,
            symbol=symbol,
            timeframe=timeframe,
            from_date=start_date,
            to_date=end_date
        )
        
        if not data.empty:
            click.echo(f"\n📊 Data for {symbol} ({exchange}) - {timeframe}")
            click.echo(f"📅 {len(data)} records from {data['timestamp'].min()} to {data['timestamp'].max()}")
            click.echo(f"\n💰 Price Summary:")
            click.echo(f"  Latest Close: ₹{data['close'].iloc[-1]:.2f}")
            click.echo(f"  Highest: ₹{data['high'].max():.2f}")
            click.echo(f"  Lowest: ₹{data['low'].min():.2f}")
            click.echo(f"  Average Volume: {data['volume'].mean():,.0f}")
            
            click.echo(f"\n📈 Recent data:")
            click.echo(data.tail(10).to_string(index=False))
        else:
            click.echo(f"❌ No data found for {symbol}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
def status():
    """Show system status"""
    click.echo("🔍 System Status Check\n")
    
    # Database status
    if db_manager.test_connection():
        click.echo("✅ Database: Connected")
    else:
        click.echo("❌ Database: Failed")
    
    # Broker status
    try:
        broker = DhanBroker(settings.DHAN_CLIENT_ID, settings.DHAN_ACCESS_TOKEN)
        if broker.connect():
            click.echo("✅ Broker: Connected")
        else:
            click.echo("❌ Broker: Failed")
    except:
        click.echo("❌ Broker: Error")
    
    # Data status
    try:
        data_manager = DataManager()
        instruments = data_manager.get_available_instruments()
        click.echo(f"📊 Instruments: {len(instruments)} available")
    except:
        click.echo("❌ Data Manager: Error")

if __name__ == '__main__':
    cli()