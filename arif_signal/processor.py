# processor.py

from datetime import datetime
from collections import defaultdict
import threading
import sys # Import sys for fallback logger
from typing import Optional, List, Tuple

# Import classes from models.py, utils.py, analysis.py, and trading_logger.py (Simulated)
# from models import CandleData, SignalData, SignalType # Gagal
# from utils import ConfigManager, TimeUtils # Gagal
# from analysis import TechnicalAnalyzer, PatternDetector # Gagal
# from trading_logger import TradingLogger # Gagal

# --- Simulate TradingLogger ---
# This is a minimal simulation just enough to prevent NameError if logger methods are called.
# The full TradingLogger class would reside in trading_logger.py
import logging # Import logging for fallback
class TradingLogger:
    def __init__(self, *args, **kwargs):
        # Use the root logger for simulation purposes
        self._logger = logging.getLogger("SIMULATED_LOGGER")
        # Configure simulation logger to output to console
        if not self._logger.handlers:
             handler = logging.StreamHandler(sys.stdout)
             formatter = logging.Formatter('%(asctime)s | SIM_LOG | %(message)s')
             handler.setFormatter(formatter)
             self._logger.addHandler(handler)
             self._logger.setLevel(logging.INFO) # Default level for simulation

    def log_bot_start(self, *args, **kwargs): self._logger.info("SIM_LOG: Bot start (simulated)")
    def log_data_initialization(self, *args, **kwargs): self._logger.info(f"SIM_LOG: Data init (simulated) - {args[0]}")
    def log_websocket_connection(self, *args, **kwargs): self._logger.info(f"SIM_LOG: WS connection ({args[0]}) (simulated)")
    def log_candle_received(self, *args, **kwargs): self._logger.debug(f"SIM_LOG: Candle received ({args[0]}) (simulated)")
    def log_signal_analysis_start(self, pair: str, entry_price: float): self._logger.info(f"SIM_LOG: Signal analysis start ({pair} @ {entry_price:.4f}) (simulated)")
    def log_filter_result(self, pair: str, filter_name: str, result: bool, details: str = ""): self._logger.debug(f"SIM_LOG: Filter result ({pair} - {filter_name}: {result}) (simulated) {details}")
    def log_pattern_detection(self, pair: str, pattern_type: str, detected: bool, details: dict = None):
        if detected: self._logger.info(f"SIM_LOG: Pattern detection ({pair} - {pattern_type} DETECTED!) (simulated)")
        else: self._logger.debug(f"SIM_LOG: Pattern detection ({pair} - {pattern_type} not found) (simulated)")
    def log_technical_analysis(self, pair: str, indicators: dict): self._logger.info(f"SIM_LOG: TA ({pair}) (simulated) {indicators}")
    def log_signal_generated(self, signal_data: dict): self._logger.info(f"SIM_LOG: Signal generated ({signal_data['pair']} - {signal_data['direction']}) (simulated)")
    def log_signal_filtered(self, pair: str, reason: str, details: dict = None): self._logger.info(f"SIM_LOG: Signal filtered ({pair} - {reason}) (simulated) {details}")
    def log_telegram_notification(self, *args, **kwargs): self._logger.info(f"SIM_LOG: Telegram notif ({args[0]}) (simulated)")
    def log_error(self, component: str, error_msg: str, pair: str = ""): self._logger.error(f"SIM_LOG: ERROR in {component} - {pair}{error_msg}")
    def log_session_stats(self): self._logger.info("SIM_LOG: Session stats (simulated)")

    @property
    def main_logger(self): return self._logger
    @property
    def data_logger(self): return self._logger
    @property
    def signal_logger(self): return self._logger
    @property
    def websocket_logger(self): return self._logger
    @property
    def pattern_logger(self): return self._logger
    @property
    def telegram_logger(self): return self._logger

    def get_trading_session(self) -> str: return "Simulated Session" # Needed by process_signal
    def get_wib_time_string(self) -> str: return "Simulated WIB Time"


# --- End Simulate TradingLogger ---


# --- Simulate Imports from other files needed by SignalProcessor ---
from dataclasses import dataclass
from datetime import datetime, timedelta # timedelta needed by TimeUtils
import numpy as np # Needed by TechnicalAnalyzer

