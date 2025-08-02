import pandas as pd
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List
from brokers.base import BaseBroker

class DhanBroker(BaseBroker):
    
    def __init__(self, client_id: str, access_token: str):
        super().__init__(client_id, access_token)
        self.base_url = "https://api.dhan.co"
        # Symbol mapping for indices
        self.symbol_map = {
            'NIFTY50': ('13', 'IDX_I', 'INDEX'),
            'NIFTY': ('13', 'IDX_I', 'INDEX'), 
            'BANKNIFTY': ('25', 'IDX_I', 'INDEX'),
            'FINNIFTY': ('27', 'IDX_I', 'INDEX'),
            'MIDCPNIFTY': ('28', 'IDX_I', 'INDEX'),
            'SENSEX': ('51', 'IDX_I', 'INDEX'),
            'BANKEX': ('54', 'IDX_I', 'INDEX')
        }
        
        # Timeframe mapping
        self.timeframe_map = {
            "1D": "D",
            "1m": "1", 
            "5m": "5",
            "15m": "15",
            "1h": "60"
        }
    
    def connect(self) -> bool:
        try:
            # Test connection by getting fund limits
            response = self._api_request("/v2/fundlimits", "POST")
            if response and response.get('status') == 'success':
                self.is_connected = True
                print(f"Connected to Dhan successfully for client: {self.client_id}")
                return True
            else:
                print(f"Failed to connect to Dhan: {response}")
                return False
        except Exception as e:
            print(f"Error connecting to Dhan: {e}")
            return False
    
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
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=payload)
            else:
                response = requests.request(method, url, headers=headers, json=payload)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return {"status": "error", "message": response.text}
                
        except Exception as e:
            print(f"Request error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_historical_data(self, symbol: str, from_date: datetime, to_date: datetime, timeframe: str = "1D") -> pd.DataFrame:
        if not self.is_connected:
            raise Exception("Not connected to broker")
        
        try:
            # Get symbol mapping
            if symbol.upper() in self.symbol_map:
                security_id, exchange_segment, instrument_type = self.symbol_map[symbol.upper()]
            else:
                # Default for equities
                security_id = symbol
                exchange_segment = "NSE_EQ"
                instrument_type = "EQUITY"
            
            # Choose endpoint based on timeframe
            if timeframe == "1D":
                endpoint = "/v2/charts/historical"
                payload = {
                    "securityId": security_id,
                    "exchangeSegment": exchange_segment,
                    "instrument": instrument_type,
                    "fromDate": from_date.strftime('%Y-%m-%d'),
                    "toDate": to_date.strftime('%Y-%m-%d'),
                    "oi": True
                }
                if instrument_type == 'EQUITY':
                    payload["expiryCode"] = 0
            else:
                endpoint = "/v2/charts/intraday"
                interval = self.timeframe_map.get(timeframe, "1")
                payload = {
                    "securityId": security_id,
                    "exchangeSegment": exchange_segment,
                    "instrument": instrument_type,
                    "interval": interval,
                    "fromDate": from_date.strftime('%Y-%m-%d'),
                    "toDate": to_date.strftime('%Y-%m-%d'),
                    "oi": True
                }
            
            print(f"Making request to {endpoint} with payload: {payload}")
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
                    # Convert timestamp (assuming it's in UTC, convert to datetime)
                    if timestamps[i]:
                        dt = datetime.utcfromtimestamp(timestamps[i]) + timedelta(hours=5, minutes=30)  # Convert to IST
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
                    return df
                else:
                    print("No data in response")
                    return pd.DataFrame()
            else:
                print(f"API error: {response}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error getting historical data: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_profile(self) -> Dict:
        if not self.is_connected:
            raise Exception("Not connected to broker")
        
        try:
            return self._api_request("/v2/fundlimits", "POST")
        except Exception as e:
            print(f"Error getting profile: {e}")
            return {}
    
    def place_order(self, symbol: str, quantity: int, price: float, order_type: str, side: str) -> Dict:
        if not self.is_connected:
            raise Exception("Not connected to broker")
        
        try:
            # Get security info
            if symbol.upper() in self.symbol_map:
                security_id, exchange_segment, instrument_type = self.symbol_map[symbol.upper()]
            else:
                security_id = symbol
                exchange_segment = "NSE_EQ"
                instrument_type = "EQUITY"
            
            transaction_type = "BUY" if side.upper() == 'BUY' else "SELL"
            
            payload = {
                "securityId": security_id,
                "exchangeSegment": exchange_segment,
                "transactionType": transaction_type,
                "quantity": quantity,
                "orderType": order_type.upper(),
                "productType": "INTRADAY",
                "price": price if order_type.upper() == 'LIMIT' else 0
            }
            
            response = self._api_request("/v2/orders", "POST", payload)
            return response
        except Exception as e:
            print(f"Error placing order: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_positions(self) -> List[Dict]:
        if not self.is_connected:
            raise Exception("Not connected to broker")
        
        try:
            response = self._api_request("/v2/positions", "POST")
            return response.get('data', []) if response.get('status') == 'success' else []
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []
    
    def get_orders(self) -> List[Dict]:
        if not self.is_connected:
            raise Exception("Not connected to broker")
        
        try:
            response = self._api_request("/v2/orders", "GET")
            return response.get('data', []) if response.get('status') == 'success' else []
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []