# SUBHA - Jesse to Indian Market Adaptation Plan
*Ultra Deep Technical Analysis & Implementation Roadmap*

## Executive Summary
**SUBHA** (शुभ - "Auspicious") - A comprehensive adaptation of Jesse framework for Indian equity markets with Zerodha integration. This document outlines the complete technical transformation required.

---

## 🎯 Core Architecture Transformation

### Current Jesse vs Required Subha

| Component | Jesse (Crypto) | Subha (Indian Equity) |
|-----------|----------------|----------------------|
| **Currency** | USD/BTC/ETH | INR (₹) |
| **Market Hours** | 24/7 | 9:15 AM - 3:30 PM IST |
| **Settlement** | T+0 | T+1/T+2 |
| **Market Type** | Spot/Futures | Equity/F&O/Commodity |
| **Data Provider** | Binance/Bybit | Zerodha/NSE/BSE |
| **Order Types** | Market/Limit/Stop | CNC/MIS/NRML |

---

## 🏗️ Deep Technical Implementation Requirements

### 1. **Core Data Layer Transformation**

#### Current Jesse Candle Structure:
```python
# jesse/models/Candle.py
[timestamp, open, close, high, low, volume]
```

#### Required Subha Extensions:
```python
# subha/models/Candle.py
[timestamp, open, close, high, low, volume, 
 delivery_qty, oi, turnover, segment, series]
```

#### Market Data Driver - Zerodha Integration:
```python
# subha/modes/import_candles_mode/drivers/Zerodha/ZerodhaEquity.py
class ZerodhaEquity(CandleExchange):
    def __init__(self):
        super().__init__(
            name="ZerodhaEquity",
            count=1000,  # Max historical data points
            rate_limit_per_second=1,  # Zerodha rate limits
            backup_exchange_class=None
        )
        self.kite = None  # KiteConnect instance
        
    def get_starting_time(self, symbol):
        # NSE/BSE specific logic for market debut dates
        return self._get_symbol_listing_date(symbol)
        
    def fetch(self, symbol, start_timestamp):
        # Transform symbol: RELIANCE -> NSE:RELIANCE
        # Handle different segments: EQ, BE, SM, etc.
        nse_symbol = self._transform_symbol(symbol)
        
        # Kite Connect API call
        data = self.kite.historical_data(
            instrument_token=self._get_instrument_token(nse_symbol),
            from_date=start_timestamp,
            to_date=arrow.now().format('YYYY-MM-DD'),
            interval=self._timeframe_to_kite_interval(self.timeframe)
        )
        
        return self._format_candles(data)
```

### 2. **Exchange Layer Complete Overhaul**

#### Zerodha Live Trading Exchange:
```python
# subha/exchanges/ZerodhaLive.py
class ZerodhaLive(Exchange):
    def __init__(self, name: str, starting_balance: float, fee_rate: float):
        super().__init__(name, starting_balance, fee_rate, "spot")
        self.kite = KiteConnect(api_key=self._get_api_key())
        self.settlement_currency = "INR"
        
    def market_order(self, symbol: str, qty: float, current_price: float, side: str, reduce_only: bool):
        # Transform to NSE format
        trading_symbol = self._get_trading_symbol(symbol)
        
        # Zerodha order placement
        order_id = self.kite.place_order(
            variety=self.kite.VARIETY_REGULAR,
            exchange=self._get_exchange(symbol),  # NSE/BSE
            tradingsymbol=trading_symbol,
            transaction_type=self.kite.TRANSACTION_TYPE_BUY if side == 'buy' else self.kite.TRANSACTION_TYPE_SELL,
            quantity=int(qty),  # Zerodha requires integer quantities
            product=self._get_product_type(),  # CNC/MIS/NRML
            order_type=self.kite.ORDER_TYPE_MARKET,
            price=None,
            validity=self.kite.VALIDITY_DAY,
            disclosed_quantity=None,
            trigger_price=None
        )
        
        return self._create_order_object(order_id, symbol, qty, current_price, side)
    
    def limit_order(self, symbol: str, qty: float, price: float, side: str, reduce_only: bool):
        # Similar implementation with ORDER_TYPE_LIMIT
        pass
        
    def _get_product_type(self):
        # Strategy-based product selection
        # CNC for delivery, MIS for intraday, NRML for F&O
        return self.kite.PRODUCT_CNC
```

### 3. **Currency & Portfolio Management**

