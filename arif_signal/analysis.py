"""
Arif Signal Trading Bot - Technical Analysis
Analisis teknis dan deteksi pola (TechnicalAnalyzer, PatternDetector)
"""

from typing import List, Optional
from .models import CandleData, SignalData, SignalType

class TechnicalAnalyzer:
    """Analis teknikal untuk perhitungan indikator"""
    
    def __init__(self):
        self.candles: List[CandleData] = []
    
    def add_candle(self, candle: CandleData) -> None:
        """Tambah candlestick baru"""
        self.candles.append(candle)
    
    def calculate_sma(self, period: int) -> Optional[float]:
        """Hitung Simple Moving Average"""
        if len(self.candles) < period:
            return None
        
        recent_candles = self.candles[-period:]
        return sum(candle.close for candle in recent_candles) / period
    
    def calculate_ema(self, period: int) -> Optional[float]:
        """Hitung Exponential Moving Average"""
        if len(self.candles) < period:
            return None
        
        # TODO: Implement EMA calculation
        return None
    
    def calculate_rsi(self, period: int = 14) -> Optional[float]:
        """Hitung Relative Strength Index"""
        if len(self.candles) < period + 1:
            return None
        
        # TODO: Implement RSI calculation
        return None
    
    def calculate_bollinger_bands(self, period: int = 20, std_dev: float = 2.0):
        """Hitung Bollinger Bands"""
        if len(self.candles) < period:
            return None, None, None
        
        # TODO: Implement Bollinger Bands calculation
        return None, None, None

class PatternDetector:
    """Detektor pola candlestick"""
    
    def __init__(self):
        self.analyzer = TechnicalAnalyzer()
    
    def detect_doji(self, candle: CandleData) -> bool:
        """Deteksi pola Doji"""
        body_size = abs(candle.close - candle.open)
        total_range = candle.high - candle.low
        
        if total_range == 0:
            return False
        
        return body_size / total_range < 0.1
    
    def detect_hammer(self, candle: CandleData) -> bool:
        """Deteksi pola Hammer"""
        body_size = abs(candle.close - candle.open)
        lower_shadow = min(candle.open, candle.close) - candle.low
        upper_shadow = candle.high - max(candle.open, candle.close)
        
        return (lower_shadow > 2 * body_size and 
                upper_shadow < body_size)
    
    def detect_shooting_star(self, candle: CandleData) -> bool:
        """Deteksi pola Shooting Star"""
        body_size = abs(candle.close - candle.open)
        lower_shadow = min(candle.open, candle.close) - candle.low
        upper_shadow = candle.high - max(candle.open, candle.close)
        
        return (upper_shadow > 2 * body_size and 
                lower_shadow < body_size)
    
    def detect_engulfing(self, candles: List[CandleData]) -> Optional[SignalType]:
        """Deteksi pola Engulfing"""
        if len(candles) < 2:
            return None
        
        prev_candle = candles[-2]
        curr_candle = candles[-1]
        
        # Bullish Engulfing
        if (prev_candle.close < prev_candle.open and  # Previous bearish
            curr_candle.close > curr_candle.open and  # Current bullish
            curr_candle.open < prev_candle.close and  # Current opens below previous close
            curr_candle.close > prev_candle.open):    # Current closes above previous open
            return SignalType.BUY
        
        # Bearish Engulfing
        elif (prev_candle.close > prev_candle.open and  # Previous bullish
              curr_candle.close < curr_candle.open and  # Current bearish
              curr_candle.open > prev_candle.close and  # Current opens above previous close
              curr_candle.close < prev_candle.open):    # Current closes below previous open
            return SignalType.SELL
        
        return None