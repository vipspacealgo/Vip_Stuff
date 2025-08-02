import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from database.connection import db_manager
from database.models import Exchange, Instrument, InstrumentType, TimeFrame, OHLCV
from broker_manager.broker_factory import broker_factory
from broker_manager.base_broker import BaseBrokerInterface
from utils.logging import get_logger

logger = get_logger(__name__)

class UnifiedDataManager:
    """
    Unified data manager that works with any broker through the broker factory.
    Provides OpenAlgo-style abstraction for data operations.
    """
    
    def __init__(self):
        self.db = db_manager
        self._initialize_reference_data()
        self._current_broker: Optional[BaseBrokerInterface] = None
    
    def _initialize_reference_data(self):
        """Initialize reference data (exchanges, timeframes, etc.)"""
        session = self.db.get_session()
        try:
            # Initialize exchanges
            if session.query(Exchange).count() == 0:
                exchanges = [
                    Exchange(name="National Stock Exchange", code="NSE"),
                    Exchange(name="Bombay Stock Exchange", code="BSE"),
                    Exchange(name="NSE Indices", code="NSE_INDEX"),
                    Exchange(name="BSE Indices", code="BSE_INDEX")
                ]
                session.add_all(exchanges)
            
            # Initialize instrument types
            if session.query(InstrumentType).count() == 0:
                instrument_types = [
                    InstrumentType(name="EQUITY", code="EQ"),
                    InstrumentType(name="INDEX", code="IDX"),
                    InstrumentType(name="FUTURES", code="FUT"),
                    InstrumentType(name="OPTIONS", code="OPT")
                ]
                session.add_all(instrument_types)
            
            # Initialize timeframes
            if session.query(TimeFrame).count() == 0:
                timeframes = [
                    TimeFrame(name="1m", minutes=1),
                    TimeFrame(name="5m", minutes=5),
                    TimeFrame(name="15m", minutes=15),
                    TimeFrame(name="1h", minutes=60),
                    TimeFrame(name="1D", minutes=1440)
                ]
                session.add_all(timeframes)
            
            session.commit()
            logger.info("Reference data initialized successfully")
        except Exception as e:
            session.rollback()
            logger.error(f"Error initializing reference data: {e}")
        finally:
            session.close()
    
    def connect_broker(self, broker_name: str, client_id: str, access_token: str) -> bool:
        """
        Connect to a broker using the factory
        Args:
            broker_name: Name of broker (e.g., 'dhan')
            client_id: Client ID
            access_token: Access token
        Returns:
            True if connection successful
        """
        try:
            # Create broker instance
            broker = broker_factory.create_broker(broker_name, client_id, access_token)
            if not broker:
                logger.error(f"Failed to create {broker_name} broker instance")
                return False
            
            # Connect to broker
            success, error = broker.connect()
            if success:
                self._current_broker = broker
                logger.info(f"Connected to {broker_name} broker successfully")
                return True
            else:
                logger.error(f"Failed to connect to {broker_name}: {error}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to {broker_name} broker: {e}")
            return False
    
    def disconnect_broker(self):
        """Disconnect from current broker"""
        if self._current_broker:
            self._current_broker.disconnect()
            self._current_broker = None
            logger.info("Disconnected from broker")
    
    def add_instrument(self, exchange_code: str, symbol: str, token: str = None, lot_size: int = 1) -> bool:
        """Add instrument to database"""
        session = self.db.get_session()
        try:
            exchange = session.query(Exchange).filter_by(code=exchange_code).first()
            if not exchange:
                logger.error(f"Exchange {exchange_code} not found")
                return False
            
            existing = session.query(Instrument).filter_by(
                exchange_id=exchange.id, symbol=symbol
            ).first()
            
            if existing:
                logger.info(f"Instrument {symbol} already exists for {exchange_code}")
                return True
            
            instrument = Instrument(
                exchange_id=exchange.id,
                symbol=symbol,
                token=token,
                lot_size=lot_size
            )
            session.add(instrument)
            session.commit()
            logger.info(f"Added instrument: {symbol} for {exchange_code}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding instrument: {e}")
            return False
        finally:
            session.close()
    
    def download_and_store_data(self, exchange_code: str, symbol: str, 
                               timeframe: str, from_date: datetime, to_date: datetime) -> bool:
        """
        Download and store historical data using current broker
        Args:
            exchange_code: Exchange code (NSE, BSE, etc.)
            symbol: Trading symbol
            timeframe: Timeframe (1m, 5m, 15m, 1h, 1D)
            from_date: Start date
            to_date: End date
        Returns:
            True if successful
        """
        if not self._current_broker:
            logger.error("No broker connected")
            return False
        
        session = self.db.get_session()
        try:
            # Get database objects
            exchange = session.query(Exchange).filter_by(code=exchange_code).first()
            instrument = session.query(Instrument).filter_by(
                exchange_id=exchange.id, symbol=symbol
            ).first()
            timeframe_obj = session.query(TimeFrame).filter_by(name=timeframe).first()
            
            if not all([exchange, instrument, timeframe_obj]):
                logger.error("Exchange, instrument, or timeframe not found in database")
                return False
            
            # Download data from broker
            df = self._current_broker.get_historical_data(
                symbol=symbol,
                exchange=exchange_code,
                interval=timeframe,
                start_date=from_date.strftime('%Y-%m-%d'),
                end_date=to_date.strftime('%Y-%m-%d')
            )
            
            if df.empty:
                logger.warning("No data received from broker")
                return False
            
            # Check for existing data
            existing_data = session.query(OHLCV).filter(
                OHLCV.instrument_id == instrument.id,
                OHLCV.timeframe_id == timeframe_obj.id,
                OHLCV.timestamp >= from_date,
                OHLCV.timestamp <= to_date
            ).all()
            
            existing_timestamps = {record.timestamp for record in existing_data}
            
            # Prepare new records
            new_records = []
            for _, row in df.iterrows():
                if row['timestamp'] not in existing_timestamps:
                    ohlcv = OHLCV(
                        instrument_id=instrument.id,
                        timeframe_id=timeframe_obj.id,
                        timestamp=row['timestamp'],
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row['volume']
                    )
                    new_records.append(ohlcv)
            
            # Store new records
            if new_records:
                session.add_all(new_records)
                session.commit()
                logger.info(f"Stored {len(new_records)} new records for {symbol} {timeframe}")
            else:
                logger.info(f"No new data to store for {symbol} {timeframe}")
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error downloading and storing data: {e}")
            return False
        finally:
            session.close()
    
    def get_stored_data(self, exchange_code: str, symbol: str, timeframe: str, 
                       from_date: datetime, to_date: datetime) -> pd.DataFrame:
        """Get stored data from database"""
        session = self.db.get_session()
        try:
            exchange = session.query(Exchange).filter_by(code=exchange_code).first()
            instrument = session.query(Instrument).filter_by(
                exchange_id=exchange.id, symbol=symbol
            ).first()
            timeframe_obj = session.query(TimeFrame).filter_by(name=timeframe).first()
            
            if not all([exchange, instrument, timeframe_obj]):
                return pd.DataFrame()
            
            data = session.query(OHLCV).filter(
                OHLCV.instrument_id == instrument.id,
                OHLCV.timeframe_id == timeframe_obj.id,
                OHLCV.timestamp >= from_date,
                OHLCV.timestamp <= to_date
            ).order_by(OHLCV.timestamp).all()
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame([{
                'timestamp': record.timestamp,
                'open': record.open,
                'high': record.high,
                'low': record.low,
                'close': record.close,
                'volume': record.volume
            } for record in data])
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting stored data: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def get_available_instruments(self, exchange_code: str = None) -> List[Dict]:
        """Get list of available instruments"""
        session = self.db.get_session()
        try:
            query = session.query(Instrument, Exchange).select_from(Instrument).join(
                Exchange, Instrument.exchange_id == Exchange.id
            )
            if exchange_code:
                query = query.filter(Exchange.code == exchange_code)
            
            results = query.all()
            instruments = []
            for instrument, exchange in results:
                instruments.append({
                    'symbol': instrument.symbol,
                    'exchange': exchange.code,
                    'token': instrument.token,
                    'lot_size': instrument.lot_size
                })
            return instruments
        except Exception as e:
            logger.error(f"Error getting instruments: {e}")
            return []
        finally:
            session.close()
    
    def get_broker_info(self) -> Optional[Dict]:
        """Get current broker information"""
        if not self._current_broker:
            return None
        
        return {
            'name': self._current_broker.get_broker_name(),
            'connected': self._current_broker.is_connected,
            'client_id': self._current_broker.client_id
        }
    
    def get_available_brokers(self) -> List[str]:
        """Get list of available brokers"""
        return broker_factory.get_available_brokers()