#### INR-Based Portfolio System:
```python
# subha/models/Portfolio.py
class INRPortfolio:
    def __init__(self, starting_balance_inr: float):
        self.base_currency = "INR"
        self.balance = starting_balance_inr
        self.holdings = {}  # {symbol: {qty: int, avg_price: float}}
        self.margin_used = 0.0
        self.margin_available = starting_balance_inr
        
    def calculate_pnl(self, symbol: str, current_price: float):
        if symbol not in self.holdings:
            return 0.0
            
        holding = self.holdings[symbol]
        unrealized_pnl = (current_price - holding['avg_price']) * holding['qty']
        return unrealized_pnl
        
    def update_margin_requirements(self, symbol: str, qty: int):
        # Calculate margin based on SPAN + Exposure
        span_margin = self._calculate_span_margin(symbol, qty)
        exposure_margin = self._calculate_exposure_margin(symbol, qty)
        return span_margin + exposure_margin
```

### 4. **Time & Market Hours Management**

#### Indian Market Hours Handler:
```python
# subha/services/market_hours.py
class IndianMarketHours:
    def __init__(self):
        self.timezone = 'Asia/Kolkata'
        self.market_segments = {
            'equity': {'open': '09:15', 'close': '15:30'},
            'futures': {'open': '09:15', 'close': '15:30'},
            'commodity': {'open': '09:00', 'close': '23:30'}
        }
        
    def is_market_open(self, segment='equity'):
        ist_now = arrow.now(self.timezone)
        
        # Skip weekends
        if ist_now.weekday() in [5, 6]:  # Saturday, Sunday
            return False
            
        # Check market holidays
        if self._is_market_holiday(ist_now.date()):
            return False
            
        # Check segment timing
        market_hours = self.market_segments[segment]
        current_time = ist_now.format('HH:mm')
        
        return market_hours['open'] <= current_time <= market_hours['close']
        
    def next_market_open(self, segment='equity'):
        # Calculate next market opening time
        pass
        
    def _is_market_holiday(self, date):
        # NSE holiday calendar integration
        # Diwali, Holi, Independence Day, etc.
        return date in self._get_nse_holidays()
```

### 5. **Strategy Adaptations for Indian Market**

#### Indian Market Specific Indicators:
```python
# subha/indicators/indian_specific.py

def nifty_correlation(candles: np.ndarray, nifty_candles: np.ndarray, period: int = 20):
    """Calculate correlation with Nifty 50"""
    stock_returns = np.diff(candles[:, 2]) / candles[:-1, 2]  # close price returns
    nifty_returns = np.diff(nifty_candles[:, 2]) / nifty_candles[:-1, 2]
    
    return np.corrcoef(stock_returns[-period:], nifty_returns[-period:])[0, 1]

def sector_strength(symbol: str, sector_symbols: list, candles_dict: dict):
    """Calculate relative strength vs sector"""
    # Implementation for sector rotation strategies
    pass

def fno_pcr(symbol: str):
    """Put-Call Ratio for F&O stocks"""
    # Integration with NSE F&O data
    pass
```

#### Sample Indian Strategy:
```python
# subha/strategies/IndianMomentum.py
class IndianMomentum(Strategy):
    def should_long(self):
        # Check if market is open
        if not self.is_market_open():
            return False
            
        # Indian specific conditions
        rsi = ta.rsi(self.candles, 14)
        sma_20 = ta.sma(self.candles, 20)
        
        # Nifty correlation check
        nifty_correlation = self.get_nifty_correlation()
        
        # Volume surge detection
        avg_volume = ta.sma(self.candles[:, 5], 20)[-1]
        current_volume = self.candles[-1, 5]
        
        return (rsi[-1] > 60 and 
                self.price > sma_20[-1] and
                nifty_correlation > 0.7 and
                current_volume > avg_volume * 1.5)
    
    def go_long(self):
        # INR-based position sizing
        capital_per_trade = self.balance * 0.02  # 2% per trade
        qty = int(capital_per_trade / self.price)
        
        # Indian order types
        self.buy = qty, self.price  # Limit order
        self.stop_loss = qty, self.price * 0.95  # 5% stop loss
        self.take_profit = qty, self.price * 1.10  # 10% target
        
    def is_market_open(self):
        from subha.services.market_hours import IndianMarketHours
        return IndianMarketHours().is_market_open('equity')
        
    def get_nifty_correlation(self):
        # Access Nifty data and calculate correlation
        nifty_candles = selectors.get_candles('NSE', 'NIFTY50', self.timeframe)
        return nifty_correlation(self.candles, nifty_candles)
```

### 6. **Data Management & Storage**

