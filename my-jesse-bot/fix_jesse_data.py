#!/usr/bin/env python3
"""
Fix Jesse's data by loading into the correct 'candle' table with proper schema
"""

import os
import psycopg2
import pandas as pd
import uuid
from datetime import datetime

def fix_jesse_candle_data():
    """Load NIFTY data into Jesse's actual 'candle' table with correct schema"""
    
    csv_file = "/Users/vipusingh/Documents/Vip-Stuff/Github/my-jesse-bot/custom_data/NIFTY50-USDT.csv"
    
    # Read CSV data
    print("📖 Reading NIFTY50 CSV data...")
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df):,} rows from CSV")
    
    # Convert timestamp to milliseconds if needed
    if df['timestamp'].dtype == 'object':
        df['timestamp'] = pd.to_datetime(df['timestamp']).astype('int64') // 10**6
    elif df['timestamp'].max() < 10**12:
        df['timestamp'] = df['timestamp'] * 1000
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='jesse_db',
        user='jesse_user',
        password='password'
    )
    
    cursor = conn.cursor()
    
    print("🗑️ Clearing old data from 'candle' table...")
    
    # Delete existing NIFTY50-USDT data from candle table
    cursor.execute("""
        DELETE FROM candle 
        WHERE exchange = 'Custom' AND symbol = 'NIFTY50-USDT' AND timeframe = '1m'
    """)
    deleted_nifty = cursor.rowcount
    print(f"Deleted {deleted_nifty:,} old NIFTY50-USDT rows")
    
    # Delete existing CUSTOM-USDT data if any
    cursor.execute("""
        DELETE FROM candle 
        WHERE exchange = 'Custom' AND symbol = 'CUSTOM-USDT' AND timeframe = '1m'
    """)
    deleted_custom = cursor.rowcount
    print(f"Deleted {deleted_custom:,} old CUSTOM-USDT rows")
    
    # Prepare data for Jesse's candle table schema
    print("🔄 Preparing data for Jesse's 'candle' table...")
    
    # Insert NIFTY50-USDT data
    print("📥 Inserting NIFTY50-USDT data...")
    nifty_data = []
    for _, row in df.iterrows():
        nifty_data.append((
            str(uuid.uuid4()),  # id (UUID)
            int(row['timestamp']),  # timestamp (bigint)
            float(row['open']),     # open (real)
            float(row['close']),    # close (real)
            float(row['high']),     # high (real)
            float(row['low']),      # low (real)
            float(row['volume']),   # volume (real)
            'Custom',               # exchange
            'NIFTY50-USDT',        # symbol
            '1m'                    # timeframe
        ))
    
    # Insert CUSTOM-USDT data (copy of NIFTY50 for compatibility)
    print("📥 Inserting CUSTOM-USDT data (copy of NIFTY50)...")
    custom_data = []
    for _, row in df.iterrows():
        custom_data.append((
            str(uuid.uuid4()),  # id (UUID)
            int(row['timestamp']),  # timestamp (bigint)
            float(row['open']),     # open (real)
            float(row['close']),    # close (real)
            float(row['high']),     # high (real)
            float(row['low']),      # low (real)
            float(row['volume']),   # volume (real)
            'Custom',               # exchange
            'CUSTOM-USDT',         # symbol
            '1m'                    # timeframe
        ))
    
    # Insert in batches to avoid memory issues
    insert_sql = """
        INSERT INTO candle (id, timestamp, open, close, high, low, volume, exchange, symbol, timeframe)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    batch_size = 10000
    
    # Insert NIFTY50-USDT
    start_time = datetime.now()
    for i in range(0, len(nifty_data), batch_size):
        batch = nifty_data[i:i + batch_size]
        cursor.executemany(insert_sql, batch)
        
        if (i // batch_size) % 10 == 0:
            print(f"   NIFTY50: {i:,} / {len(nifty_data):,} rows...")
    
    nifty_time = datetime.now() - start_time
    print(f"✅ NIFTY50-USDT: {len(nifty_data):,} rows in {nifty_time}")
    
    # Insert CUSTOM-USDT
    start_time = datetime.now()
    for i in range(0, len(custom_data), batch_size):
        batch = custom_data[i:i + batch_size]
        cursor.executemany(insert_sql, batch)
        
        if (i // batch_size) % 10 == 0:
            print(f"   CUSTOM: {i:,} / {len(custom_data):,} rows...")
    
    custom_time = datetime.now() - start_time
    print(f"✅ CUSTOM-USDT: {len(custom_data):,} rows in {custom_time}")
    
    conn.commit()
    
    # Verify the data
    print("\n📊 Verification:")
    cursor.execute("""
        SELECT symbol, COUNT(*), MIN(timestamp), MAX(timestamp) 
        FROM candle 
        WHERE exchange = 'Custom' AND timeframe = '1m'
        GROUP BY symbol
        ORDER BY symbol;
    """)
    
    for symbol, count, min_ts, max_ts in cursor.fetchall():
        min_date = datetime.fromtimestamp(min_ts / 1000).strftime('%Y-%m-%d')
        max_date = datetime.fromtimestamp(max_ts / 1000).strftime('%Y-%m-%d')
        print(f"   {symbol}: {count:,} candles ({min_date} to {max_date})")
    
    # Check for 2017 data specifically (for the warmup error)
    print("\n🎯 Checking 2017 data for warmup:")
    jan_24_2017 = int(datetime(2017, 1, 24, 0, 0).timestamp() * 1000)
    jan_25_2017 = int(datetime(2017, 1, 25, 0, 0).timestamp() * 1000)
    
    cursor.execute("""
        SELECT symbol, COUNT(*) 
        FROM candle 
        WHERE exchange = 'Custom' AND timeframe = '1m'
        AND timestamp >= %s AND timestamp < %s
        GROUP BY symbol;
    """, (jan_24_2017, jan_25_2017))
    
    warmup_data = cursor.fetchall()
    for symbol, count in warmup_data:
        print(f"   {symbol} on 2017-01-24: {count} candles ✅")
    
    if not warmup_data:
        print("   ❌ No data for 2017-01-24 - checking actual date range...")
        cursor.execute("""
            SELECT symbol, MIN(timestamp), MAX(timestamp) 
            FROM candle 
            WHERE exchange = 'Custom' AND timeframe = '1m'
            GROUP BY symbol;
        """)
        for symbol, min_ts, max_ts in cursor.fetchall():
            min_date = datetime.fromtimestamp(min_ts / 1000).strftime('%Y-%m-%d')
            max_date = datetime.fromtimestamp(max_ts / 1000).strftime('%Y-%m-%d')
            print(f"   {symbol} actual range: {min_date} to {max_date}")
    
    cursor.close()
    conn.close()
    
    print("\n🎉 Data loaded into Jesse's 'candle' table successfully!")
    print("Now both NIFTY50-USDT and CUSTOM-USDT should be available for backtesting!")

if __name__ == "__main__":
    try:
        fix_jesse_candle_data()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()