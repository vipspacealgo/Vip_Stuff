#!/usr/bin/env python3
"""
Check the 'candle' table (singular) where Jesse might store real data
"""

import os
import psycopg2
from datetime import datetime

def check_candle_table():
    """Check the singular 'candle' table structure and data"""
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='jesse_db',
        user='jesse_user',
        password='password'
    )
    
    cursor = conn.cursor()
    
    print("🔍 Checking 'candle' table (singular)")
    print("=" * 40)
    
    # Check candle table structure
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'candle'
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    print("🏗️ 'candle' table structure:")
    for col_name, data_type, nullable in columns:
        print(f"   {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
    
    # Check all data in candle table
    print(f"\n📊 Data in 'candle' table:")
    cursor.execute("""
        SELECT exchange, symbol, timeframe, COUNT(*) as count,
               MIN(timestamp) as first_ts, MAX(timestamp) as last_ts
        FROM candle 
        GROUP BY exchange, symbol, timeframe
        ORDER BY count DESC;
    """)
    
    data = cursor.fetchall()
    for exchange, symbol, timeframe, count, first_ts, last_ts in data:
        if first_ts and last_ts:
            first_date = datetime.fromtimestamp(first_ts / 1000).strftime('%Y-%m-%d')
            last_date = datetime.fromtimestamp(last_ts / 1000).strftime('%Y-%m-%d')
            date_range = f"{first_date} to {last_date}"
        else:
            date_range = "No data"
        print(f"   {exchange:20} | {symbol:15} | {timeframe:3} | {count:8,} | {date_range}")
    
    # Look for BTC data in the candle table
    print("\n🔍 Looking for BTC data in 'candle' table:")
    cursor.execute("""
        SELECT exchange, symbol, timeframe, COUNT(*) as count
        FROM candle 
        WHERE symbol LIKE '%BTC%' OR symbol LIKE '%btc%'
        GROUP BY exchange, symbol, timeframe
        ORDER BY count DESC;
    """)
    
    btc_data = cursor.fetchall()
    if btc_data:
        for exchange, symbol, timeframe, count in btc_data:
            print(f"   ✅ Found BTC: {exchange} | {symbol} | {timeframe} | {count:,} candles")
            
            # Get sample data structure from BTC
            cursor.execute("""
                SELECT * FROM candle 
                WHERE exchange = %s AND symbol = %s AND timeframe = %s
                ORDER BY timestamp
                LIMIT 2;
            """, (exchange, symbol, timeframe))
            
            sample_data = cursor.fetchall()
            print(f"   📋 Sample BTC data structure:")
            for i, row in enumerate(sample_data):
                print(f"     Row {i+1}: {row}")
                
            # Check if our NIFTY data is in this table
            print(f"\n🔍 Checking if NIFTY data is in 'candle' table:")
            cursor.execute("""
                SELECT COUNT(*) FROM candle 
                WHERE exchange = 'Custom' AND symbol = 'NIFTY50-USDT' AND timeframe = '1m';
            """)
            nifty_count = cursor.fetchone()[0]
            print(f"   NIFTY50-USDT in 'candle' table: {nifty_count:,} rows")
            
            if nifty_count == 0:
                print("   ❌ NIFTY data is NOT in the 'candle' table!")
                print("   💡 We need to insert into 'candle' table, not 'candles'!")
    else:
        print("   No BTC data found in 'candle' table either")
    
    # Check for CUSTOM-USDT data (the one that's causing the error)
    print(f"\n🔍 Looking for CUSTOM-USDT data:")
    cursor.execute("""
        SELECT exchange, symbol, timeframe, COUNT(*) as count
        FROM candle 
        WHERE symbol = 'CUSTOM-USDT'
        GROUP BY exchange, symbol, timeframe;
    """)
    
    custom_data = cursor.fetchall()
    if custom_data:
        for exchange, symbol, timeframe, count in custom_data:
            print(f"   ✅ Found CUSTOM-USDT: {exchange} | {symbol} | {timeframe} | {count:,} candles")
    else:
        print("   ❌ CUSTOM-USDT not found in 'candle' table")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        check_candle_table()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()