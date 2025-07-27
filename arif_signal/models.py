# models.py

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Tuple

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

# New Swing Trading Data Structures
@dataclass
class SwingIndicators:
    """Swing trading indicators for OTL strategy"""
    # Primary Trend Indicators
    ema_20: float
    ema_50: float
    ema_200: float
    macd_line: float
    macd_signal: float
    macd_histogram: float
    ichimoku_tenkan: float
    ichimoku_kijun: float
    ichimoku_senkou_a: float
    ichimoku_senkou_b: float
    parabolic_sar: float
    
    # Swing Oscillators
    weekly_rsi: float
    stochastic_k: float
    stochastic_d: float
    cci: float
    
    # Volume & Strength
    mfi: float
    volume_profile: Dict[str, float]  # Price levels -> Volume
    accumulation_distribution: float
    
    # Support/Resistance
    pivot_points: Dict[str, float]  # PP, R1, R2, R3, S1, S2, S3
    fibonacci_levels: Dict[str, float]  # 0.236, 0.382, 0.5, 0.618, 0.786
    swing_highs: List[float]
    swing_lows: List[float]
    supply_zones: List[Tuple[float, float]]  # (price, strength)
    demand_zones: List[Tuple[float, float]]  # (price, strength)

@dataclass
class OTLSignal:
    """OTL (Outside The Lines) signal for swing trading"""
    pair: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    strength: float
    risk_reward: float
    timestamp: datetime
    
    # OTL Specific Data
    breakout_level: float
    breakout_type: str  # "SUPPLY_BREAKOUT", "DEMAND_BREAKOUT", "FIBONACCI_BREAKOUT"
    trend_context: str  # "BULLISH_TREND", "BEARISH_TREND", "SIDEWAYS"
    volume_confirmation: bool
    momentum_confirmation: bool
    
    # Multi-timeframe confirmation
    daily_trend: str
    weekly_trend: str
    confirmation_timeframes: List[str]  # ["4H", "1H", "15M"]
    
    # Risk Management
    position_size: float  # Percentage of capital
    max_risk_per_trade: float  # Percentage of capital
    trailing_stop: bool
    partial_take_profit: List[float]  # Multiple TP levels

@dataclass
class SwingLevels:
    """Key swing trading levels"""
    support_levels: List[float]
    resistance_levels: List[float]
    breakout_levels: List[float]
    confluence_zones: List[Dict[str, any]]  # Multiple indicators agreeing
    invalidation_levels: List[float]  # Levels that invalidate the trade

class SwingTimeframe:
    """Swing trading timeframes"""
    WEEKLY = "1w"
    DAILY = "1d"
    FOUR_HOUR = "4h"
    ONE_HOUR = "1h"
    FIFTEEN_MIN = "15m"

class OTLBreakoutType:
    """OTL breakout types"""
    SUPPLY_BREAKOUT = "SUPPLY_BREAKOUT"
    DEMAND_BREAKOUT = "DEMAND_BREAKOUT"
    FIBONACCI_BREAKOUT = "FIBONACCI_BREAKOUT"
    PIVOT_BREAKOUT = "PIVOT_BREAKOUT"
    SWING_HIGH_BREAKOUT = "SWING_HIGH_BREAKOUT"
    SWING_LOW_BREAKOUT = "SWING_LOW_BREAKOUT"