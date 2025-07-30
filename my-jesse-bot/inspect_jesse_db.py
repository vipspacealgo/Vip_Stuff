#!/usr/bin/env python3
"""
Inspect Jesse's actual database structure and find BTC-USDT data
"""

import os
import psycopg2
from datetime import datetime

def inspect_jesse_database():
    """Inspect Jesse's database to understand its exact structure"""
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='jesse_db',
        user='jesse_user',
        password='password'
    )
    
    cursor = conn.cursor()
    
    print("🔍 Inspecting Jesse's Database Structure")
    print("=" * 50)
    
    # Get all tables
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    print("📋 Available tables:")
    for table in tables:
        print(f"   - {table[0]}")
    
    # Check candles table structure
    if any('candles' in str(table) for table in tables):
        print("\n🏗️ Candles table structure:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'candles'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        for col_name, data_type, nullable in columns:
            print(f"   {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
    
    # Check all data in the database
    print("\n📊 All data in database:")
    cursor.execute("""
        SELECT exchange, symbol, timeframe, COUNT(*) as count,
               MIN(timestamp) as first_ts, MAX(timestamp) as last_ts
        FROM candles 
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
    
    # Look specifically for BTC-USDT data
    print("\n🔍 Looking for BTC-USDT data:")
    cursor.execute("""
        SELECT exchange, symbol, timeframe, COUNT(*) as count
        FROM candles 
        WHERE symbol LIKE '%BTC%' OR symbol LIKE '%btc%'
        GROUP BY exchange, symbol, timeframe
        ORDER BY count DESC;
    """)
    
    btc_data = cursor.fetchall()
    if btc_data:
        for exchange, symbol, timeframe, count in btc_data:
            print(f"   Found: {exchange} | {symbol} | {timeframe} | {count:,} candles")
            
            # Get sample data structure
            cursor.execute("""
                SELECT * FROM candles 
                WHERE exchange = %s AND symbol = %s AND timeframe = %s
                ORDER BY timestamp
                LIMIT 3;
            """, (exchange, symbol, timeframe))
            
            sample_data = cursor.fetchall()
            print(f"   Sample data for {symbol}:")
            for row in sample_data:
                print(f"     {row}")
    else:
        print("   No BTC data found")
    
    # Check Jesse's internal database location
    print("\n🗂️ Database connection info:")
    cursor.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port();")
    db_info = cursor.fetchone()
    print(f"   Database: {db_info[0]}")
    print(f"   User: {db_info[1]}")
    print(f"   Host: {db_info[2] or 'localhost'}")
    print(f"   Port: {db_info[3] or 5432}")
    
    # Check for any Jesse-specific tables or configurations
    print("\n🔧 Jesse-specific tables:")
    for table_name in [t[0] for t in tables]:
        if table_name != 'candles':
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"   {table_name}: {count} rows")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        inspect_jesse_database()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()