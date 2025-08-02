#!/usr/bin/env python3

import os
from datetime import datetime, timedelta
from config.settings import settings
from database.connection import db_manager
from brokers.dhan import DhanBroker
from data_manager.data_manager import DataManager

def test_database_connection():
    print("Testing database connection...")
    if db_manager.test_connection():
        print("✓ Database connection successful")
        return True
    else:
        print("✗ Database connection failed")
        return False

def setup_database():
    print("Setting up database tables...")
    try:
        db_manager.create_tables()
        print("✓ Database tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating database tables: {e}")
        return False

def test_broker_connection():
    print("Testing broker connection...")
    
    if not settings.DHAN_CLIENT_ID or not settings.DHAN_ACCESS_TOKEN:
        print("✗ Dhan API credentials not found. Please set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN in .env file")
        return None
    
    try:
        broker = DhanBroker(settings.DHAN_CLIENT_ID, settings.DHAN_ACCESS_TOKEN)
        if broker.connect():
            print("✓ Broker connection successful")
            profile = broker.get_profile()
            if profile and profile.get('status') == 'success':
                print(f"✓ Profile retrieved successfully")
            return broker
        else:
            print("✗ Broker connection failed")
            return None
    except Exception as e:
        print(f"✗ Error connecting to broker: {e}")
        return None

def test_data_operations(broker, data_manager):
    print("\nTesting data operations...")
    
    symbol = "RELIANCE"
    exchange = "NSE"
    timeframe = "1D"
    
    data_manager.add_instrument(exchange, symbol)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"Downloading data for {symbol} from {start_date.date()} to {end_date.date()}")
    
    success = data_manager.download_and_store_data(
        broker=broker,
        exchange_code=exchange,
        symbol=symbol,
        timeframe=timeframe,
        from_date=start_date,
        to_date=end_date
    )
    
    if success:
        print("✓ Data download and storage successful")
        
        stored_data = data_manager.get_stored_data(
            exchange_code=exchange,
            symbol=symbol,
            timeframe=timeframe,
            from_date=start_date,
            to_date=end_date
        )
        
        if not stored_data.empty:
            print(f"✓ Retrieved {len(stored_data)} records from database")
            print(f"Data range: {stored_data['timestamp'].min()} to {stored_data['timestamp'].max()}")
            print("\nSample data:")
            print(stored_data.head())
            return True
        else:
            print("✗ No data retrieved from database")
            return False
    else:
        print("✗ Data download failed")
        return False

def main():
    print("=== Indian Trading Bot - Initial Test ===\n")
    
    if not test_database_connection():
        return
    
    if not setup_database():
        return
    
    data_manager = DataManager()
    print("✓ Data manager initialized")
    
    broker = test_broker_connection()
    if not broker:
        return
    
    if test_data_operations(broker, data_manager):
        print("\n=== All tests passed! ===")
        print("\n✅ COMPLETED COMPONENTS:")
        print("- Database connection and schema setup")
        print("- Broker connection with Dhan API")
        print("- Data manager for downloading and storing OHLCV data")
        print("- PostgreSQL storage with proper indexing")
        print("- Basic data retrieval functionality")
        
        print("\n⏳ PENDING COMPONENTS:")
        print("- GUI for user interaction")
        print("- Strategy engine integration") 
        print("- Backtesting engine with vectorbt")
        print("- Live trading order placement")
        print("- Interactive charting and trade navigation")
        print("- Additional broker integrations")
        print("- Strategy import/export functionality")
        
    else:
        print("\n=== Some tests failed ===")
    
    print(f"\nInstruments available:")
    instruments = data_manager.get_available_instruments()
    for inst in instruments:
        print(f"- {inst['symbol']} ({inst['exchange']})")

if __name__ == "__main__":
    main()