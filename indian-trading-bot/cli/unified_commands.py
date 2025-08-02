#!/usr/bin/env python3

import click
from datetime import datetime, timedelta
from config.settings import settings
from database.connection import db_manager
from data_manager.unified_data_manager import UnifiedDataManager
from broker_manager.broker_factory import broker_factory

# Register brokers by importing plugins
from broker_plugins.dhan_broker import register_broker
register_broker(broker_factory)

@click.group()
def cli():
    """Indian Trading Bot - Unified CLI with OpenAlgo-style broker abstraction"""
    pass

@cli.command()
def setup():
    """Setup database and initialize reference data"""
    click.echo("Setting up database...")
    try:
        db_manager.create_tables()
        click.echo("✅ Database tables created successfully")
        
        data_manager = UnifiedDataManager()
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
@click.option('--broker', default='dhan', help='Broker name (dhan, zerodha, etc.)')
def test_broker(broker):
    """Test broker connection"""
    click.echo(f"Testing {broker} broker connection...")
    
    if broker.lower() == 'dhan':
        if not settings.DHAN_CLIENT_ID or not settings.DHAN_ACCESS_TOKEN:
            click.echo("❌ Dhan API credentials not found in .env file")
            return
        client_id = settings.DHAN_CLIENT_ID
        access_token = settings.DHAN_ACCESS_TOKEN
    else:
        click.echo(f"❌ Broker {broker} configuration not found")
        return
    
    try:
        data_manager = UnifiedDataManager()
        success = data_manager.connect_broker(broker, client_id, access_token)
        
        if success:
            click.echo("✅ Broker connection successful")
            
            # Get broker info
            broker_info = data_manager.get_broker_info()
            if broker_info:
                click.echo(f"✅ Broker: {broker_info['name']}")
                click.echo(f"✅ Client ID: {broker_info['client_id']}")
            
            data_manager.disconnect_broker()
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
@click.option('--broker', default='dhan', help='Broker to use (dhan, zerodha, etc.)')
def download_data(symbol, exchange, timeframe, from_date, to_date, days, broker):
    """Download historical data using unified broker system"""
    
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
        
        click.echo(f"📥 Downloading {timeframe} data for {symbol} ({exchange}) using {broker}")
        click.echo(f"📅 Date range: {start_date.date()} to {end_date.date()}")
        
        # Initialize unified data manager
        data_manager = UnifiedDataManager()
        
        # Connect to broker
        if broker.lower() == 'dhan':
            client_id = settings.DHAN_CLIENT_ID
            access_token = settings.DHAN_ACCESS_TOKEN
        else:
            click.echo(f"❌ Broker {broker} not supported yet")
            return
        
        success = data_manager.connect_broker(broker, client_id, access_token)
        if not success:
            click.echo("❌ Failed to connect to broker")
            return
        
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
        
        # Disconnect
        data_manager.disconnect_broker()
            
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
        data_manager = UnifiedDataManager()
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
def list_brokers():
    """List available brokers"""
    try:
        brokers = broker_factory.get_available_brokers()
        click.echo("📋 Available brokers:")
        for broker_name in brokers:
            broker_info = broker_factory.get_broker_info(broker_name)
            if broker_info:
                click.echo(f"  • {broker_name.upper()}: {broker_info.get('description', 'No description')}")
            else:
                click.echo(f"  • {broker_name.upper()}")
                
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
        data_manager = UnifiedDataManager()
        
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
    
    # Available brokers
    try:
        brokers = broker_factory.get_available_brokers()
        click.echo(f"🔌 Brokers: {len(brokers)} available ({', '.join(brokers)})")
    except:
        click.echo("❌ Brokers: Error loading")
    
    # Data status
    try:
        data_manager = UnifiedDataManager()
        instruments = data_manager.get_available_instruments()
        click.echo(f"📊 Instruments: {len(instruments)} available")
    except:
        click.echo("❌ Data Manager: Error")

if __name__ == '__main__':
    cli()