from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

class BaseBroker(ABC):
    
    def __init__(self, client_id: str, access_token: str):
        self.client_id = client_id
        self.access_token = access_token
        self.is_connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, from_date: datetime, to_date: datetime, timeframe: str) -> pd.DataFrame:
        pass
    
    @abstractmethod
    def get_profile(self) -> Dict:
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, quantity: int, price: float, order_type: str, side: str) -> Dict:
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict]:
        pass
    
    @abstractmethod
    def get_orders(self) -> List[Dict]:
        pass
    
    def disconnect(self):
        self.is_connected = False