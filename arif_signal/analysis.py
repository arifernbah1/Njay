# analysis.py

import logging
import sys

try:
    import numpy as np
except ImportError:
    print("❌ numpy is required. Please install: pip install numpy")
    sys.exit(1)
from typing import List, Optional, Tuple

# Import classes from other files
from models import CandleData, SignalType
from config import ConfigManager

# ========== TECHNICAL ANALYSIS ==========
class TechnicalAnalyzer:
    """Technical analysis calculations"""

    def __init__(self, logger: Optional['TradingLogger'] = None):
        self.logger = logger

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def find_support_resistance(self, candles: List[CandleData], lookback: int = 20) -> Tuple[List[float], List[float]]:
        """Find key support and resistance levels"""
        if len(candles) < lookback * 2:
            return [], []

        highs = [c.high for c in candles[-lookback*2:]]
        lows = [c.low for c in candles[-lookback*2:]]

        resistance_levels = []
        support_levels = []

        # Basic level finding logic
        for i in range(lookback, len(highs) - lookback):
            if highs[i] == max(highs[i-lookback:i+lookback+1]):
                resistance_levels.append(highs[i])

            if lows[i] == min(lows[i-lookback:i+lookback+1]):
                support_levels.append(lows[i])

        # Sorting and taking top N levels
        support_levels = sorted(list(set(support_levels)))[:5]
        resistance_levels = sorted(list(set(resistance_levels)), reverse=True)[:5]

        return (support_levels, resistance_levels)


