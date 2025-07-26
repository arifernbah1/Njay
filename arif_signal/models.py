# models.py

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple

@dataclass
class CandleData:
    """Immutable candle data structure"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)

    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low

@dataclass
class TradingConfig:
    """Trading configuration for each pair"""
    min_strength: float
    volume_multiplier: float
    rsi_oversold: int
    rsi_overbought: int
    min_risk_reward: float
    priority: int
    max_daily_signals: int

@dataclass
class SignalData:
    """Signal information structure"""
    pair: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    strength: float
    risk_reward: float
    timestamp: datetime

class SignalType:
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    BUY = "BUY"
    SELL = "SELL"