@dataclass
class CandleData:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    @property
    def body_size(self) -> float: return abs(self.close - self.open)
    @property
    def upper_wick(self) -> float: return self.high - max(self.open, self.close)
    @property
    def lower_wick(self) -> float: return min(self.open, self.close) - self.low

@dataclass
class TradingConfig:
    min_strength: float
    volume_multiplier: float
    rsi_oversold: int
    rsi_overbought: int
    min_risk_reward: float
    priority: int
    max_daily_signals: int

@dataclass
class SignalData:
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

class ConfigManager:
    # Only include what's needed by processor.py
    MIN_VOLUME_USDT = 500000
    SIGNAL_COOLDOWN_MINUTES = 30
    CONFIGS = { # Dummy config needed by get_config
         'BTCUSDT': TradingConfig(4.0, 2.0, 25, 75, 2.0, 1, 4),
         'ETHUSDT': TradingConfig(3.8, 1.8, 28, 72, 2.0, 1, 4),
         'BNBUSDT': TradingConfig(3.5, 1.7, 30, 70, 1.8, 2, 3),
         'SOLUSDT': TradingConfig(3.6, 1.9, 27, 73, 1.8, 2, 3),
         'ADAUSDT': TradingConfig(3.2, 1.6, 30, 70, 1.5, 3, 2),
         'AVAXUSDT': TradingConfig(3.4, 1.8, 28, 72, 1.6, 2, 3),
         'MATICUSDT': TradingConfig(3.0, 1.5, 32, 68, 1.5, 3, 2),
         'DOTUSDT': TradingConfig(3.3, 1.7, 30, 70, 1.6, 3, 2)
    }
    @classmethod
    def get_config(cls, pair: str) -> TradingConfig:
        return cls.CONFIGS.get(pair, cls.CONFIGS['BTCUSDT'])

class TimeUtils:
    WIB_OFFSET = 7
    @classmethod
    def get_wib_hour(cls) -> int: return (datetime.utcnow().hour + cls.WIB_OFFSET) % 24
    @classmethod
    def get_wib_time_string(cls) -> str: wib_time = datetime.utcnow() + timedelta(hours=cls.WIB_OFFSET); return wib_time.strftime('%H:%M:%S WIB')
    @classmethod
    def is_good_trading_time(cls) -> bool: hour = cls.get_wib_hour(); return (8 <= hour <= 12) or (15 <= hour <= 19) or (20 <= hour <= 23)
    @classmethod
    def get_trading_session(cls) -> str:
        hour = cls.get_wib_hour()
        if 8 <= hour <= 12: return "PAGI (Asian+EU Prep)"
        elif 15 <= hour <= 19: return "SORE (London Active)"
        elif 20 <= hour <= 23: return "MALAM (NY Prime)"
        elif 1 <= hour <= 7: return "DINI HARI (Low Volume)"
        else: return "TRANSISI"

class TechnicalAnalyzer:
    def __init__(self, logger: Optional[TradingLogger] = None): self.logger = logger # Accept logger
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1: return 50.0
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0: return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    def find_support_resistance(self, candles: List[CandleData], lookback: int = 20) -> Tuple[List[float], List[float]]:
        if len(candles) < lookback * 2: return [], []
        highs = [c.high for c in candles[-lookback*2:]]
        lows = [c.low for c in candles[-lookback*2:]]
        resistance_levels = [h for i, h in enumerate(highs) if i >= lookback and i < len(highs) - lookback and h == max(highs[i-lookback:i+lookback+1])]
        support_levels = [l for i, l in enumerate(lows) if i >= lookback and i < len(lows) - lookback and l == min(lows[i-lookback:i+lookback+1])]
        return (sorted(list(set(support_levels)))[:5], sorted(list(set(resistance_levels)), reverse=True)[:5])


