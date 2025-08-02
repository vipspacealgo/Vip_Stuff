import pandas as pd
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from database.connection import db_manager
from database.models import Exchange, Instrument, InstrumentType, TimeFrame, OHLCV
from brokers.base import BaseBroker

class DataManager:
    
    def __init__(self):
        self.db = db_manager
        self._initialize_reference_data()
    
    def _initialize_reference_data(self):
        session = self.db.get_session()
        try:
            if session.query(Exchange).count() == 0:
                exchanges = [
                    Exchange(name="National Stock Exchange", code="NSE"),
                    Exchange(name="Bombay Stock Exchange", code="BSE")
                ]
                session.add_all(exchanges)
            
            if session.query(InstrumentType).count() == 0:
                instrument_types = [
                    InstrumentType(name="EQUITY", code="EQ"),
                    InstrumentType(name="FUTURES", code="FUT"),
                    InstrumentType(name="OPTIONS", code="OPT")
                ]
                session.add_all(instrument_types)
            
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
        except Exception as e:
            session.rollback()
            print(f"Error initializing reference data: {e}")
        finally:
            session.close()
    
    def add_instrument(self, exchange_code: str, symbol: str, token: str = None, lot_size: int = 1) -> bool:
        session = self.db.get_session()
        try:
            exchange = session.query(Exchange).filter_by(code=exchange_code).first()
            if not exchange:
                print(f"Exchange {exchange_code} not found")
                return False
            
            existing = session.query(Instrument).filter_by(
                exchange_id=exchange.id, symbol=symbol
            ).first()
            
            if existing:
                print(f"Instrument {symbol} already exists for {exchange_code}")
                return True
            
            instrument = Instrument(
                exchange_id=exchange.id,
                symbol=symbol,
                token=token,
                lot_size=lot_size
            )
            session.add(instrument)
            session.commit()
            print(f"Added instrument: {symbol} for {exchange_code}")
            return True
        except Exception as e:
            session.rollback()
            print(f"Error adding instrument: {e}")
            return False
        finally:
            session.close()
    
    def download_and_store_data(self, broker: BaseBroker, exchange_code: str, symbol: str, 
                               timeframe: str, from_date: datetime, to_date: datetime) -> bool:
        if not broker.is_connected:
            print("Broker not connected")
            return False
        
        session = self.db.get_session()
        try:
            exchange = session.query(Exchange).filter_by(code=exchange_code).first()
            instrument = session.query(Instrument).filter_by(
                exchange_id=exchange.id, symbol=symbol
            ).first()
            timeframe_obj = session.query(TimeFrame).filter_by(name=timeframe).first()
            
            if not all([exchange, instrument, timeframe_obj]):
                print("Exchange, instrument, or timeframe not found")
                return False
            
            df = broker.get_historical_data(symbol, from_date, to_date, timeframe)
            
            if df.empty:
                print("No data received from broker")
                return False
            
            existing_data = session.query(OHLCV).filter(
                OHLCV.instrument_id == instrument.id,
                OHLCV.timeframe_id == timeframe_obj.id,
                OHLCV.timestamp >= from_date,
                OHLCV.timestamp <= to_date
            ).all()
            
            existing_timestamps = {record.timestamp for record in existing_data}
            
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
            
            if new_records:
                session.add_all(new_records)
                session.commit()
                print(f"Stored {len(new_records)} new records for {symbol} {timeframe}")
            else:
                print(f"No new data to store for {symbol} {timeframe}")
            
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error downloading and storing data: {e}")
            return False
        finally:
            session.close()
    
    def get_stored_data(self, exchange_code: str, symbol: str, timeframe: str, 
                       from_date: datetime, to_date: datetime) -> pd.DataFrame:
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
            print(f"Error getting stored data: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def get_available_instruments(self, exchange_code: str = None) -> List[dict]:
        session = self.db.get_session()
        try:
            query = session.query(Instrument, Exchange).select_from(Instrument).join(Exchange, Instrument.exchange_id == Exchange.id)
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
            print(f"Error getting instruments: {e}")
            return []
        finally:
            session.close()