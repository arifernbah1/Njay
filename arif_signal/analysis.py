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
from trading_logger import TradingLogger

# ========== TECHNICAL ANALYSIS ==========
class TechnicalAnalyzer:
    """Technical analysis calculations"""
    # Add logger parameter
    def __init__(self, logger: Optional[TradingLogger] = None, exchange=None):
        self.logger = logger
        self.exchange = exchange  # Store exchange for multi-TF analysis

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            # Instead of returning 50.0, calculate with available data
            if len(prices) < 2:
                return 50.0  # Only if absolutely no data
            
            # Use available data with shorter period
            available_period = min(period, len(prices) - 1)
            if available_period < 2:
                return 50.0
            
            deltas = np.diff(prices[-available_period-1:])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            
            if avg_loss == 0:
                return 100.0
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))
        
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
            if self.logger: self.logger.pattern_logger.debug("   🔍 {}: Sweep check failed - insufficient candles ({})".format(pair, len(candles)))
            return False, None

        current = candles[-1]
        config = ConfigManager.get_config(pair)

        # Volume validation
        recent_volumes = [c.volume for c in candles[-10:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes) if len(recent_volumes) > 0 else 0

        if avg_volume > 0 and current.volume <= avg_volume * config.volume_multiplier:
            if self.logger: self.logger.pattern_logger.debug("   🔍 {}: Sweep check failed - insufficient volume ({:.0f} vs avg {:.0f} * {})".format(pair, current.volume, avg_volume, config.volume_multiplier))
            return False, None

        # Get support/resistance levels
        support_levels, resistance_levels = self.analyzer.find_support_resistance(candles)

        if not support_levels and not resistance_levels:
            if self.logger: self.logger.pattern_logger.debug("   🔍 {}: Sweep check failed - no significant S/R levels found".format(pair))
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
                    if self.logger: self.logger.pattern_logger.debug("   🔍 {}: Bullish sweep near support {:.4f} failed RSI check ({:.2f} not < {})".format(pair, support, rsi, config.rsi_overbought))

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
                    if self.logger: self.logger.pattern_logger.debug("   🔍 {}: Bearish sweep near resistance {:.4f} failed RSI check ({:.2f} not > {})".format(pair, resistance, rsi, config.rsi_oversold))

        if self.logger: self.logger.pattern_logger.debug("   🔍 {}: No sweep pattern detected after checks".format(pair))
        return False, None

    def detect_engulfing(self, candles: List[CandleData], direction: str) -> bool:
        """Enhanced engulfing pattern detection"""
        if len(candles) < 3:
            if self.logger: self.logger.pattern_logger.debug("   🔍 Engulfing check failed - insufficient candles ({})".format(len(candles)))
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
            if self.logger: self.logger.pattern_logger.debug("   🔍 Engulfing check failed - basic pattern not found")
            return False

        # Volume and body size confirmation
        volume_confirmed = c2.volume > 0 and c3.volume > c2.volume * 1.2
        body_confirmed = c2.body_size > 0 and c3.body_size / c2.body_size >= 1.3

        if not volume_confirmed:
            if self.logger: self.logger.pattern_logger.debug("   🔍 Engulfing check failed - volume not confirmed (c3:{:.0f} vs c2:{:.0f} * 1.2)".format(c3.volume, c2.volume))

        if not body_confirmed:
            if self.logger: self.logger.pattern_logger.debug("   🔍 Engulfing check failed - body size not confirmed (c3:{:.4f} vs c2:{:.4f} * 1.3)".format(c3.body_size, c2.body_size))

        # Wick analysis
        if direction == SignalType.BULLISH:
            wick_confirmed = c3.lower_wick >= c3.body_size * 0.3
            if not wick_confirmed:
                if self.logger: self.logger.pattern_logger.debug("   🔍 Bullish Engulfing check failed - lower wick not confirmed (c3 lower wick:{:.4f} vs body size:{:.4f} * 0.3)".format(c3.lower_wick, c3.body_size))
        else:  # Bearish
            wick_confirmed = c3.upper_wick >= c3.body_size * 0.3
            if not wick_confirmed:
                if self.logger: self.logger.pattern_logger.debug("   🔍 Bearish Engulfing check failed - upper wick not confirmed (c3 upper wick:{:.4f} vs body size:{:.4f} * 0.3)".format(c3.upper_wick, c3.body_size))

        is_engulfing = basic_engulf and volume_confirmed and body_confirmed and wick_confirmed

        if is_engulfing:
            if self.logger: self.logger.pattern_logger.debug("   🔍 Engulfing check PASSED")

        return is_engulfing

    def _get_higher_timeframe_trend(self, pair: str) -> str:
        """Get higher timeframe trend - real implementation"""
        try:
            # Get exchange from TechnicalAnalyzer
            if not hasattr(self.analyzer, 'exchange'):
                # Try to get exchange from data_manager if available
                if hasattr(self.analyzer, 'data_manager') and hasattr(self.analyzer.data_manager, 'exchange'):
                    exchange = self.analyzer.data_manager.exchange
                else:
                    if self.logger: self.logger.pattern_logger.debug("   🔍 {}: No exchange available, using NEUTRAL".format(pair))
                    return "NEUTRAL"
            else:
                exchange = self.analyzer.exchange
            
            if not exchange:
                if self.logger: self.logger.pattern_logger.debug("   🔍 {}: Exchange not initialized, using NEUTRAL".format(pair))
                return "NEUTRAL"
            
            # Convert pair format for ccxt
            ccxt_pair = pair.replace('USDT', '/USDT')
            
            # Fetch 1H data
            ohlcv_1h = exchange.fetch_ohlcv(ccxt_pair, '1h', limit=50)
            # Fetch 4H data  
            ohlcv_4h = exchange.fetch_ohlcv(ccxt_pair, '4h', limit=50)
            
            if len(ohlcv_1h) < 20 or len(ohlcv_4h) < 20:
                if self.logger: self.logger.pattern_logger.debug("   🔍 {}: Insufficient HTF data, using NEUTRAL".format(pair))
                return "NEUTRAL"
            
            # Calculate trends
            trend_1h = self._calculate_trend(ohlcv_1h)
            trend_4h = self._calculate_trend(ohlcv_4h)
            
            if self.logger: self.logger.pattern_logger.debug("   🔍 {}: HTF Trends - 1H: {}, 4H: {}".format(pair, trend_1h, trend_4h))
            
            # Combine analysis
            if trend_4h == "BULLISH" and trend_1h == "BULLISH":
                return "BULLISH"
            elif trend_4h == "BEARISH" and trend_1h == "BEARISH":
                return "BEARISH"
            else:
                return "NEUTRAL"
                
        except Exception as e:
            if self.logger: self.logger.log_error("PatternDetector", "Error fetching higher timeframe trend for {}: {}".format(pair, e), pair=pair)
            return "NEUTRAL"  # Return NEUTRAL on error
    
    def _calculate_trend(self, ohlcv_data):
        """Calculate trend from OHLCV data"""
        if len(ohlcv_data) < 20:
            return "NEUTRAL"
        
        closes = [float(candle[4]) for candle in ohlcv_data]
        
        # Simple trend calculation using SMA
        sma_20 = sum(closes[-20:]) / 20
        sma_10 = sum(closes[-10:]) / 10
        current_price = closes[-1]
        
        # Trend logic
        if current_price > sma_20 and sma_10 > sma_20:
            return "BULLISH"
        elif current_price < sma_20 and sma_10 < sma_20:
            return "BEARISH"
        else:
            return "NEUTRAL"