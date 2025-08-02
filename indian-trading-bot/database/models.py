from sqlalchemy import Column, Integer, String, DateTime, Float, BigInteger, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Exchange(Base):
    __tablename__ = 'exchanges'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())

class Instrument(Base):
    __tablename__ = 'instruments'
    
    id = Column(Integer, primary_key=True)
    exchange_id = Column(Integer, nullable=False)
    symbol = Column(String(100), nullable=False)
    token = Column(String(50))
    lot_size = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_exchange_symbol', 'exchange_id', 'symbol'),
    )

class InstrumentType(Base):
    __tablename__ = 'instrument_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # EQUITY, FUTURES, OPTIONS
    code = Column(String(10), unique=True, nullable=False)

class TimeFrame(Base):
    __tablename__ = 'timeframes'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)  # 1m, 5m, 15m, 1h, 1d
    minutes = Column(Integer, nullable=False)  # Duration in minutes

class OHLCV(Base):
    __tablename__ = 'ohlcv_data'
    
    id = Column(BigInteger, primary_key=True)
    instrument_id = Column(Integer, nullable=False)
    timeframe_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_instrument_timeframe_timestamp', 'instrument_id', 'timeframe_id', 'timestamp'),
        Index('idx_timestamp', 'timestamp'),
    )