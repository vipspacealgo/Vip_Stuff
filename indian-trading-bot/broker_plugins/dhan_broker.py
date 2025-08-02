import pandas as pd
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from broker_manager.base_broker import (
    BaseBrokerInterface, SecurityInfo, OrderRequest, OrderResponse,
    Position, MarginInfo, OrderType, TransactionType, ProductType,
    ExchangeSegment, InstrumentType
)
from utils.logging import get_logger

logger = get_logger(__name__)

class DhanBroker(BaseBrokerInterface):
    """
    Dhan broker implementation following OpenAlgo-style architecture
    """
    
    def __init__(self, client_id: str, access_token: str, **kwargs):
        super().__init__(client_id, access_token)
        self.base_url = "https://api.dhan.co"
        
        # Symbol mapping for major indices
        self.symbol_master = {
            'NIFTY50': SecurityInfo('13', ExchangeSegment.IDX_I, InstrumentType.INDEX, 'NIFTY50'),
            'NIFTY': SecurityInfo('13', ExchangeSegment.IDX_I, InstrumentType.INDEX, 'NIFTY'),
            'BANKNIFTY': SecurityInfo('25', ExchangeSegment.IDX_I, InstrumentType.INDEX, 'BANKNIFTY'),
            'FINNIFTY': SecurityInfo('27', ExchangeSegment.IDX_I, InstrumentType.INDEX, 'FINNIFTY'),
            'MIDCPNIFTY': SecurityInfo('28', ExchangeSegment.IDX_I, InstrumentType.INDEX, 'MIDCPNIFTY'),
            'SENSEX': SecurityInfo('51', ExchangeSegment.IDX_I, InstrumentType.INDEX, 'SENSEX'),
            'BANKEX': SecurityInfo('54', ExchangeSegment.IDX_I, InstrumentType.INDEX, 'BANKEX')
        }
        
        # Timeframe mapping
        self.timeframe_map = {
            "1D": "D",
            "1m": "1", 
            "5m": "5",
            "15m": "15",
            "1h": "60"
        }
    
    def connect(self) -> Tuple[bool, Optional[str]]:
        """Connect and validate credentials"""
        try:
            response = self._api_request("/v2/fundlimit", "GET")
            if response and response.get('status') != 'error':
                self.is_connected = True
                logger.info(f"Connected to Dhan successfully for client: {self.client_id}")
                return True, None
            else:
                error_msg = response.get('message', 'Unknown error') if response else 'Connection failed'
                logger.error(f"Failed to connect to Dhan: {error_msg}")
                return False, error_msg
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error connecting to Dhan: {error_msg}")
            return False, error_msg
    
    def disconnect(self):
        """Disconnect from broker"""
        self.is_connected = False
        logger.info("Disconnected from Dhan")
    
    def _api_request(self, endpoint: str, method: str = "POST", payload: dict = None) -> dict:
        """Make API request to Dhan"""
        headers = {
            'access-token': self.access_token,
            'client-id': self.client_id,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        url = self.base_url + endpoint
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=payload, timeout=30)
            else:
                response = requests.request(method, url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API Error: {response.status_code} - {response.text}")
                return {"status": "error", "message": response.text}
                
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_historical_data(self, symbol: str, exchange: str, interval: str, 
                          start_date: str, end_date: str) -> pd.DataFrame:
        """Get historical OHLCV data"""
        if not self.is_connected:
            raise Exception("Not connected to broker")
        
        try:
            # Get security info
            security_info = self.get_security_info(symbol, exchange)
            if not security_info:
                logger.error(f"Security info not found for {symbol}")
                return pd.DataFrame()
            
            # Choose endpoint based on timeframe
            if interval == "1D":
                endpoint = "/v2/charts/historical"
                payload = {
                    "securityId": security_info.security_id,
                    "exchangeSegment": security_info.exchange_segment.value,
                    "instrument": security_info.instrument_type.value,
                    "fromDate": start_date,
                    "toDate": end_date,
                    "oi": True
                }
                if security_info.instrument_type == InstrumentType.EQUITY:
                    payload["expiryCode"] = 0
            else:
                endpoint = "/v2/charts/intraday"
                dhan_interval = self.timeframe_map.get(interval, "1")
                payload = {
                    "securityId": security_info.security_id,
                    "exchangeSegment": security_info.exchange_segment.value,
                    "instrument": security_info.instrument_type.value,
                    "interval": dhan_interval,
                    "fromDate": start_date,
                    "toDate": end_date,
                    "oi": True
                }
            
            logger.info(f"Requesting historical data: {endpoint} with payload: {payload}")
            response = self._api_request(endpoint, "POST", payload)
            
            if response and response.get('status') != 'error':
                # Extract data arrays
                timestamps = response.get('timestamp', [])
                opens = response.get('open', [])
                highs = response.get('high', [])
                lows = response.get('low', [])
                closes = response.get('close', [])
                volumes = response.get('volume', [])
                
                # Create list of candles
                candles = []
                for i in range(len(timestamps)):
                    if timestamps[i]:
                        # Convert timestamp from UTC to IST
                        dt = datetime.utcfromtimestamp(timestamps[i]) + timedelta(hours=5, minutes=30)
                        candles.append({
                            'timestamp': dt,
                            'open': float(opens[i]) if opens[i] else 0,
                            'high': float(highs[i]) if highs[i] else 0,
                            'low': float(lows[i]) if lows[i] else 0,
                            'close': float(closes[i]) if closes[i] else 0,
                            'volume': int(float(volumes[i])) if volumes[i] else 0
                        })
                
                # Create DataFrame
                if candles:
                    df = pd.DataFrame(candles)
                    df = df.sort_values('timestamp').reset_index(drop=True)
                    logger.info(f"Retrieved {len(df)} historical records for {symbol}")
                    return df
                else:
                    logger.warning("No data in response")
                    return pd.DataFrame()
            else:
                logger.error(f"API error: {response}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return pd.DataFrame()
    
    def get_quote(self, symbol: str, exchange: str) -> Dict:
        """Get real-time quote"""
        # Implementation for quotes - simplified for now
        return {"ltp": 0, "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0}
    
    def get_market_depth(self, symbol: str, exchange: str) -> Dict:
        """Get market depth"""
        # Implementation for market depth - simplified for now
        return {"bids": [], "asks": []}
    
    def place_order(self, order_request: OrderRequest) -> OrderResponse:
        """Place order"""
        # Implementation for order placement - simplified for now
        return OrderResponse(
            order_id=None,
            status="error",
            message="Order placement not implemented yet",
            timestamp=datetime.now()
        )
    
    def modify_order(self, order_id: str, quantity: Optional[int] = None, 
                    price: Optional[float] = None) -> OrderResponse:
        """Modify order"""
        return OrderResponse(
            order_id=order_id,
            status="error", 
            message="Order modification not implemented yet",
            timestamp=datetime.now()
        )
    
    def cancel_order(self, order_id: str) -> OrderResponse:
        """Cancel order"""
        return OrderResponse(
            order_id=order_id,
            status="error",
            message="Order cancellation not implemented yet", 
            timestamp=datetime.now()
        )
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get order status"""
        return {"status": "not_implemented"}
    
    def get_order_book(self) -> List[Dict]:
        """Get order book"""
        return []
    
    def get_trade_book(self) -> List[Dict]:
        """Get trade book"""
        return []
    
    def get_positions(self) -> List[Position]:
        """Get positions"""
        return []
    
    def get_holdings(self) -> List[Dict]:
        """Get holdings"""
        return []
    
    def get_margin_info(self) -> MarginInfo:
        """Get margin info"""
        try:
            response = self._api_request("/v2/fundlimit", "GET")
            if response and response.get('status') != 'error':
                return MarginInfo(
                    available_cash=float(response.get('availabelBalance', 0)),
                    used_margin=float(response.get('utilizedAmount', 0)),
                    collateral=float(response.get('collateralAmount', 0)),
                    total_margin=float(response.get('totalBalance', 0))
                )
        except Exception as e:
            logger.error(f"Error getting margin info: {e}")
        
        return MarginInfo(0, 0, 0, 0)
    
    def get_security_info(self, symbol: str, exchange: str) -> Optional[SecurityInfo]:
        """Get security information"""
        # Check symbol master first
        symbol_key = symbol.upper()
        if symbol_key in self.symbol_master:
            return self.symbol_master[symbol_key]
        
        # Default for equity stocks
        if exchange.upper() == "NSE":
            return SecurityInfo(
                security_id=symbol,
                exchange_segment=ExchangeSegment.NSE_EQ,
                instrument_type=InstrumentType.EQUITY,
                symbol=symbol
            )
        elif exchange.upper() == "BSE":
            return SecurityInfo(
                security_id=symbol,
                exchange_segment=ExchangeSegment.BSE_EQ,
                instrument_type=InstrumentType.EQUITY,
                symbol=symbol
            )
        
        return None
    
    def search_instruments(self, query: str, exchange: Optional[str] = None) -> List[Dict]:
        """Search instruments"""
        results = []
        for symbol, info in self.symbol_master.items():
            if query.upper() in symbol.upper():
                results.append({
                    'symbol': symbol,
                    'exchange': info.exchange_segment.value,
                    'instrument_type': info.instrument_type.value
                })
        return results

def register_broker(factory):
    """Register Dhan broker with the factory"""
    factory.register_broker('dhan', DhanBroker, {
        'name': 'Dhan',
        'description': 'Dhan Securities broker implementation',
        'supported_exchanges': ['NSE', 'BSE', 'IDX_I'],
        'supported_products': ['EQUITY', 'INDEX', 'F&O']
    })