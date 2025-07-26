# processor.py

from datetime import datetime
from collections import defaultdict
import threading
import sys
from typing import Optional, List, Tuple

# Import classes from other files
from models import CandleData, SignalData, SignalType
from utils import TimeUtils
from analysis import TechnicalAnalyzer, PatternDetector
from config import ConfigManager

# ========== SIGNAL PROCESSOR ==========
class SignalProcessor:
    """Main signal processing logic"""

    def __init__(self, analyzer: TechnicalAnalyzer, detector: PatternDetector, logger: 'TradingLogger'):
        self.analyzer = analyzer
        self.detector = detector
        self.logger = logger
        self.daily_signal_count = defaultdict(int)
        self.last_signals = {}
        self.processing_lock = threading.Lock()

    def calculate_strength(self, candles: List[CandleData], pair: str) -> float:
        """Calculate signal strength score"""
        if len(candles) < 30:
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
        rsi = self.analyzer.calculate_rsi(closes)

        if config.rsi_oversold <= rsi <= config.rsi_overbought:
            strength_score += 1.0
        else:
            strength_score += 0.3

        # Time bonus (max 0.5)
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
            support_levels, resistance_levels = self.analyzer.find_support_resistance(candles)

            if direction == SignalType.BULLISH:
                # Find closest support below entry for stop loss
                stop_loss = min([s for s in support_levels if s < entry_price],
                               default=entry_price * 0.98) if support_levels else entry_price * 0.98
                # Find closest resistance above entry for take profit
                take_profit = min([r for r in resistance_levels if r > entry_price],
                                 default=entry_price * 1.04) if resistance_levels else entry_price * 1.04
            else:  # Bearish
                # Find closest resistance above entry for stop loss
                stop_loss = max([r for r in resistance_levels if r > entry_price],
                               default=entry_price * 1.02) if resistance_levels else entry_price * 1.02
                # Find closest support below entry for take profit
                take_profit = max([s for s in support_levels if s < entry_price],
                                 default=entry_price * 0.96) if support_levels else entry_price * 0.96

            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)

            rr_ratio = reward / risk if risk > 0 else 0

            return rr_ratio, stop_loss, take_profit

        except Exception as e:
            # Log specific error during R:R calculation
            self.logger.log_error("SignalProcessor", "R:R calculation error: {}".format(e))
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
            has_sweep, sweep_direction = self.detector.detect_sweep(candle_history, pair)
            # Log the result of sweep detection
            self.logger.log_pattern_detection(pair, "Sweep", has_sweep, {
                "Direction": sweep_direction if has_sweep else "None"
            })

            if not has_sweep:
                self.logger.log_signal_filtered(pair, "No sweep pattern detected")
                return None

            has_engulfing = self.detector.detect_engulfing(candle_history, sweep_direction)
            # Log the result of engulfing detection
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