#!/usr/bin/env python3
"""
Futures Trading Examples for Indian Jesse

This file shows how easy it is to trade different futures instruments
with the new instrument configuration system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indian_market_jesse.models.instrument import InstrumentRegistry, Instrument, InstrumentType
from indian_market_jesse.strategies.futures_mean_reversion import FuturesMeanReversion

def example_1_list_available_instruments():
    """Show all available instruments"""
    print("=== Available Instruments ===")
    instruments = InstrumentRegistry.list_instruments()
    
    for symbol, instrument in instruments.items():
        print(f"{symbol}: {instrument}")
    print()

def example_2_calculate_margin_requirements():
    """Calculate margin requirements for different instruments"""
    print("=== Margin Calculations ===")
    
    # Get instruments
    nifty = InstrumentRegistry.get("NIFTY")
    banknifty = InstrumentRegistry.get("BANKNIFTY")
    
    price_nifty = 23500
    price_banknifty = 48000
    
    print(f"NIFTY at ₹{price_nifty}:")
    print(f"  Contract Value: ₹{nifty.calculate_contract_value(price_nifty):,.0f}")
    print(f"  Margin Required: ₹{nifty.calculate_margin_required(price_nifty):,.0f}")
    print(f"  Max lots with ₹5L: {nifty.calculate_max_lots(500000, price_nifty)}")
    print()
    
    print(f"BANKNIFTY at ₹{price_banknifty}:")
    print(f"  Contract Value: ₹{banknifty.calculate_contract_value(price_banknifty):,.0f}")
    print(f"  Margin Required: ₹{banknifty.calculate_margin_required(price_banknifty):,.0f}")
    print(f"  Max lots with ₹3L: {banknifty.calculate_max_lots(300000, price_banknifty)}")
    print()

def example_3_add_custom_instrument():
    """Add a custom futures instrument"""
    print("=== Adding Custom Instrument ===")
    
    # Add a custom commodity futures contract
    gold_futures = Instrument(
        symbol="GOLD",
        instrument_type=InstrumentType.FUTURES,
        lot_size=100,           # 100 grams per lot
        margin_rate=0.08,       # 8% margin
        tick_size=1.0,          # ₹1 minimum price movement
        max_leverage=12.5,      # ~1/0.08
        transaction_cost=0.0002 # 0.02% transaction cost
    )
    
    InstrumentRegistry.register(gold_futures)
    print(f"Added: {gold_futures}")
    
    # Test calculations
    gold_price = 6000  # ₹6000 per gram
    print(f"Gold at ₹{gold_price}/gram:")
    print(f"  Contract Value: ₹{gold_futures.calculate_contract_value(gold_price):,.0f}")
    print(f"  Margin Required: ₹{gold_futures.calculate_margin_required(gold_price):,.0f}")
    print()

def example_4_strategy_with_different_instruments():
    """Show how to create strategies for different instruments"""
    print("=== Strategy Examples ===")
    
    # NIFTY Strategy
    nifty_strategy = FuturesMeanReversion("NIFTY")
    print(f"NIFTY Strategy using: {nifty_strategy.instrument}")
    
    # BANKNIFTY Strategy  
    banknifty_strategy = FuturesMeanReversion("BANKNIFTY")
    print(f"BANKNIFTY Strategy using: {banknifty_strategy.instrument}")
    
    # Custom instrument strategy (if added in example_3)
    try:
        gold_strategy = FuturesMeanReversion("GOLD")
        print(f"GOLD Strategy using: {gold_strategy.instrument}")
    except:
        print("GOLD instrument not available (run example_3 first)")
    print()

def example_5_capital_recommendations():
    """Show capital recommendations for different instruments"""
    print("=== Capital Recommendations ===")
    
    instruments_data = [
        ("NIFTY", 23500, "Conservative futures trading"),
        ("BANKNIFTY", 48000, "High volatility, smaller lots"),
        ("FINNIFTY", 20000, "Mid-tier futures trading"),
        ("EQUITY_MTF", 500, "Leveraged equity trading"),
    ]
    
    print(f"{'Instrument':<12} {'Price':<8} {'1 Lot Margin':<12} {'Rec. Capital':<12} {'Description'}")
    print("-" * 80)
    
    for symbol, price, description in instruments_data:
        instrument = InstrumentRegistry.get(symbol)
        if instrument:
            margin = instrument.calculate_margin_required(price)
            rec_capital = margin * 2.5  # 2.5x margin as recommended capital
            
            print(f"{symbol:<12} ₹{price:<7} ₹{margin:<11,.0f} ₹{rec_capital:<11,.0f} {description}")
    print()

if __name__ == "__main__":
    print("🚀 Indian Jesse Futures Trading Examples\n")
    
    example_1_list_available_instruments()
    example_2_calculate_margin_requirements()
    example_3_add_custom_instrument()
    example_4_strategy_with_different_instruments()
    example_5_capital_recommendations()
    
    print("💡 Usage Tips:")
    print("1. Always ensure 2-3x margin as available capital")
    print("2. Use --instrument parameter to specify futures type")
    print("3. Check margin requirements before live trading")
    print("4. Add custom instruments in instrument.py for new contracts")
    print("\n⚡ Ready for futures trading with proper risk management!")