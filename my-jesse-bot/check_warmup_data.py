#!/usr/bin/env python3
"""
Check specific warmup data around 2024-01-24
"""

import os
import psycopg2
from datetime import datetime

def check_warmup_data():
    """Check if warmup data exists for the exact date Jesse is requesting"""
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='jesse_db',
        user='jesse_user',
        password='password'
    )
    
    cursor = conn.cursor()
    
    print("🔍 Checking Warmup Data for 2024-01-24")
    print("=" * 50)
    
    # Convert 2024-01-24 to timestamp
    jan_24_start = int(datetime(2024, 1, 24, 0, 0).timestamp() * 1000)
    jan_24_end = int(datetime(2024, 1, 25, 0, 0).timestamp() * 1000)
    
    print(f"📅 Looking for data from {datetime(2024, 1, 24)} onwards")
    print(f"🕐 Timestamp range: {jan_24_start} - {jan_24_end}")
    
    # Check data around 2024-01-24
    cursor.execute("""
        SELECT COUNT(*) FROM candles 
        WHERE exchange = 'Custom' AND symbol = 'NIFTY50-USDT' AND timeframe = '1m'
        AND timestamp >= %s AND timestamp < %s
    """, (jan_24_start, jan_24_end))
    
    jan_24_candles = cursor.fetchone()[0]
    print(f"📊 Candles on 2024-01-24: {jan_24_candles}")
    
    # Check a few days before (for warmup)
    jan_22_start = int(datetime(2024, 1, 22, 0, 0).timestamp() * 1000)
    cursor.execute("""
        SELECT COUNT(*) FROM candles 
        WHERE exchange = 'Custom' AND symbol = 'NIFTY50-USDT' AND timeframe = '1m'
        AND timestamp >= %s AND timestamp < %s
    """, (jan_22_start, jan_24_start))
    
    warmup_candles = cursor.fetchone()[0]
    print(f"🔄 Warmup candles (Jan 22-24): {warmup_candles}")
    
    # Find the actual date range around that time
    cursor.execute("""
        SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM candles 
        WHERE exchange = 'Custom' AND symbol = 'NIFTY50-USDT' AND timeframe = '1m'
        AND timestamp >= %s AND timestamp < %s
    """, (jan_22_start, jan_24_end + 86400000))  # +1 day
    
    min_ts, max_ts, total = cursor.fetchone()
    if min_ts and max_ts:
        min_date = datetime.fromtimestamp(min_ts / 1000).strftime('%Y-%m-%d %H:%M')
        max_date = datetime.fromtimestamp(max_ts / 1000).strftime('%Y-%m-%d %H:%M')
        print(f"📈 Actual range: {min_date} to {max_date} ({total} candles)")
    
    # Check for any gaps in the data
    cursor.execute("""
        SELECT timestamp FROM candles 
        WHERE exchange = 'Custom' AND symbol = 'NIFTY50-USDT' AND timeframe = '1m'
        AND timestamp >= %s AND timestamp < %s
        ORDER BY timestamp
        LIMIT 10
    """, (jan_22_start, jan_24_end))
    
    print("\n🕐 First 10 timestamps around that period:")
    for row in cursor.fetchall():
        ts = row[0]
        dt = datetime.fromtimestamp(ts / 1000)
        print(f"   {dt.strftime('%Y-%m-%d %H:%M:%S')} ({ts})")
    
    # Check overall data availability
    cursor.execute("""
        SELECT 
            MIN(timestamp) as first_candle,
            MAX(timestamp) as last_candle,
            COUNT(*) as total_candles
        FROM candles 
        WHERE exchange = 'Custom' AND symbol = 'NIFTY50-USDT' AND timeframe = '1m'
    """)
    
    first_ts, last_ts, total = cursor.fetchone()
    first_date = datetime.fromtimestamp(first_ts / 1000).strftime('%Y-%m-%d')
    last_date = datetime.fromtimestamp(last_ts / 1000).strftime('%Y-%m-%d')
    
    print(f"\n📋 Overall NIFTY50-USDT data:")
    print(f"   📅 Range: {first_date} to {last_date}")
    print(f"   📊 Total: {total:,} candles")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        check_warmup_data()
    except Exception as e:
        print(f"❌ Error: {e}")