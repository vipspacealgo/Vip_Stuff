#!/usr/bin/env python3
"""
Batch Insert for Jesse Bot
Uses executemany for fast bulk inserts without file permissions
"""

import os
import psycopg2
import pandas as pd
from datetime import datetime
import uuid

def get_postgres_connection():
    """Get PostgreSQL connection using Jesse's config"""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', 5432),
        database=os.getenv('POSTGRES_NAME', 'jesse_db'),
        user=os.getenv('POSTGRES_USERNAME', 'jesse_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'password')
    )

def batch_import_csv_to_postgres(csv_file_path, exchange='Custom', symbol='NIFTY50-USDT', timeframe='1m'):
    """Batch import CSV data using executemany"""
    print(f"Starting batch import of {csv_file_path}")
    
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
            timeframe VARCHAR(255) NOT NULL
        );
        """
        cursor.execute(create_table_sql)
        
        # Create unique index to prevent duplicates
        try:
            index_sql = """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_candles_unique 
            ON candles (exchange, symbol, timeframe, timestamp);
            """
            cursor.execute(index_sql)
        except:
            pass  # Index might already exist
        
        print("Table and indexes ready")
        
        # Delete existing data for this symbol to avoid conflicts
        delete_sql = """
        DELETE FROM candles 
        WHERE exchange = %s AND symbol = %s AND timeframe = %s
        """
        cursor.execute(delete_sql, (exchange, symbol, timeframe))
        deleted_rows = cursor.rowcount
        print(f"Deleted {deleted_rows} existing rows for {symbol}")
        
        # Prepare data for batch insert
        data_tuples = [tuple(row) for row in df.values]
        
        # Use executemany for batch insert
        insert_sql = """
        INSERT INTO candles (id, symbol, exchange, timestamp, open, high, low, close, volume, timeframe)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        start_time = datetime.now()
        print(f"Starting batch insert at {start_time}")
        
        # Insert in chunks to avoid memory issues
        chunk_size = 10000
        total_inserted = 0
        
        for i in range(0, len(data_tuples), chunk_size):
            chunk = data_tuples[i:i + chunk_size]
            cursor.executemany(insert_sql, chunk)
            total_inserted += len(chunk)
            
            if i % (chunk_size * 10) == 0:  # Progress every 100k rows
                print(f"Inserted {total_inserted:,} / {len(data_tuples):,} rows...")
        
        conn.commit()
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"✅ Successfully inserted {total_inserted:,} rows in {duration}")
        print(f"⚡ Speed: {total_inserted/duration.total_seconds():.0f} rows/second")
        
        # Verify the data
        cursor.execute("""
            SELECT COUNT(*) FROM candles 
            WHERE exchange = %s AND symbol = %s AND timeframe = %s
        """, (exchange, symbol, timeframe))
        
        total_count = cursor.fetchone()[0]
        print(f"📊 Total {symbol} candles in database: {total_count:,}")
        
        # Show date range
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp) FROM candles 
            WHERE exchange = %s AND symbol = %s AND timeframe = %s
        """, (exchange, symbol, timeframe))
        
        min_ts, max_ts = cursor.fetchone()
        min_date = datetime.fromtimestamp(min_ts / 1000).strftime('%Y-%m-%d')
        max_date = datetime.fromtimestamp(max_ts / 1000).strftime('%Y-%m-%d')
        print(f"📅 Date range: {min_date} to {max_date}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        raise
    
    print("🎉 Batch import completed successfully!")

def main():
    """Main function to run the batch import"""
    csv_file = "/Users/vipusingh/Documents/Vip-Stuff/Github/my-jesse-bot/custom_data/NIFTY50-USDT.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print("🚀 Batch PostgreSQL Import for Jesse Bot")
    print("=" * 50)
    
    try:
        batch_import_csv_to_postgres(csv_file)
        
        print("\n✅ Import completed! Your NIFTY50 data is now ready!")
        print("You can now run backtests with 932K+ candles from 2015-2025")
        
    except Exception as e:
        print(f"❌ Error during import: {e}")

if __name__ == "__main__":
    main()