#### Enhanced Database Schema:
```sql
-- subha/storage/schema.sql

-- Extended candles table for Indian market
CREATE TABLE IF NOT EXISTS candles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    open REAL NOT NULL,
    close REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    volume REAL NOT NULL,
    
    -- Indian market specific fields
    delivery_qty REAL DEFAULT 0,
    open_interest REAL DEFAULT 0,
    turnover REAL DEFAULT 0,
    segment TEXT DEFAULT 'EQ',
    series TEXT DEFAULT 'EQ',
    
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL
);

-- NSE symbols master
CREATE TABLE IF NOT EXISTS nse_symbols (
    instrument_token INTEGER PRIMARY KEY,
    exchange_token INTEGER,
    tradingsymbol TEXT NOT NULL,
    name TEXT,
    last_price REAL,
    expiry DATE,
    strike REAL,
    tick_size REAL,
    lot_size INTEGER,
    instrument_type TEXT,
    segment TEXT,
    exchange TEXT
);

-- Market holidays
CREATE TABLE IF NOT EXISTS market_holidays (
    date DATE PRIMARY KEY,
    description TEXT,
    segment TEXT DEFAULT 'equity'
);
```

### 7. **Configuration & Setup**

#### Subha Configuration Structure:
```python
# config.py
from subha.enums import environments, exchanges, timeframes

config = {
    'env': {
        'identifier': environments.PAPER_TRADING  # or LIVE_TRADING
    },
    
    'exchanges': {
        'Zerodha': {
            'balance': 1000000,  # 10 lakh INR
            'fee': 0.0003,  # 0.03% brokerage
            'type': 'spot',  # equity spot trading
            'settlement_currency': 'INR'
        }
    },
    
    'logging': {
        'order_submission': True,
        'order_cancellation': True,
        'order_execution': True,
        'position_update': True,
        'shorter_period': True
    },
    
    'Indian_Market': {
        'timezone': 'Asia/Kolkata',
        'default_segment': 'equity',
        'auto_square_off': True,  # MIS positions
        'auto_square_off_time': '15:20'  # Before market close
    }
}
```

### 8. **API Integration Layer**

#### Zerodha KiteConnect Wrapper:
```python
# subha/services/zerodha_api.py
class ZerodhaApiManager:
    def __init__(self):
        self.kite = None
        self.access_token = None
        self.api_key = os.getenv('ZERODHA_API_KEY')
        self.api_secret = os.getenv('ZERODHA_API_SECRET')
        
    def authenticate(self, request_token):
        """Complete OAuth flow and get access token"""
        kite = KiteConnect(api_key=self.api_key)
        data = kite.generate_session(request_token, api_secret=self.api_secret)
        self.access_token = data["access_token"]
        kite.set_access_token(self.access_token)
        self.kite = kite
        return True
        
    def get_instruments(self, exchange='NSE'):
        """Download and cache instrument master"""
        instruments = self.kite.instruments(exchange)
        self._cache_instruments(instruments)
        return instruments
        
    def get_positions(self):
        """Get current positions"""
        return self.kite.positions()
        
    def get_holdings(self):
        """Get long-term holdings"""
        return self.kite.holdings()
        
    def place_order(self, order_params):
        """Unified order placement"""
        return self.kite.place_order(**order_params)
```

### 9. **Risk Management Extensions**

#### Indian Market Risk Controls:
```python
# subha/services/risk_management.py
class IndianRiskManager:
    def __init__(self):
        self.max_positions = 10
        self.max_sector_exposure = 0.3  # 30% max in any sector
        self.max_single_stock = 0.1     # 10% max in any single stock
        self.circuit_limit_check = True
        
    def validate_order(self, symbol, qty, price, side):
        """Pre-order risk validation"""
        
        # Circuit limit check
        if self._is_circuit_limit_hit(symbol):
            raise exceptions.CircuitLimitHit(f"{symbol} hit circuit limit")
            
        # Position limit check
        if self._exceeds_position_limit(symbol, qty):
            raise exceptions.PositionLimitExceeded()
            
        # Sector exposure check
        if self._exceeds_sector_limit(symbol, qty, price):
            raise exceptions.SectorLimitExceeded()
            
        return True
        
    def _is_circuit_limit_hit(self, symbol):
        # Check NSE circuit breaker status
        # Upper/Lower circuit integration
        pass
        
    def calculate_margin_requirement(self, orders):
        """SPAN + Exposure margin calculation"""
        total_margin = 0
        
        for order in orders:
            if order.symbol.endswith('FUT') or order.symbol.endswith('CE') or order.symbol.endswith('PE'):
                # F&O margin calculation
                span_margin = self._calculate_span(order)
                exposure_margin = self._calculate_exposure(order)
                total_margin += span_margin + exposure_margin
            else:
                # Equity margin (for MIS)
                total_margin += order.qty * order.price * 0.2  # 20% margin for MIS
                
        return total_margin
```

