#!/usr/bin/env python3
"""
Reload fresh NIFTY50 data directly from CSV to fix data corruption
"""

import psycopg2
import pandas as pd
import uuid
from datetime import datetime

def reload_fresh_data():
    """Load fresh data directly from CSV to correct table"""
    
    csv_file = "/Users/vipusingh/Documents/Vip-Stuff/Github/my-jesse-bot/custom_data/NIFTY50-USDT.csv"
    
    print("🔄 Reloading fresh NIFTY50 data from CSV")
    print("=" * 50)
    
    # Read CSV data
    df = pd.read_csv(csv_file)
    print(f"📖 Loaded {len(df):,} rows from CSV")
    
    # Convert timestamp to milliseconds if needed
    if df['timestamp'].dtype == 'object':
        df['timestamp'] = pd.to_datetime(df['timestamp']).astype('int64') // 10**6
    elif df['timestamp'].max() < 10**12:
        df['timestamp'] = df['timestamp'] * 1000
    
    # Verify CSV data quality
    jan_2_start = int(datetime(2024, 1, 2, 0, 0).timestamp() * 1000)
    jan_3_start = int(datetime(2024, 1, 3, 0, 0).timestamp() * 1000)
    jan_2_data = df[(df['timestamp'] >= jan_2_start) & (df['timestamp'] < jan_3_start)]
    
    print(f"✅ CSV has {len(jan_2_data)} rows for Jan 2, 2024")
    if len(jan_2_data) > 0:
        sample = jan_2_data.iloc[0]
        print(f"   Sample: open={sample['open']} high={sample['high']} low={sample['low']} close={sample['close']}")
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='jesse_db',
        user='jesse_user',
        password='password'
    )
    
    cursor = conn.cursor()
    
    # Delete existing NIFTY50-USDT data
    cursor.execute("""
        DELETE FROM candle 
        WHERE exchange = 'Custom' AND symbol = 'NIFTY50-USDT' AND timeframe = '1m'
    """)
    deleted = cursor.rowcount
    print(f"🗑️ Deleted {deleted:,} old NIFTY50-USDT rows")
    
    # Insert fresh data from CSV
    insert_sql = """
        INSERT INTO candle (id, timestamp, open, close, high, low, volume, exchange, symbol, timeframe)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    batch_size = 10000
    inserted = 0
    
    print("📥 Inserting fresh data...")
    for i in range(0, len(df), batch_size):
        batch = []
        for _, row in df.iloc[i:i + batch_size].iterrows():
            batch.append((
                str(uuid.uuid4()),      # id as UUID
                int(row['timestamp']),  # timestamp
                float(row['open']),     # open
                float(row['close']),    # close  
                float(row['high']),     # high
                float(row['low']),      # low
                float(row['volume']),   # volume
                'Custom',               # exchange
                'NIFTY50-USDT',        # symbol
                '1m'                    # timeframe
            ))
        
        cursor.executemany(insert_sql, batch)
        inserted += len(batch)
        
        if i % (batch_size * 10) == 0:
            print(f"   Progress: {inserted:,} / {len(df):,} rows...")
    
    conn.commit()
    print(f"✅ Successfully inserted {inserted:,} fresh rows")
    
    # Verify the fix
    cursor.execute("""
        SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM candle 
        WHERE exchange = 'Custom' AND symbol = 'NIFTY50-USDT' AND timeframe = '1m'
    """)
    count, min_ts, max_ts = cursor.fetchone()
    
    min_date = datetime.fromtimestamp(min_ts / 1000).strftime('%Y-%m-%d')
    max_date = datetime.fromtimestamp(max_ts / 1000).strftime('%Y-%m-%d')
    
    print(f"📊 Final verification:")
    print(f"   NIFTY50-USDT: {count:,} candles ({min_date} to {max_date})")
    
    # Check Jan 2, 2024 data quality
    cursor.execute("""
        SELECT timestamp, open, high, low, close, volume FROM candle 
        WHERE exchange = 'Custom' AND symbol = 'NIFTY50-USDT' AND timeframe = '1m'
        AND timestamp >= %s AND timestamp < %s
        ORDER BY timestamp
        LIMIT 3
    """, (jan_2_start, jan_3_start))
    
    print(f"🎯 Jan 2, 2024 data quality check:")
    for timestamp, open_p, high, low, close, volume in cursor.fetchall():
        dt = datetime.fromtimestamp(timestamp / 1000)
        print(f"   {dt}: open={open_p} high={high} low={low} close={close}")
        
        # Verify data has variation
        if open_p != high or high != low or low != close:
            print("   ✅ Data has proper OHLC variation!")
            break
    else:
        print("   ❌ Data still has identical OHLC values")
    
    cursor.close()
    conn.close()
    
    print("\n🎉 Fresh data reload complete!")

if __name__ == "__main__":
    try:
        reload_fresh_data()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()