# analysis.py

import logging
import sys

try:
    import numpy as np
except ImportError:
    print("❌ numpy is required. Please install: pip install numpy")
    sys.exit(1)
from typing import List, Optional, Tuple, Dict

# Import classes from other files
from models import CandleData, SignalType
from config import ConfigManager
from trading_logger import TradingLogger

# ========== TECHNICAL ANALYSIS ==========
class TechnicalAnalyzer:
    """Technical analysis calculations with swing trading support"""
    # Add logger parameter
    def __init__(self, logger: Optional[TradingLogger] = None):
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

    # Swing Trading Indicators
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema

    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow + signal:
            return 0.0, 0.0, 0.0
        
        ema_fast = TechnicalAnalyzer.calculate_ema(prices, fast)
        ema_slow = TechnicalAnalyzer.calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line (EMA of MACD)
        macd_values = []
        for i in range(len(prices) - slow + 1):
            ema_f = TechnicalAnalyzer.calculate_ema(prices[i:i+slow], fast)
            ema_s = TechnicalAnalyzer.calculate_ema(prices[i:i+slow], slow)
            macd_values.append(ema_f - ema_s)
        
        signal_line = TechnicalAnalyzer.calculate_ema(macd_values, signal) if len(macd_values) >= signal else macd_line
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_ichimoku(candles: List[CandleData]) -> Tuple[float, float, float, float]:
        """Calculate Ichimoku Cloud components"""
        if len(candles) < 52:
            return 0.0, 0.0, 0.0, 0.0
        
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
        tenkan = (max(highs[-9:]) + min(lows[-9:])) / 2
        
        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        kijun = (max(highs[-26:]) + min(lows[-26:])) / 2
        
        # Senkou Span A (Leading Span A): (Tenkan + Kijun)/2
        senkou_a = (tenkan + kijun) / 2
        
        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
        senkou_b = (max(highs[-52:]) + min(lows[-52:])) / 2
        
        return tenkan, kijun, senkou_a, senkou_b

    @staticmethod
    def calculate_parabolic_sar(candles: List[CandleData], acceleration: float = 0.02, maximum: float = 0.2) -> float:
        """Calculate Parabolic SAR"""
        if len(candles) < 2:
            return candles[-1].close if candles else 0.0
        
        # Simplified Parabolic SAR calculation
        current = candles[-1]
        previous = candles[-2]
        
        # Determine trend
        if current.close > previous.close:
            # Uptrend
            sar = min(current.low, previous.low)
        else:
            # Downtrend
            sar = max(current.high, previous.high)
        
        return sar

    @staticmethod
    def calculate_stochastic(candles: List[CandleData], k_period: int = 14, d_period: int = 3) -> Tuple[float, float]:
        """Calculate Stochastic Oscillator"""
        if len(candles) < k_period:
            return 50.0, 50.0
        
        current = candles[-1]
        lookback = candles[-k_period:]
        
        highest_high = max([c.high for c in lookback])
        lowest_low = min([c.low for c in lookback])
        
        if highest_high == lowest_low:
            k_percent = 50.0
        else:
            k_percent = ((current.close - lowest_low) / (highest_high - lowest_low)) * 100
        
        # Calculate %D (SMA of %K)
        k_values = []
        for i in range(len(candles) - k_period + 1):
            candle = candles[i + k_period - 1]
            lookback_window = candles[i:i + k_period]
            hh = max([c.high for c in lookback_window])
            ll = min([c.low for c in lookback_window])
            if hh != ll:
                k_val = ((candle.close - ll) / (hh - ll)) * 100
            else:
                k_val = 50.0
            k_values.append(k_val)
        
        d_percent = sum(k_values[-d_period:]) / d_period if len(k_values) >= d_period else k_percent
        
        return k_percent, d_percent

    @staticmethod
    def calculate_cci(candles: List[CandleData], period: int = 20) -> float:
        """Calculate Commodity Channel Index"""
        if len(candles) < period:
            return 0.0
        
        typical_prices = [(c.high + c.low + c.close) / 3 for c in candles[-period:]]
        sma_tp = sum(typical_prices) / len(typical_prices)
        
        mean_deviation = sum([abs(tp - sma_tp) for tp in typical_prices]) / len(typical_prices)
        
        if mean_deviation == 0:
            return 0.0
        
        current_tp = (candles[-1].high + candles[-1].low + candles[-1].close) / 3
        cci = (current_tp - sma_tp) / (0.015 * mean_deviation)
        
        return cci

    @staticmethod
    def calculate_mfi(candles: List[CandleData], period: int = 14) -> float:
        """Calculate Money Flow Index"""
        if len(candles) < period + 1:
            return 50.0
        
        money_flows = []
        for i in range(1, len(candles)):
            current = candles[i]
            previous = candles[i-1]
            
            typical_price = (current.high + current.low + current.close) / 3
            prev_typical_price = (previous.high + previous.low + previous.close) / 3
            
            if typical_price > prev_typical_price:
                money_flow = typical_price * current.volume
                money_flows.append(('positive', money_flow))
            elif typical_price < prev_typical_price:
                money_flow = typical_price * current.volume
                money_flows.append(('negative', money_flow))
            else:
                money_flows.append(('neutral', 0))
        
        recent_flows = money_flows[-period:]
        positive_flow = sum([flow[1] for flow in recent_flows if flow[0] == 'positive'])
        negative_flow = sum([flow[1] for flow in recent_flows if flow[0] == 'negative'])
        
        if negative_flow == 0:
            return 100.0
        
        money_ratio = positive_flow / negative_flow
        mfi = 100 - (100 / (1 + money_ratio))
        
        return mfi

    @staticmethod
    def calculate_pivot_points(candles: List[CandleData]) -> Dict[str, float]:
        """Calculate Pivot Points"""
        if len(candles) < 1:
            return {}
        
        current = candles[-1]
        high = current.high
        low = current.low
        close = current.close
        
        pp = (high + low + close) / 3
        r1 = (2 * pp) - low
        r2 = pp + (high - low)
        r3 = high + 2 * (pp - low)
        s1 = (2 * pp) - high
        s2 = pp - (high - low)
        s3 = low - 2 * (high - pp)
        
        return {
            'PP': pp,
            'R1': r1,
            'R2': r2,
            'R3': r3,
            'S1': s1,
            'S2': s2,
            'S3': s3
        }

    @staticmethod
    def calculate_fibonacci_levels(high: float, low: float) -> Dict[str, float]:
        """Calculate Fibonacci Retracement Levels"""
        diff = high - low
        return {
            '0.0': low,
            '0.236': low + 0.236 * diff,
            '0.382': low + 0.382 * diff,
            '0.5': low + 0.5 * diff,
            '0.618': low + 0.618 * diff,
            '0.786': low + 0.786 * diff,
            '1.0': high
        }

    @staticmethod
    def find_swing_levels(candles: List[CandleData], lookback: int = 20) -> Tuple[List[float], List[float]]:
        """Find swing highs and lows"""
        if len(candles) < lookback * 2:
            return [], []
        
        highs = [c.high for c in candles[-lookback*2:]]
        lows = [c.low for c in candles[-lookback*2:]]
        
        swing_highs = []
        swing_lows = []
        
        for i in range(lookback, len(highs) - lookback):
            if highs[i] == max(highs[i-lookback:i+lookback+1]):
                swing_highs.append(highs[i])
            if lows[i] == min(lows[i-lookback:i+lookback+1]):
                swing_lows.append(lows[i])
        
        return swing_highs, swing_lows

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
    """Pattern detection algorithms with swing trading OTL support"""
    # Add logger parameter
    def __init__(self, analyzer: TechnicalAnalyzer, logger: Optional[TradingLogger] = None):
        self.analyzer = analyzer
        self.logger = logger # Store logger

    # Modified to use logger
    def detect_sweep(self, candles: List[CandleData], pair: str, mode: str = "SCALPING") -> Tuple[bool, Optional[str]]:
        """Advanced sweep detection with mode-specific analysis"""
        if len(candles) < 20:
            if self.logger:
                self.logger.pattern_logger.debug("   🔍 {}: Sweep check failed - insufficient candles ({})".format(pair, len(candles)))
            return False, None
        
        current = candles[-1]
        config = ConfigManager.get_config(pair)
        
        # Mode-specific technical analysis
        if mode == "SCALPING":
            ta_data = self.analyze_scalping_15m(candles, pair)
        else:  # SWING mode
            ta_data = self.analyze_swing_1h(candles, pair)
        
        # Volume validation
        if mode == "SCALPING":
            volume_ratio = ta_data.get('volume_ratio', 1)
            if volume_ratio <= config.volume_multiplier:
                if self.logger:
                    self.logger.pattern_logger.debug("   🔍 {}: Sweep check failed - insufficient volume (ratio: {:.2f})".format(pair, volume_ratio))
                return False, None
        else:  # SWING mode
            mfi = ta_data.get('volume_analysis', {}).get('mfi', 50)
            if mfi < 50:  # Low money flow
                if self.logger:
                    self.logger.pattern_logger.debug("   🔍 {}: Sweep check failed - low MFI ({:.2f})".format(pair, mfi))
                return False, None
        
        # Get support/resistance levels
        if mode == "SCALPING":
            support_levels = ta_data.get('support_levels', [])
            resistance_levels = ta_data.get('resistance_levels', [])
        else:  # SWING mode
            support_levels = ta_data.get('levels', {}).get('swing_lows', [])
            resistance_levels = ta_data.get('levels', {}).get('swing_highs', [])
        
        if not support_levels and not resistance_levels:
            if self.logger:
                self.logger.pattern_logger.debug("   🔍 {}: Sweep check failed - no significant S/R levels found".format(pair))
            return False, None
        
        # Higher timeframe trend
        htf_trend = self._get_higher_timeframe_trend(pair)
        if self.logger:
            self.logger.pattern_logger.debug("   🔍 {}: HTF Trend: {}".format(pair, htf_trend))
        
        # Check for bullish sweep
        for support in support_levels:
            tolerance = support * 0.0015
            if (current.low <= support - tolerance and current.close > support + tolerance and htf_trend in ["BULLISH", "NEUTRAL"]):
                # Mode-specific RSI check
                if mode == "SCALPING":
                    rsi = ta_data.get('rsi', 50)
                    if rsi < config.rsi_overbought:
                        if self.logger:
                            self.logger.pattern_logger.debug("   🔍 {}: Bullish sweep conditions met near support {:.4f}".format(pair, support))
                        return True, SignalType.BULLISH
                else:  # SWING mode
                    weekly_rsi = ta_data.get('oscillators', {}).get('weekly_rsi', 50)
                    if weekly_rsi < 70:  # Not overbought
                        if self.logger:
                            self.logger.pattern_logger.debug("   🔍 {}: Bullish sweep conditions met near support {:.4f}".format(pair, support))
                        return True, SignalType.BULLISH
        
        # Check for bearish sweep
        for resistance in resistance_levels:
            tolerance = resistance * 0.0015
            if (current.high >= resistance + tolerance and current.close < resistance - tolerance and htf_trend in ["BEARISH", "NEUTRAL"]):
                # Mode-specific RSI check
                if mode == "SCALPING":
                    rsi = ta_data.get('rsi', 50)
                    if rsi > config.rsi_oversold:
                        if self.logger:
                            self.logger.pattern_logger.debug("   🔍 {}: Bearish sweep conditions met near resistance {:.4f}".format(pair, resistance))
                        return True, SignalType.BEARISH
                else:  # SWING mode
                    weekly_rsi = ta_data.get('oscillators', {}).get('weekly_rsi', 50)
                    if weekly_rsi > 30:  # Not oversold
                        if self.logger:
                            self.logger.pattern_logger.debug("   🔍 {}: Bearish sweep conditions met near resistance {:.4f}".format(pair, resistance))
                        return True, SignalType.BEARISH
        
        if self.logger:
            self.logger.pattern_logger.debug("   🔍 {}: No sweep pattern detected after checks".format(pair))
        return False, None

    # Modified to use logger
    def detect_engulfing(self, candles: List[CandleData], direction: str) -> bool:
        """Enhanced engulfing pattern detection"""
        if len(candles) < 3:
            if self.logger:
                self.logger.pattern_logger.debug("   🔍 Engulfing check failed - insufficient candles ({})".format(len(candles)))
            return False
        c1, c2, c3 = candles[-3], candles[-2], candles[-1]
        # Basic engulfing pattern
        if direction == SignalType.BULLISH:
            basic_engulf = (c2.close < c2.open and c3.close > c3.open and c3.close > c2.open and c3.open < c2.close)
        else:  # Bearish
            basic_engulf = (c2.close > c2.open and c3.close < c3.open and c3.close < c2.open and c3.open > c2.close)
        if not basic_engulf:
            if self.logger:
                self.logger.pattern_logger.debug("   🔍 Engulfing check failed - basic pattern not found")
            return False
        # Volume and body size confirmation
        volume_confirmed = c2.volume > 0 and c3.volume > c2.volume * 1.2
        body_confirmed = c2.body_size > 0 and c3.body_size / c2.body_size >= 1.3
        if not volume_confirmed:
            if self.logger:
                self.logger.pattern_logger.debug("   🔍 Engulfing check failed - volume not confirmed (c3:{:.0f} vs c2:{:.0f} * 1.2)".format(c3.volume, c2.volume))
        if not body_confirmed:
            if self.logger:
                self.logger.pattern_logger.debug("   🔍 Engulfing check failed - body size not confirmed (c3:{:.4f} vs c2:{:.4f} * 1.3)".format(c3.body_size, c2.body_size))
        # Wick analysis
        if direction == SignalType.BULLISH:
            wick_confirmed = c3.lower_wick >= c3.body_size * 0.3
            if not wick_confirmed:
                if self.logger:
                    self.logger.pattern_logger.debug("   🔍 Bullish Engulfing check failed - lower wick not confirmed (c3 lower wick:{:.4f} vs body size:{:.4f} * 0.3)".format(c3.lower_wick, c3.body_size))
        else:  # Bearish
            wick_confirmed = c3.upper_wick >= c3.body_size * 0.3
            if not wick_confirmed:
                if self.logger:
                    self.logger.pattern_logger.debug("   🔍 Bearish Engulfing check failed - upper wick not confirmed (c3 upper wick:{:.4f} vs body size:{:.4f} * 0.3)".format(c3.upper_wick, c3.body_size))
        is_engulfing = basic_engulf and volume_confirmed and body_confirmed and wick_confirmed
        if is_engulfing:
            if self.logger:
                self.logger.pattern_logger.debug("   🔍 Engulfing check PASSED")
        return is_engulfing

    # Swing Trading OTL Pattern Detection
    def detect_otl_breakout(self, candles: List[CandleData], pair: str) -> Tuple[bool, Optional[str], Dict]:
        """Detect OTL (Outside The Lines) breakout patterns for swing trading"""
        if len(candles) < 50:
            if self.logger:
                self.logger.pattern_logger.debug("   🔍 {}: OTL check failed - insufficient candles ({})".format(pair, len(candles)))
            return False, None, {}
        
        current = candles[-1]
        closes = [c.close for c in candles]
        
        # Calculate swing indicators
        swing_indicators = self._calculate_swing_indicators(candles)
        
        # Find key levels
        swing_highs, swing_lows = self.analyzer.find_swing_levels(candles)
        pivot_points = self.analyzer.calculate_pivot_points(candles)
        
        # Determine trend context
        trend_context = self._determine_trend_context(swing_indicators, closes)
        
        # Check for bullish OTL breakout
        if trend_context in ["BULLISH_TREND", "SIDEWAYS"]:
            # Check resistance breakouts
            for resistance in swing_highs + [pivot_points.get('R1', 0), pivot_points.get('R2', 0)]:
                if resistance > 0 and current.close > resistance * 1.001:  # 0.1% breakout
                    # Volume confirmation
                    volume_confirmed = current.volume > sum([c.volume for c in candles[-10:]]) / 10 * 1.5
                    
                    # Momentum confirmation
                    momentum_confirmed = (
                        swing_indicators['macd_line'] > swing_indicators['macd_signal'] and
                        swing_indicators['weekly_rsi'] < 70 and
                        swing_indicators['stochastic_k'] > swing_indicators['stochastic_d']
                    )
                    
                    if volume_confirmed and momentum_confirmed:
                        breakout_data = {
                            'breakout_level': resistance,
                            'breakout_type': 'SWING_HIGH_BREAKOUT',
                            'trend_context': trend_context,
                            'volume_confirmation': volume_confirmed,
                            'momentum_confirmation': momentum_confirmed,
                            'indicators': swing_indicators
                        }
                        
                        if self.logger:
                            self.logger.pattern_logger.debug("   🔍 {}: Bullish OTL breakout detected at {:.4f}".format(pair, resistance))
                        
                        return True, SignalType.BULLISH, breakout_data
        
        # Check for bearish OTL breakout
        if trend_context in ["BEARISH_TREND", "SIDEWAYS"]:
            # Check support breakouts
            for support in swing_lows + [pivot_points.get('S1', 0), pivot_points.get('S2', 0)]:
                if support > 0 and current.close < support * 0.999:  # 0.1% breakdown
                    # Volume confirmation
                    volume_confirmed = current.volume > sum([c.volume for c in candles[-10:]]) / 10 * 1.5
                    
                    # Momentum confirmation
                    momentum_confirmed = (
                        swing_indicators['macd_line'] < swing_indicators['macd_signal'] and
                        swing_indicators['weekly_rsi'] > 30 and
                        swing_indicators['stochastic_k'] < swing_indicators['stochastic_d']
                    )
                    
                    if volume_confirmed and momentum_confirmed:
                        breakout_data = {
                            'breakout_level': support,
                            'breakout_type': 'SWING_LOW_BREAKOUT',
                            'trend_context': trend_context,
                            'volume_confirmation': volume_confirmed,
                            'momentum_confirmation': momentum_confirmed,
                            'indicators': swing_indicators
                        }
                        
                        if self.logger:
                            self.logger.pattern_logger.debug("   🔍 {}: Bearish OTL breakout detected at {:.4f}".format(pair, support))
                        
                        return True, SignalType.BEARISH, breakout_data
        
        if self.logger:
            self.logger.pattern_logger.debug("   🔍 {}: No OTL breakout detected".format(pair))
        
        return False, None, {}

    def _calculate_swing_indicators(self, candles: List[CandleData]) -> Dict:
        """Calculate all swing trading indicators"""
        closes = [c.close for c in candles]
        
        # Primary Trend Indicators
        ema_20 = self.analyzer.calculate_ema(closes, 20)
        ema_50 = self.analyzer.calculate_ema(closes, 50)
        ema_200 = self.analyzer.calculate_ema(closes, 200)
        macd_line, macd_signal, macd_histogram = self.analyzer.calculate_macd(closes)
        tenkan, kijun, senkou_a, senkou_b = self.analyzer.calculate_ichimoku(candles)
        parabolic_sar = self.analyzer.calculate_parabolic_sar(candles)
        
        # Swing Oscillators
        weekly_rsi = self.analyzer.calculate_rsi(closes, 14)  # Using 14-period as weekly proxy
        stochastic_k, stochastic_d = self.analyzer.calculate_stochastic(candles)
        cci = self.analyzer.calculate_cci(candles)
        
        # Volume & Strength
        mfi = self.analyzer.calculate_mfi(candles)
        
        return {
            'ema_20': ema_20,
            'ema_50': ema_50,
            'ema_200': ema_200,
            'macd_line': macd_line,
            'macd_signal': macd_signal,
            'macd_histogram': macd_histogram,
            'ichimoku_tenkan': tenkan,
            'ichimoku_kijun': kijun,
            'ichimoku_senkou_a': senkou_a,
            'ichimoku_senkou_b': senkou_b,
            'parabolic_sar': parabolic_sar,
            'weekly_rsi': weekly_rsi,
            'stochastic_k': stochastic_k,
            'stochastic_d': stochastic_d,
            'cci': cci,
            'mfi': mfi
        }

    def _determine_trend_context(self, indicators: Dict, closes: List[float]) -> str:
        """Determine overall trend context based on multiple indicators"""
        current_price = closes[-1]
        
        # EMA trend analysis
        ema_bullish = current_price > indicators['ema_20'] > indicators['ema_50'] > indicators['ema_200']
        ema_bearish = current_price < indicators['ema_20'] < indicators['ema_50'] < indicators['ema_200']
        
        # MACD trend analysis
        macd_bullish = indicators['macd_line'] > indicators['macd_signal'] and indicators['macd_histogram'] > 0
        macd_bearish = indicators['macd_line'] < indicators['macd_signal'] and indicators['macd_histogram'] < 0
        
        # Ichimoku trend analysis
        ichimoku_bullish = (
            indicators['ichimoku_tenkan'] > indicators['ichimoku_kijun'] and
            current_price > indicators['ichimoku_senkou_a'] and
            indicators['ichimoku_senkou_a'] > indicators['ichimoku_senkou_b']
        )
        ichimoku_bearish = (
            indicators['ichimoku_tenkan'] < indicators['ichimoku_kijun'] and
            current_price < indicators['ichimoku_senkou_a'] and
            indicators['ichimoku_senkou_a'] < indicators['ichimoku_senkou_b']
        )
        
        # Count bullish and bearish signals
        bullish_signals = sum([ema_bullish, macd_bullish, ichimoku_bullish])
        bearish_signals = sum([ema_bearish, macd_bearish, ichimoku_bearish])
        
        if bullish_signals >= 2:
            return "BULLISH_TREND"
        elif bearish_signals >= 2:
            return "BEARISH_TREND"
        else:
            return "SIDEWAYS"

    def _get_higher_timeframe_trend(self, pair: str) -> str:
        """Get higher timeframe trend - simplified version"""
        try:
            # This would use the exchange API in real implementation
            # For refactor demo, return NEUTRAL
            # Add logging for this simulation
            if self.logger:
                self.logger.pattern_logger.debug("   🔍 {}: Simulating higher timeframe trend check...".format(pair))
            return "NEUTRAL"
        except Exception as e:
            # Log error if fetching HTF trend fails in a real scenario
            if self.logger:
                self.logger.log_error("PatternDetector", "Error fetching higher timeframe trend for {}: {}".format(pair, e), pair=pair)
            return "NEUTRAL"  # Return NEUTRAL on error

    # Mode-Specific Technical Analysis
    def analyze_scalping_15m(self, candles: List[CandleData], pair: str) -> Dict:
        """Technical analysis specifically for Scalping 15m mode"""
        if len(candles) < 20:
            return {}
        
        closes = [c.close for c in candles]
        current = candles[-1]
        
        # 1. Simple RSI Analysis
        rsi = self.analyzer.calculate_rsi(closes, 14)
        
        # 2. Volume Analysis
        recent_volumes = [c.volume for c in candles[-10:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
        volume_ratio = current.volume / avg_volume if avg_volume > 0 else 1
        
        # 3. Basic Support/Resistance
        support_levels, resistance_levels = self.analyzer.find_support_resistance(candles, lookback=15)
        
        # 4. Simple Trend Analysis
        sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1]
        trend = "BULLISH" if current.close > sma_20 else "BEARISH"
        
        return {
            'rsi': rsi,
            'volume_ratio': volume_ratio,
            'support_levels': support_levels,
            'resistance_levels': resistance_levels,
            'trend': trend,
            'sma_20': sma_20,
            'current_price': current.close
        }

    def analyze_swing_1h(self, candles: List[CandleData], pair: str) -> Dict:
        """Technical analysis specifically for Swing 1h mode"""
        if len(candles) < 50:
            return {}
        
        closes = [c.close for c in candles]
        current = candles[-1]
        
        # 1. Multi-EMA Trend Analysis
        ema_20 = self.analyzer.calculate_ema(closes, 20)
        ema_50 = self.analyzer.calculate_ema(closes, 50)
        ema_200 = self.analyzer.calculate_ema(closes, 200)
        
        # 2. MACD Analysis
        macd_line, macd_signal, macd_histogram = self.analyzer.calculate_macd(closes)
        
        # 3. Ichimoku Cloud
        tenkan, kijun, senkou_a, senkou_b = self.analyzer.calculate_ichimoku(candles)
        
        # 4. Advanced Oscillators
        weekly_rsi = self.analyzer.calculate_rsi(closes, 14)  # Weekly proxy
        stochastic_k, stochastic_d = self.analyzer.calculate_stochastic(candles)
        cci = self.analyzer.calculate_cci(candles)
        
        # 5. Volume Analysis
        mfi = self.analyzer.calculate_mfi(candles)
        
        # 6. Advanced Support/Resistance
        pivot_points = self.analyzer.calculate_pivot_points(candles)
        swing_highs, swing_lows = self.analyzer.find_swing_levels(candles)
        
        # 7. Trend Context Analysis
        trend_context = self._determine_comprehensive_trend(
            ema_20, ema_50, ema_200, macd_line, macd_signal, 
            tenkan, kijun, current.close
        )
        
        return {
            'ema_analysis': {
                'ema_20': ema_20,
                'ema_50': ema_50,
                'ema_200': ema_200,
                'trend_alignment': self._analyze_ema_trend(ema_20, ema_50, ema_200, current.close)
            },
            'macd_analysis': {
                'macd_line': macd_line,
                'macd_signal': macd_signal,
                'macd_histogram': macd_histogram,
                'macd_bullish': macd_line > macd_signal and macd_histogram > 0
            },
            'ichimoku_analysis': {
                'tenkan': tenkan,
                'kijun': kijun,
                'senkou_a': senkou_a,
                'senkou_b': senkou_b,
                'cloud_bullish': senkou_a > senkou_b and current.close > senkou_a
            },
            'oscillators': {
                'weekly_rsi': weekly_rsi,
                'stochastic_k': stochastic_k,
                'stochastic_d': stochastic_d,
                'cci': cci,
                'rsi_condition': 30 < weekly_rsi < 70,
                'stoch_bullish': stochastic_k > stochastic_d
            },
            'volume_analysis': {
                'mfi': mfi,
                'mfi_bullish': mfi > 50
            },
            'levels': {
                'pivot_points': pivot_points,
                'swing_highs': swing_highs,
                'swing_lows': swing_lows
            },
            'trend_context': trend_context,
            'current_price': current.close
        }

    def _analyze_ema_trend(self, ema_20: float, ema_50: float, ema_200: float, current_price: float) -> str:
        """Analyze EMA trend alignment"""
        if current_price > ema_20 > ema_50 > ema_200:
            return "STRONG_BULLISH"
        elif current_price > ema_20 > ema_50:
            return "BULLISH"
        elif current_price < ema_20 < ema_50 < ema_200:
            return "STRONG_BEARISH"
        elif current_price < ema_20 < ema_50:
            return "BEARISH"
        else:
            return "MIXED"

    def _determine_comprehensive_trend(self, ema_20: float, ema_50: float, ema_200: float, 
                                     macd_line: float, macd_signal: float, 
                                     tenkan: float, kijun: float, current_price: float) -> str:
        """Determine comprehensive trend using multiple indicators"""
        bullish_signals = 0
        bearish_signals = 0
        
        # EMA trend signals
        if current_price > ema_20 > ema_50 > ema_200:
            bullish_signals += 2
        elif current_price < ema_20 < ema_50 < ema_200:
            bearish_signals += 2
        
        # MACD signals
        if macd_line > macd_signal:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        # Ichimoku signals
        if tenkan > kijun:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        # Determine overall trend
        if bullish_signals >= 3:
            return "BULLISH_TREND"
        elif bearish_signals >= 3:
            return "BEARISH_TREND"
        else:
            return "SIDEWAYS"