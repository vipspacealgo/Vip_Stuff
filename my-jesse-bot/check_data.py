#!/usr/bin/env python3
"""
Check if Jesse can see the imported NIFTY50 data
"""

import os
import psycopg2
from datetime import datetime

def check_jesse_database():
    """Check if data is properly loaded in Jesse's database"""
    
    # Use Jesse's exact configuration
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='jesse_db',
        user='jesse_user',
        password='password'
    )
    
    cursor = conn.cursor()
    
    print("🔍 Checking Jesse's Database")
    print("=" * 40)
    
    # Check if candles table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'candles'
        );
    """)
    table_exists = cursor.fetchone()[0]
    print(f"📋 Candles table exists: {table_exists}")
    
    if not table_exists:
        print("❌ Candles table not found!")
        return
    
    # Check total candles
    cursor.execute("SELECT COUNT(*) FROM candles")
    total_candles = cursor.fetchone()[0]
    print(f"📊 Total candles in database: {total_candles:,}")
    
    # Check NIFTY50 data specifically
    cursor.execute("""
        SELECT COUNT(*) FROM candles 
        WHERE exchange = 'Custom' AND symbol = 'NIFTY50-USDT' AND timeframe = '1m'
    """)
    nifty_candles = cursor.fetchone()[0]
    print(f"🏛️ NIFTY50-USDT candles: {nifty_candles:,}")
    
    if nifty_candles > 0:
        # Check date range
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp) FROM candles 
            WHERE exchange = 'Custom' AND symbol = 'NIFTY50-USDT' AND timeframe = '1m'
        """)
        min_ts, max_ts = cursor.fetchone()
        min_date = datetime.fromtimestamp(min_ts / 1000).strftime('%Y-%m-%d %H:%M')
        max_date = datetime.fromtimestamp(max_ts / 1000).strftime('%Y-%m-%d %H:%M')
        print(f"📅 Date range: {min_date} to {max_date}")
        
        # Check for 2024 data (warmup period)
        cursor.execute("""
            SELECT COUNT(*) FROM candles 
            WHERE exchange = 'Custom' AND symbol = 'NIFTY50-USDT' AND timeframe = '1m'
            AND timestamp >= 1704067200000  -- 2024-01-01
            AND timestamp < 1735689600000   -- 2025-01-01
        """)
        candles_2024 = cursor.fetchone()[0]
        print(f"📈 2024 candles available: {candles_2024:,}")
        
        # Check for recent data around 2024-01-02
        cursor.execute("""
            SELECT COUNT(*) FROM candles 
            WHERE exchange = 'Custom' AND symbol = 'NIFTY50-USDT' AND timeframe = '1m'
            AND timestamp >= 1704153600000  -- 2024-01-02
            AND timestamp < 1704240000000   -- 2024-01-03
        """)
        jan_2_candles = cursor.fetchone()[0]
        print(f"🎯 Jan 2, 2024 candles: {jan_2_candles}")
        
        if jan_2_candles > 0:
            print("✅ Warmup data is available!")
        else:
            print("❌ Missing warmup data for 2024-01-02")
    
    # Check other symbols for comparison
    cursor.execute("""
        SELECT exchange, symbol, timeframe, COUNT(*) as count
        FROM candles 
        GROUP BY exchange, symbol, timeframe
        ORDER BY count DESC
        LIMIT 10
    """)
    
    print("\n📋 All available data:")
    for row in cursor.fetchall():
        exchange, symbol, timeframe, count = row
        print(f"   {exchange} | {symbol} | {timeframe} | {count:,} candles")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        check_jesse_database()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure PostgreSQL is running and Jesse's database is accessible.")