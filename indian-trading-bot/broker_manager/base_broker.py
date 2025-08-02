from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
from dataclasses import dataclass
from enum import Enum

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "SL"
    STOP_LOSS_MARKET = "SL-M"

class TransactionType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class ProductType(Enum):
    INTRADAY = "INTRADAY"
    DELIVERY = "DELIVERY"
    MARGIN = "MARGIN"

class ExchangeSegment(Enum):
    NSE_EQ = "NSE_EQ"       # NSE Equity
    BSE_EQ = "BSE_EQ"       # BSE Equity
    NSE_FNO = "NSE_FNO"     # NSE F&O
    BSE_FNO = "BSE_FNO"     # BSE F&O
    MCX_COMM = "MCX_COMM"   # MCX Commodity
    IDX_I = "IDX_I"         # Index

class InstrumentType(Enum):
    EQUITY = "EQUITY"
    INDEX = "INDEX"
    FUTIDX = "FUTIDX"       # Index Futures
    FUTSTK = "FUTSTK"       # Stock Futures
    OPTIDX = "OPTIDX"       # Index Options
    OPTSTK = "OPTSTK"       # Stock Options
    FUTCOM = "FUTCOM"       # Commodity Futures

@dataclass
class SecurityInfo:
    security_id: str
    exchange_segment: ExchangeSegment
    instrument_type: InstrumentType
    symbol: str
    lot_size: int = 1

@dataclass
class OrderRequest:
    security_info: SecurityInfo
    quantity: int
    price: float
    order_type: OrderType
    transaction_type: TransactionType
    product_type: ProductType
    trigger_price: Optional[float] = None
    disclosed_quantity: Optional[int] = None
    validity: str = "DAY"

@dataclass
class OrderResponse:
    order_id: Optional[str]
    status: str
    message: str
    timestamp: datetime

@dataclass
class Position:
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    current_price: float
    pnl: float
    product_type: str

@dataclass
class MarginInfo:
    available_cash: float
    used_margin: float
    collateral: float
    total_margin: float

class BaseBrokerInterface(ABC):
    """
    Abstract base class for all broker implementations.
    Provides unified interface for order management, data fetching, and account operations.
    """
    
    def __init__(self, client_id: str, access_token: str):
        self.client_id = client_id
        self.access_token = access_token
        self.is_connected = False
        self._security_master = {}
    
    @abstractmethod
    def connect(self) -> Tuple[bool, Optional[str]]:
        """
        Connect to broker API and validate credentials
        Returns: (success, error_message)
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from broker API"""
        pass
    
    # Market Data Methods
    @abstractmethod
    def get_historical_data(self, symbol: str, exchange: str, interval: str, 
                          start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get historical OHLCV data
        Args:
            symbol: Trading symbol
            exchange: Exchange code (NSE, BSE, etc.)
            interval: Timeframe (1m, 5m, 15m, 1h, 1D)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        pass
    
    @abstractmethod
    def get_quote(self, symbol: str, exchange: str) -> Dict:
        """
        Get real-time quote for symbol
        Returns: Dict with ltp, open, high, low, close, volume, etc.
        """
        pass
    
    @abstractmethod
    def get_market_depth(self, symbol: str, exchange: str) -> Dict:
        """
        Get market depth (order book) for symbol
        Returns: Dict with bids, asks arrays
        """
        pass
    
    # Order Management Methods
    @abstractmethod
    def place_order(self, order_request: OrderRequest) -> OrderResponse:
        """Place a new order"""
        pass
    
    @abstractmethod
    def modify_order(self, order_id: str, quantity: Optional[int] = None, 
                    price: Optional[float] = None) -> OrderResponse:
        """Modify existing order"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> OrderResponse:
        """Cancel existing order"""
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict:
        """Get status of specific order"""
        pass
    
    @abstractmethod
    def get_order_book(self) -> List[Dict]:
        """Get all orders for the day"""
        pass
    
    @abstractmethod
    def get_trade_book(self) -> List[Dict]:
        """Get all trades for the day"""
        pass
    
    # Portfolio Management Methods
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Get current positions"""
        pass
    
    @abstractmethod
    def get_holdings(self) -> List[Dict]:
        """Get long-term holdings"""
        pass
    
    @abstractmethod
    def get_margin_info(self) -> MarginInfo:
        """Get margin and fund information"""
        pass
    
    # Security Master Methods
    @abstractmethod
    def get_security_info(self, symbol: str, exchange: str) -> Optional[SecurityInfo]:
        """Get security information including token, lot size, etc."""
        pass
    
    @abstractmethod
    def search_instruments(self, query: str, exchange: Optional[str] = None) -> List[Dict]:
        """Search for instruments by name/symbol"""
        pass
    
    # Utility Methods
    def get_broker_name(self) -> str:
        """Return broker name"""
        return self.__class__.__name__.replace('Broker', '').upper()
    
    def validate_connection(self) -> bool:
        """Validate if connection is still active"""
        return self.is_connected
    
    def _map_timeframe(self, timeframe: str) -> str:
        """Map common timeframe to broker-specific format"""
        # Override in broker implementations
        return timeframe
    
    def _handle_api_error(self, response: Dict) -> Tuple[bool, str]:
        """Handle and parse API error responses"""
        # Override in broker implementations for specific error handling
        if 'error' in response:
            return False, response.get('error', 'Unknown error')
        return True, ""