class PatternDetector:
    def __init__(self, analyzer: TechnicalAnalyzer, logger: Optional[TradingLogger] = None):
        self.analyzer = analyzer
        self.logger = logger # Accept logger
    def detect_sweep(self, candles: List[CandleData], pair: str) -> Tuple[bool, Optional[str]]:
        if len(candles) < 20: return False, None
        current = candles[-1]
        config = ConfigManager.get_config(pair)
        recent_volumes = [c.volume for c in candles[-10:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes) if len(recent_volumes) > 0 else 0
        if avg_volume > 0 and current.volume <= avg_volume * config.volume_multiplier: return False, None
        support_levels, resistance_levels = self.analyzer.find_support_resistance(candles)
        if not support_levels and not resistance_levels: return False, None
        htf_trend = self._get_higher_timeframe_trend(pair)
        for support in support_levels:
            tolerance = support * 0.0015
            if (current.low <= support - tolerance and current.close > support + tolerance and htf_trend in ["BULLISH", "NEUTRAL"]):
                closes = [c.close for c in candles[-14:]]
                rsi = self.analyzer.calculate_rsi(closes)
                if rsi < config.rsi_overbought: return True, SignalType.BULLISH
        for resistance in resistance_levels:
            tolerance = resistance * 0.0015
            if (current.high >= resistance + tolerance and current.close < resistance - tolerance and htf_trend in ["BEARISH", "NEUTRAL"]):
                closes = [c.close for c in candles[-14:]]
                rsi = self.analyzer.calculate_rsi(closes)
                if rsi > config.rsi_oversold: return True, SignalType.BEARISH
        return False, None
    def detect_engulfing(self, candles: List[CandleData], direction: str) -> bool:
        if len(candles) < 3: return False
        c2, c3 = candles[-2], candles[-1]
        if direction == SignalType.BULLISH: basic_engulf = (c2.close < c2.open and c3.close > c3.open and c3.close > c2.open and c3.open < c2.close)
        else: basic_engulf = (c2.close > c2.open and c3.close < c3.open and c3.close < c2.open and c3.open > c2.close)
        if not basic_engulf: return False
        volume_confirmed = c2.volume > 0 and c3.volume > c2.volume * 1.2
        body_confirmed = c2.body_size > 0 and c3.body_size / c2.body_size >= 1.3
        if direction == SignalType.BULLISH: wick_confirmed = c3.lower_wick >= c3.body_size * 0.3
        else: wick_confirmed = c3.upper_wick >= c3.body_size * 0.3
        return volume_confirmed and body_confirmed and wick_confirmed
    def _get_higher_timeframe_trend(self, pair: str) -> str: return "NEUTRAL" # Simulated

# --- End Simulate Imports ---


# ========== SIGNAL PROCESSOR ==========
class SignalProcessor:
    """Main signal processing logic"""

    # Add logger parameter
    def __init__(self, analyzer: TechnicalAnalyzer, detector: PatternDetector, logger: TradingLogger):
        self.analyzer = analyzer
        self.detector = detector
        self.logger = logger # Store logger
        self.daily_signal_count = defaultdict(int)
        self.last_signals = {}
        self.processing_lock = threading.Lock()

    def calculate_strength(self, candles: List[CandleData], pair: str) -> float:
        """Calculate signal strength score"""
        if len(candles) < 30:
            # No specific logging needed for insufficient candles here, caller handles
            return 2.0

        current = candles[-1]
        config = ConfigManager.get_config(pair)
        strength_score = 0.0

        # Volume strength (max 2.0)
        volumes = [c.volume for c in candles[-10:]]
        avg_vol = sum(volumes) / len(volumes) if len(volumes) > 0 else 0
        vol_ratio = current.volume / avg_vol if avg_vol > 0 else 1

        if vol_ratio >= 3.0:
            strength_score += 2.0
        elif vol_ratio >= 2.0:
            strength_score += 1.5
        elif vol_ratio >= 1.5:
            strength_score += 1.0
        else:
            strength_score += 0.5

        # RSI position (max 1.0)
        closes = [c.close for c in candles[-20:]]
        rsi = self.analyzer.calculate_rsi(closes) # TechnicalAnalyzer handles its own logging or returns result

        if config.rsi_oversold <= rsi <= config.rsi_overbought:
            strength_score += 1.0
        else:
            strength_score += 0.3

        # Time bonus (max 0.5)
        # TimeUtils doesn't log internally for verbosity reasons, check and log here
        if TimeUtils.is_good_trading_time():
            strength_score += 0.5
        else:
            strength_score += 0.1

        # Additional factors can be added here
        strength_score += 1.5  # Base score for other factors

        return min(strength_score, 6.5)

    def calculate_risk_reward(self, entry_price: float, direction: str,
                            candles: List[CandleData]) -> Tuple[float, float, float]:
        """Calculate risk/reward ratio and levels"""
        try:
            # TechnicalAnalyzer logs errors if any occur internally during S/R finding
            support_levels, resistance_levels = self.analyzer.find_support_resistance(candles)

            if direction == SignalType.BULLISH:
                # Find closest support below entry for stop loss
                stop_loss = min([s for s in support_levels if s < entry_price],
                                  default=entry_price * 0.98) if support_levels else entry_price * 0.98
                # Find closest resistance above entry for take profit
                take_profit = min([r for r in resistance_levels if r > entry_price],
                                    default=entry_price * 1.04) if resistance_levels else entry_price * 1.04
            else: # Bearish
                # Find closest resistance above entry for stop loss
                stop_loss = max([r for r in resistance_levels if r > entry_price],
                                  default=entry_price * 1.02) if resistance_levels else entry_price * 1.02
                # Find closest support below entry for take profit
                take_profit = max([s for s in support_levels if s < entry_price],
                                    default=entry_price * 0.96) if resistance_levels else entry_price * 0.96

            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)

            rr_ratio = reward / risk if risk > 0 else 0

            # No specific logging of R:R calculation success here, logged with the signal
            return rr_ratio, stop_loss, take_profit

        except Exception as e:
            # Log specific error during R:R calculation
            self.logger.log_error("SignalProcessor", f"R:R calculation error: {e}")
            # Return default values on error to avoid stopping the process
            return 0, entry_price * 0.98, entry_price * 1.02

    def process_signal(self, pair: str, candle: CandleData,
                      candle_history: List[CandleData]) -> Optional[SignalData]:
        """Main signal processing method with detailed logging"""
        with self.processing_lock:
            entry_price = candle.close
            # Log the start of the analysis process for this candle
            self.logger.log_signal_analysis_start(pair, entry_price)

            # Time filter
            if not TimeUtils.is_good_trading_time():
                session = TimeUtils.get_trading_session()
                self.logger.log_filter_result(
                    pair, "Time Filter", False,
                    f"Bad session: {session}"
                )
                # Log that the signal was filtered due to time
                self.logger.log_signal_filtered(pair, "Outside good trading hours", {
                    "Session": session,
                    "Current Time": TimeUtils.get_wib_time_string()
                })
                return None

            self.logger.log_filter_result(pair, "Time Filter", True, "Good trading session")

            # Daily limit check
            today = datetime.utcnow().date()
            config = ConfigManager.get_config(pair)
            current_signals = self.daily_signal_count[f"{pair}_{today}"]

            if current_signals >= config.max_daily_signals:
                self.logger.log_filter_result(
                    pair, "Daily Limit", False,
                    f"{current_signals}/{config.max_daily_signals} signals today"
                )
                # Log that the signal was filtered due to daily limit
                self.logger.log_signal_filtered(pair, "Daily signal limit reached", {
                    "Count Today": current_signals,
                    "Limit": config.max_daily_signals
                })
                return None

            self.logger.log_filter_result(
                pair, "Daily Limit", True,
                f"{current_signals}/{config.max_daily_signals} signals today"
            )

            # Volume filter
            volume_usdt = candle.volume * candle.close
            min_volume = ConfigManager.MIN_VOLUME_USDT

            if volume_usdt < min_volume:
                self.logger.log_filter_result(
                    pair, "Volume Filter", False,
                    f"${volume_usdt:,.0f} < ${min_volume:,.0f} required"
                )
                 # Log that the signal was filtered due to low volume
                self.logger.log_signal_filtered(pair, "Insufficient volume", {
                    "Actual Volume (USDT)": f"${volume_usdt:,.0f}",
                    "Minimum Required (USDT)": f"${min_volume:,.0f}"
                })
                return None

            self.logger.log_filter_result(
                pair, "Volume Filter", True,
                f"${volume_usdt:,.0f} volume"
            )

            # Pattern detection
            # PatternDetector logs debug information internally
            has_sweep, sweep_direction = self.detector.detect_sweep(candle_history, pair)
            # Log the result of sweep detection (PatternDetector's method logs details)
            self.logger.log_pattern_detection(pair, "Sweep", has_sweep, {
                "Direction": sweep_direction if has_sweep else "None"
            })

            if not has_sweep:
                self.logger.log_signal_filtered(pair, "No sweep pattern detected")
                return None

            # PatternDetector logs debug information internally
            has_engulfing = self.detector.detect_engulfing(candle_history, sweep_direction)
             # Log the result of engulfing detection (PatternDetector's method logs details)
            self.logger.log_pattern_detection(pair, "Engulfing", has_engulfing, {
                "Direction": sweep_direction,
                "Candles Analyzed": len(candle_history)
            })


            if not has_engulfing:
                self.logger.log_signal_filtered(pair, "No engulfing pattern detected")
                return None

            # Strength calculation
            strength = self.calculate_strength(candle_history, pair)

            # Technical analysis logging - Gather data and log here
            closes = [c.close for c in candle_history[-20:]]
            rsi = self.analyzer.calculate_rsi(closes)
            support_levels, resistance_levels = self.analyzer.find_support_resistance(candle_history)

            # Log key TA indicators used in the analysis
            self.logger.log_technical_analysis(pair, {
                "RSI": rsi,
                "Strength Score": strength,
                "Support Levels Found": len(support_levels),
                "Resistance Levels Found": len(resistance_levels),
                "Volume Ratio (Current/Avg)": volume_usdt / (sum([c.volume for c in candle_history[-10:]]) / 10) if sum([c.volume for c in candle_history[-10:]]) > 0 else 0
            })


            if strength < config.min_strength:
                self.logger.log_filter_result(
                    pair, "Strength Filter", False,
                    f"{strength:.1f} < {config.min_strength} required"
                )
                # Log that the signal was filtered due to insufficient strength
                self.logger.log_signal_filtered(pair, "Insufficient signal strength", {
                    "Actual Strength": f"{strength:.1f}★",
                    "Required Strength": f"{config.min_strength}★"
                })
                return None

            self.logger.log_filter_result(
                pair, "Strength Filter", True,
                f"{strength:.1f}★ strength"
            )

            # Risk/reward calculation
            # calculate_risk_reward logs errors internally
            rr_ratio, stop_loss, take_profit = self.calculate_risk_reward(
                entry_price, sweep_direction, candle_history
            )

            if rr_ratio < config.min_risk_reward:
                self.logger.log_filter_result(
                    pair, "Risk/Reward Filter", False,
                    f"1:{rr_ratio:.1f} < 1:{config.min_risk_reward} required"
                )
                # Log that the signal was filtered due to poor R:R
                self.logger.log_signal_filtered(pair, "Poor risk/reward ratio", {
                    "Actual R:R": f"1:{rr_ratio:.1f}",
                    "Required R:R": f"1:{config.min_risk_reward}"
                })
                return None

            self.logger.log_filter_result(
                pair, "Risk/Reward Filter", True,
                f"1:{rr_ratio:.1f} ratio"
            )

            # Anti-spam check (Cooldown Filter)
            current_time = datetime.utcnow()
            signal_key = f"{pair}_{sweep_direction}"

            if signal_key in self.last_signals:
                time_diff = (current_time - self.last_signals[signal_key]).total_seconds() / 60
                if time_diff < ConfigManager.SIGNAL_COOLDOWN_MINUTES:
                    self.logger.log_filter_result(
                        pair, "Cooldown Filter", False,
                        f"{time_diff:.1f} min < {ConfigManager.SIGNAL_COOLDOWN_MINUTES} min required"
                    )
                    # Log that the signal was filtered due to cooldown
                    self.logger.log_signal_filtered(pair, "Signal cooldown active", {
                        "Time Since Last Signal": f"{time_diff:.1f} minutes",
                        "Cooldown Period": f"{ConfigManager.SIGNAL_COOLDOWN_MINUTES} minutes"
                    })
                    return None

            self.logger.log_filter_result(pair, "Cooldown Filter", True, "No recent signals")

            # Create signal data
            signal_type = SignalType.BUY if sweep_direction == SignalType.BULLISH else SignalType.SELL
            signal_data = {
                'pair': pair,
                'direction': signal_type,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'strength': strength,
                'risk_reward': rr_ratio,
                'timestamp': current_time
            }

            # Log successful signal generation
            self.logger.log_signal_generated(signal_data)

            # Update counters
            self.last_signals[signal_key] = current_time
            self.daily_signal_count[f"{pair}_{today}"] += 1

            # Return the generated signal data object
            return SignalData(**signal_data)