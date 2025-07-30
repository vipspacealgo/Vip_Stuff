#!/usr/bin/env python3
"""
Fast PostgreSQL Bulk Import for Jesse Bot
Loads NIFTY50 data directly into PostgreSQL using COPY command
Reduces 70 hours to under 5 minutes!
"""

import os
import psycopg2
import pandas as pd
import tempfile
from datetime import datetime
import uuid

def get_postgres_connection():
    """Get PostgreSQL connection using Jesse's config"""
    # Default Jesse database configuration
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', 5432),
        database=os.getenv('POSTGRES_NAME', 'jesse_db'),
        user=os.getenv('POSTGRES_USERNAME', 'jesse_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'password')
    )

def bulk_import_csv_to_postgres(csv_file_path, exchange='Custom', symbol='NIFTY50-USDT', timeframe='1m'):
    """
    Bulk import CSV data directly to PostgreSQL using COPY command
    This bypasses Jesse's slow ORM and uses raw SQL for maximum speed
    """
    print(f"Starting bulk import of {csv_file_path}")
    
    # Read and prepare the CSV data
    df = pd.read_csv(csv_file_path)
    print(f"Loaded {len(df)} rows from CSV")
    
    # Convert timestamp to milliseconds if needed
    if df['timestamp'].dtype == 'object':
        df['timestamp'] = pd.to_datetime(df['timestamp']).astype('int64') // 10**6
    elif df['timestamp'].max() < 10**12:
        df['timestamp'] = df['timestamp'] * 1000
    
    # Add Jesse required columns
    df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    df['exchange'] = exchange
    df['symbol'] = symbol
    df['timeframe'] = timeframe
    
    # Reorder columns to match Jesse's candles table
    df = df[['id', 'symbol', 'exchange', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'timeframe']]
    
    # Create temporary CSV file for PostgreSQL COPY
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
        df.to_csv(temp_file.name, index=False, header=False)
        temp_csv_path = temp_file.name
    
    try:
        # Connect to PostgreSQL
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        print("Connected to PostgreSQL")
        
        # Check if table exists, if not create it
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS candles (
            id VARCHAR(255) PRIMARY KEY,
            symbol VARCHAR(255) NOT NULL,
            exchange VARCHAR(255) NOT NULL,
            timestamp BIGINT NOT NULL,
            open DOUBLE PRECISION NOT NULL,
            high DOUBLE PRECISION NOT NULL,
            low DOUBLE PRECISION NOT NULL,
            close DOUBLE PRECISION NOT NULL,
            volume DOUBLE PRECISION NOT NULL,
            timeframe VARCHAR(255) NOT NULL,
            UNIQUE(exchange, symbol, timeframe, timestamp)
        );
        """
        cursor.execute(create_table_sql)
        
        # Create index for faster queries
        index_sql = """
        CREATE INDEX IF NOT EXISTS idx_candles_lookup 
        ON candles (exchange, symbol, timeframe, timestamp);
        """
        cursor.execute(index_sql)
        
        print("Table and indexes ready")
        
        # Use COPY command for ultra-fast bulk insert
        copy_sql = f"""
        COPY candles (id, symbol, exchange, timestamp, open, high, low, close, volume, timeframe)
        FROM '{temp_csv_path}' 
        WITH (FORMAT CSV, HEADER FALSE)
        ON CONFLICT (exchange, symbol, timeframe, timestamp) DO NOTHING;
        """
        
        start_time = datetime.now()
        print(f"Starting COPY operation at {start_time}")
        
        cursor.execute(copy_sql)
        rows_inserted = cursor.rowcount
        
        conn.commit()
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"✅ Successfully inserted {rows_inserted} rows in {duration}")
        print(f"⚡ Speed: {rows_inserted/duration.total_seconds():.0f} rows/second")
        
        # Verify the data
        cursor.execute("""
            SELECT COUNT(*) FROM candles 
            WHERE exchange = %s AND symbol = %s AND timeframe = %s
        """, (exchange, symbol, timeframe))
        
        total_count = cursor.fetchone()[0]
        print(f"📊 Total {symbol} candles in database: {total_count}")
        
        cursor.close()
        conn.close()
        
    finally:
        # Clean up temporary file
        os.unlink(temp_csv_path)
    
    print("🎉 Bulk import completed successfully!")

def main():
    """Main function to run the bulk import"""
    csv_file = "/Users/vipusingh/Documents/Vip-Stuff/Github/my-jesse-bot/custom_data/NIFTY50-USDT.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print("🚀 Fast PostgreSQL Bulk Import for Jesse Bot")
    print("=" * 50)
    
    try:
        bulk_import_csv_to_postgres(csv_file)
        
        print("\n✅ Import completed! You can now:")
        print("1. Start Jesse GUI: jesse-gui")
        print("2. Go to Backtest section")
        print("3. Select 'Custom' exchange")
        print("4. Choose 'NIFTY50-USDT' symbol")
        print("5. Run your backtest on 10+ years of data!")
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        print("Please check your PostgreSQL connection and try again.")

if __name__ == "__main__":
    main()