---

## 🚀 Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
1. **Setup Subha Project Structure**
   - Fork Jesse codebase
   - Rename package structure
   - Update imports and dependencies

2. **Core Data Layer**
   - Implement ZerodhaEquity data driver
   - Extend Candle model for Indian fields
   - Database schema modifications

3. **Currency System**
   - Replace USD with INR throughout
   - Portfolio calculations in rupees
   - Indian number formatting (lakhs/crores)

### Phase 2: Market Integration (Weeks 5-8)
1. **Zerodha API Integration**
   - KiteConnect wrapper
   - Authentication flow
   - Instrument master download
   - Real-time data feeds

2. **Market Hours & Time Management**
   - IST timezone implementation
   - Market holiday calendar
   - Trading session controls

3. **Order Management System**
   - Indian order types (CNC/MIS/NRML)
   - Exchange routing (NSE/BSE)
   - Product type handling

### Phase 3: Advanced Features (Weeks 9-12)
1. **Indian-Specific Indicators**
   - Nifty correlation
   - Sector strength analysis
   - F&O indicators (PCR, OI analysis)

2. **Risk Management**
   - SPAN/Exposure margin calculations
   - Circuit breaker integration
   - Position and sector limits

3. **Strategy Templates**
   - Indian momentum strategies
   - Sector rotation
   - Index arbitrage

### Phase 4: Testing & Production (Weeks 13-16)
1. **Backtesting with Indian Data**
   - Historical NSE/BSE data
   - Holiday-adjusted backtests
   - Performance metrics in INR

2. **Paper Trading**
   - Zerodha sandbox integration
   - Real-time strategy testing
   - Order execution simulation

3. **Production Deployment**
   - Live trading infrastructure
   - Monitoring and alerting
   - Performance tracking

---

## 🔧 Technical Dependencies

### New Python Packages Required:
```bash
pip install kiteconnect           # Zerodha API
pip install pytz                  # Timezone handling
pip install pandas-market-calendars  # Market holidays
pip install NSEpy                 # NSE data backup
pip install yfinance              # Yahoo Finance backup
```

### Environment Variables:
```bash
export ZERODHA_API_KEY="your_api_key"
export ZERODHA_API_SECRET="your_secret"
export ZERODHA_ACCESS_TOKEN="your_token"
export SUBHA_ENV="paper_trading"  # or "live_trading"
```

---

## 📊 Success Metrics

### Technical KPIs:
- **Data Accuracy**: 99.9% match with NSE official data
- **Order Execution**: < 100ms average latency
- **System Uptime**: 99.5% during market hours
- **Backtest Speed**: Process 1 year data in < 5 minutes

### Trading KPIs:
- **Strategy Win Rate**: Track across different market conditions
- **Drawdown Control**: Max 15% portfolio drawdown
- **Risk Metrics**: Sharpe ratio > 1.5, Sortino ratio > 2.0
- **Transaction Costs**: Keep brokerage + impact < 0.1%

---

## 🚨 Critical Considerations

### Regulatory Compliance:
- SEBI guidelines adherence
- Tax calculation (STCG/LTCG)
- Audit trail maintenance
- Client fund segregation

### Technical Challenges:
- NSE data feed reliability
- Market closure handling
- Corporate actions (splits, bonuses)
- Settlement cycle management

### Operational Risks:
- API rate limiting
- Network connectivity
- Market volatility spikes
- System failover procedures

---

## 💡 Future Enhancements

### Advanced Features:
- **Multi-Asset Support**: Equity + F&O + Commodity
- **Portfolio Optimization**: Modern Portfolio Theory implementation
- **Alternative Data**: News sentiment, social media analysis
- **Machine Learning**: AI-powered strategy optimization

### Market Expansion:
- **Regional Exchanges**: BSE, MCX integration
- **Cross-Border**: Dubai, Singapore markets
- **Cryptocurrency**: Indian crypto exchanges

---

## 📝 Conclusion

Transforming Jesse into Subha requires comprehensive changes across every layer - from data ingestion to order execution. The modular architecture of Jesse makes this adaptation feasible, but requires careful attention to Indian market nuances.

**Key Success Factors:**
1. Robust Zerodha API integration
2. Accurate market hours and holiday handling
3. INR-based calculations throughout
4. Indian regulatory compliance
5. Comprehensive testing with historical data

The roadmap provides a systematic approach to building a world-class algorithmic trading platform specifically designed for Indian markets, combining Jesse's proven framework with India-specific requirements.

---

*Document Version: 1.0*  
*Last Updated: 2024*  
*Author: Subha Development Team*