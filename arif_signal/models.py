"""
Arif Signal Trading Bot - Data Models
Definisi struktur data (CandleData, TradingConfig, SignalData, SignalType)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class SignalType(Enum):
    """Enum untuk tipe sinyal trading"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class CandleData:
    """Struktur data untuk candlestick"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str

@dataclass
class TradingConfig:
    """Konfigurasi trading bot"""
    api_key: str
    api_secret: str
    symbol: str
    timeframe: str
    risk_percentage: float
    max_position_size: float

@dataclass
class SignalData:
    """Data sinyal trading"""
    timestamp: datetime
    symbol: str
    signal_type: SignalType
    price: float
    strength: float
    pattern: str
    description: str