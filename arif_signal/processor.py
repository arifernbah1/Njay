"""
Arif Signal Trading Bot - Signal Processor
Logika pemrosesan sinyal (SignalProcessor)
"""

from typing import List, Optional
from .models import CandleData, SignalData, SignalType
from .analysis import TechnicalAnalyzer, PatternDetector

class SignalProcessor:
    """Processor untuk memproses dan menghasilkan sinyal trading"""
    
    def __init__(self):
        self.analyzer = TechnicalAnalyzer()
        self.pattern_detector = PatternDetector()
        self.candles: List[CandleData] = []
        self.signals: List[SignalData] = []
    
    def add_candle(self, candle: CandleData) -> None:
        """Tambah candlestick baru dan analisis"""
        self.candles.append(candle)
        self.analyzer.add_candle(candle)
        
        # Analisis dan deteksi sinyal
        signal = self.analyze_candle(candle)
        if signal:
            self.signals.append(signal)
    
    def analyze_candle(self, candle: CandleData) -> Optional[SignalData]:
        """Analisis candlestick untuk menghasilkan sinyal"""
        signal_type = None
        pattern = ""
        strength = 0.0
        
        # Deteksi pola candlestick
        if self.pattern_detector.detect_doji(candle):
            pattern = "Doji"
            strength = 0.3
        elif self.pattern_detector.detect_hammer(candle):
            pattern = "Hammer"
            signal_type = SignalType.BUY
            strength = 0.7
        elif self.pattern_detector.detect_shooting_star(candle):
            pattern = "Shooting Star"
            signal_type = SignalType.SELL
            strength = 0.7
        
        # Deteksi pola engulfing
        if len(self.candles) >= 2:
            engulfing_signal = self.pattern_detector.detect_engulfing(self.candles[-2:])
            if engulfing_signal:
                signal_type = engulfing_signal
                pattern = "Engulfing"
                strength = 0.8
        
        # Analisis teknikal
        if len(self.candles) >= 20:
            sma_20 = self.analyzer.calculate_sma(20)
            sma_50 = self.analyzer.calculate_sma(50)
            
            if sma_20 and sma_50:
                if candle.close > sma_20 > sma_50:
                    if not signal_type:
                        signal_type = SignalType.BUY
                    strength = max(strength, 0.6)
                elif candle.close < sma_20 < sma_50:
                    if not signal_type:
                        signal_type = SignalType.SELL
                    strength = max(strength, 0.6)
        
        if signal_type and strength > 0.5:
            return SignalData(
                timestamp=candle.timestamp,
                symbol=candle.symbol,
                signal_type=signal_type,
                price=candle.close,
                strength=strength,
                pattern=pattern,
                description=f"{pattern} pattern detected with {strength:.2f} strength"
            )
        
        return None
    
    def get_recent_signals(self, count: int = 10) -> List[SignalData]:
        """Ambil sinyal terbaru"""
        return self.signals[-count:] if self.signals else []
    
    def get_signals_by_type(self, signal_type: SignalType) -> List[SignalData]:
        """Ambil sinyal berdasarkan tipe"""
        return [signal for signal in self.signals if signal.signal_type == signal_type]
    
    def clear_signals(self) -> None:
        """Bersihkan semua sinyal"""
        self.signals.clear()