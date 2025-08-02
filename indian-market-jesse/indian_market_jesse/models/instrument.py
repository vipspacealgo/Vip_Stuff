"""
Instrument Configuration for Indian Markets

This module handles different instrument specifications like futures, options, equity MTF etc.
Users can easily configure lot sizes, margins, and other instrument-specific parameters.
"""

from typing import Dict, Optional
from enum import Enum

class InstrumentType(Enum):
    """Types of instruments supported"""
    EQUITY = "equity"
    FUTURES = "futures"
    OPTIONS = "options"
    ETF = "etf"

class Instrument:
    """
    Instrument configuration class that handles:
    - Lot sizes for futures/options
    - Margin requirements 
    - Leverage settings
    - Transaction costs
    """
    
    def __init__(self, 
                 symbol: str,
                 instrument_type: InstrumentType,
                 lot_size: int = 1,
                 margin_rate: float = 1.0,
                 tick_size: float = 0.05,
                 max_leverage: float = 1.0,
                 transaction_cost: float = 0.0003):
        """
        Initialize instrument configuration
        
        Args:
            symbol: Symbol name (e.g., 'NIFTY', 'BANKNIFTY', 'RELIANCE')
            instrument_type: Type of instrument
            lot_size: Number of shares per lot (1 for equity, 75 for NIFTY futures)
            margin_rate: Margin as percentage of contract value (0.11 = 11%)
            tick_size: Minimum price movement
            max_leverage: Maximum leverage allowed
            transaction_cost: Transaction cost as percentage (0.0003 = 0.03%)
        """
        self.symbol = symbol
        self.instrument_type = instrument_type
        self.lot_size = lot_size
        self.margin_rate = margin_rate
        self.tick_size = tick_size
        self.max_leverage = max_leverage
        self.transaction_cost = transaction_cost
    
    def calculate_contract_value(self, price: float, lots: int = 1) -> float:
        """Calculate total contract value"""
        return price * self.lot_size * lots
    
    def calculate_margin_required(self, price: float, lots: int = 1) -> float:
        """Calculate margin required for given lots"""
        contract_value = self.calculate_contract_value(price, lots)
        return contract_value * self.margin_rate
    
    def calculate_max_lots(self, capital: float, price: float, risk_percent: float = 1.0) -> int:
        """Calculate maximum lots that can be traded"""
        available_capital = capital * risk_percent
        margin_per_lot = self.calculate_margin_required(price, 1)
        
        if margin_per_lot <= 0:
            return 0
        
        return int(available_capital // margin_per_lot)
    
    def calculate_quantity(self, lots: int) -> int:
        """Convert lots to actual quantity"""
        return lots * self.lot_size
    
    def calculate_transaction_cost(self, value: float) -> float:
        """Calculate transaction cost"""
        return value * self.transaction_cost
    
    def validate_quantity(self, quantity: int) -> bool:
        """Check if quantity is valid (multiple of lot size)"""
        return quantity % self.lot_size == 0
    
    def round_to_lot_size(self, quantity: int) -> int:
        """Round quantity to nearest valid lot size"""
        return (quantity // self.lot_size) * self.lot_size
    
    def __str__(self) -> str:
        return (f"Instrument({self.symbol}, {self.instrument_type.value}, "
                f"lot_size={self.lot_size}, margin={self.margin_rate:.1%})")


class InstrumentRegistry:
    """
    Registry for pre-configured instruments
    Makes it easy for users to get instrument configs without manual setup
    """
    
    _instruments: Dict[str, Instrument] = {}
    
    @classmethod
    def register(cls, instrument: Instrument) -> None:
        """Register an instrument"""
        cls._instruments[instrument.symbol.upper()] = instrument
    
    @classmethod
    def get(cls, symbol: str) -> Optional[Instrument]:
        """Get instrument by symbol"""
        return cls._instruments.get(symbol.upper())
    
    @classmethod
    def list_instruments(cls) -> Dict[str, Instrument]:
        """List all registered instruments"""
        return cls._instruments.copy()
    
    @classmethod
    def setup_default_instruments(cls) -> None:
        """Setup commonly used Indian market instruments"""
        
        # NIFTY Futures
        cls.register(Instrument(
            symbol="NIFTY",
            instrument_type=InstrumentType.FUTURES,
            lot_size=75,
            margin_rate=0.11,  # 11%
            tick_size=0.05,
            max_leverage=9.0,  # ~1/0.11
            transaction_cost=0.0003
        ))
        
        # BANKNIFTY Futures
        cls.register(Instrument(
            symbol="BANKNIFTY", 
            instrument_type=InstrumentType.FUTURES,
            lot_size=25,
            margin_rate=0.12,  # 12%
            tick_size=0.05,
            max_leverage=8.3,  # ~1/0.12
            transaction_cost=0.0003
        ))
        
        # FINNIFTY Futures
        cls.register(Instrument(
            symbol="FINNIFTY",
            instrument_type=InstrumentType.FUTURES,
            lot_size=50,
            margin_rate=0.12,  # 12%
            tick_size=0.05,
            max_leverage=8.3,
            transaction_cost=0.0003
        ))
        
        # Equity with MTF (Margin Trading Facility)
        cls.register(Instrument(
            symbol="EQUITY_MTF",
            instrument_type=InstrumentType.EQUITY,
            lot_size=1,
            margin_rate=0.25,  # 25% for MTF
            tick_size=0.05,
            max_leverage=4.0,  # 4x leverage
            transaction_cost=0.001
        ))
        
        # Regular Equity
        cls.register(Instrument(
            symbol="EQUITY",
            instrument_type=InstrumentType.EQUITY,
            lot_size=1,
            margin_rate=1.0,  # 100% - no leverage
            tick_size=0.05,
            max_leverage=1.0,
            transaction_cost=0.001
        ))
        
        # NIFTY ETF
        cls.register(Instrument(
            symbol="NIFTY_ETF",
            instrument_type=InstrumentType.ETF,
            lot_size=1,
            margin_rate=1.0,
            tick_size=0.01,
            max_leverage=1.0,
            transaction_cost=0.0005
        ))

# Initialize default instruments
InstrumentRegistry.setup_default_instruments()