# ========== PATTERN DETECTION ==========
class PatternDetector:
    """Pattern detection algorithms"""

    def __init__(self, analyzer: TechnicalAnalyzer, logger: Optional['TradingLogger'] = None):
        self.analyzer = analyzer
        self.logger = logger

    def detect_sweep(self, candles: List[CandleData], pair: str) -> Tuple[bool, Optional[str]]:
        """Advanced sweep detection"""
        if len(candles) < 20:
            if self.logger: self.logger.pattern_logger.debug(f"   🔍 {pair}: Sweep check failed - insufficient candles ({len(candles)})")
            return False, None

        current = candles[-1]
        config = ConfigManager.get_config(pair)

        # Volume validation
        recent_volumes = [c.volume for c in candles[-10:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes) if len(recent_volumes) > 0 else 0

        if avg_volume > 0 and current.volume <= avg_volume * config.volume_multiplier:
            if self.logger: self.logger.pattern_logger.debug(f"   🔍 {pair}: Sweep check failed - insufficient volume ({current.volume:.0f} vs avg {avg_volume:.0f} * {config.volume_multiplier})")
            return False, None

        # Get support/resistance levels
        support_levels, resistance_levels = self.analyzer.find_support_resistance(candles)

        if not support_levels and not resistance_levels:
            if self.logger: self.logger.pattern_logger.debug(f"   🔍 {pair}: Sweep check failed - no significant S/R levels found")
            return False, None

        # Higher timeframe trend
        htf_trend = self._get_higher_timeframe_trend(pair)
        if self.logger: self.logger.pattern_logger.debug("   🔍 {}: HTF Trend: {}".format(pair, htf_trend))

        # Check for bullish sweep
        for support in support_levels:
            tolerance = support * 0.0015

            if (current.low <= support - tolerance and
                current.close > support + tolerance and
                htf_trend in ["BULLISH", "NEUTRAL"]):

                closes = [c.close for c in candles[-14:]]
                rsi = self.analyzer.calculate_rsi(closes)

                if rsi < config.rsi_overbought:
                    if self.logger: self.logger.pattern_logger.debug("   🔍 {}: Bullish sweep conditions met near support {:.4f}".format(pair, support))
                    return True, SignalType.BULLISH
                else:
                    if self.logger: self.logger.pattern_logger.debug(f"   🔍 {pair}: Bullish sweep near support {support:.4f} failed RSI check ({rsi:.2f} not < {config.rsi_overbought})")

        # Check for bearish sweep
        for resistance in resistance_levels:
            tolerance = resistance * 0.0015

            if (current.high >= resistance + tolerance and
                current.close < resistance - tolerance and
                htf_trend in ["BEARISH", "NEUTRAL"]):

                closes = [c.close for c in candles[-14:]]
                rsi = self.analyzer.calculate_rsi(closes)

                if rsi > config.rsi_oversold:
                    if self.logger: self.logger.pattern_logger.debug("   🔍 {}: Bearish sweep conditions met near resistance {:.4f}".format(pair, resistance))
                    return True, SignalType.BEARISH
                else:
                    if self.logger: self.logger.pattern_logger.debug(f"   🔍 {pair}: Bearish sweep near resistance {resistance:.4f} failed RSI check ({rsi:.2f} not > {config.rsi_oversold})")

        if self.logger: self.logger.pattern_logger.debug(f"   🔍 {pair}: No sweep pattern detected after checks")
        return False, None

    def detect_engulfing(self, candles: List[CandleData], direction: str) -> bool:
        """Enhanced engulfing pattern detection"""
        if len(candles) < 3:
            if self.logger: self.logger.pattern_logger.debug(f"   🔍 Engulfing check failed - insufficient candles ({len(candles)})")
            return False

        c1, c2, c3 = candles[-3], candles[-2], candles[-1]

        # Basic engulfing pattern
        if direction == SignalType.BULLISH:
            basic_engulf = (c2.close < c2.open and c3.close > c3.open and
                           c3.close > c2.open and c3.open < c2.close)
        else:  # Bearish
            basic_engulf = (c2.close > c2.open and c3.close < c3.open and
                           c3.close < c2.open and c3.open > c2.close)

        if not basic_engulf:
            if self.logger: self.logger.pattern_logger.debug(f"   🔍 Engulfing check failed - basic pattern not found")
            return False

        # Volume and body size confirmation
        volume_confirmed = c2.volume > 0 and c3.volume > c2.volume * 1.2
        body_confirmed = c2.body_size > 0 and c3.body_size / c2.body_size >= 1.3

        if not volume_confirmed:
            if self.logger: self.logger.pattern_logger.debug(f"   🔍 Engulfing check failed - volume not confirmed (c3:{c3.volume:.0f} vs c2:{c2.volume:.0f} * 1.2)")

        if not body_confirmed:
            if self.logger: self.logger.pattern_logger.debug(f"   🔍 Engulfing check failed - body size not confirmed (c3:{c3.body_size:.4f} vs c2:{c2.body_size:.4f} * 1.3)")

        # Wick analysis
        if direction == SignalType.BULLISH:
            wick_confirmed = c3.lower_wick >= c3.body_size * 0.3
            if not wick_confirmed:
                if self.logger: self.logger.pattern_logger.debug(f"   🔍 Bullish Engulfing check failed - lower wick not confirmed (c3 lower wick:{c3.lower_wick:.4f} vs body size:{c3.body_size:.4f} * 0.3)")
        else:  # Bearish
            wick_confirmed = c3.upper_wick >= c3.body_size * 0.3
            if not wick_confirmed:
                if self.logger: self.logger.pattern_logger.debug(f"   🔍 Bearish Engulfing check failed - upper wick not confirmed (c3 upper wick:{c3.upper_wick:.4f} vs body size:{c3.body_size:.4f} * 0.3)")

        is_engulfing = basic_engulf and volume_confirmed and body_confirmed and wick_confirmed

        if is_engulfing:
            if self.logger: self.logger.pattern_logger.debug(f"   🔍 Engulfing check PASSED")

        return is_engulfing

    def _get_higher_timeframe_trend(self, pair: str) -> str:
        """Get higher timeframe trend - simplified version"""
        try:
            # This would use the exchange API in real implementation
            # For now, return NEUTRAL
            if self.logger: self.logger.pattern_logger.debug(f"   🔍 {pair}: Simulating higher timeframe trend check...")
            return "NEUTRAL"
        except Exception as e:
            # Log error if fetching HTF trend fails in a real scenario
            if self.logger: self.logger.log_error("PatternDetector", "Error fetching higher timeframe trend for {}: {}".format(pair, e), pair=pair)
            return "NEUTRAL"  # Return NEUTRAL on error