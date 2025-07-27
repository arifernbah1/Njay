# processor.py

from datetime import datetime
from collections import defaultdict
import threading
import sys
from typing import Optional, List, Tuple, Dict

# Import classes from other files
from models import CandleData, SignalData, SignalType
from utils import TimeUtils
from analysis import TechnicalAnalyzer, PatternDetector
from config import ConfigManager

# ========== SIGNAL PROCESSOR ==========
class SignalProcessor:
    """Main signal processing logic for dual mode"""
    # Add logger parameter
    def __init__(self, analyzer: TechnicalAnalyzer, detector: PatternDetector, logger: TradingLogger):
        self.analyzer = analyzer
        self.detector = detector
        self.logger = logger # Store logger
        # Separate tracking for each mode
        self.daily_signal_count_scalping = defaultdict(int)
        self.daily_signal_count_swing = defaultdict(int)
        self.last_signals_scalping = {}
        self.last_signals_swing = {}
        self.processing_lock = threading.Lock()

    def calculate_strength(self, candles: List[CandleData], pair: str, mode: str = "SCALPING") -> float:
        """Calculate signal strength score for specific mode"""
        if len(candles) < 30:
            return 2.0 if mode == "SCALPING" else 3.0  # Different base scores per mode
            
        current = candles[-1]
        mode_config = ConfigManager.get_mode_config(mode)
        strength_score = 0.0
        
        # Volume strength (max 2.0)
        volumes = [c.volume for c in candles[-10:]]
        avg_vol = sum(volumes) / len(volumes) if len(volumes) > 0 else 0
        vol_ratio = current.volume / avg_vol if avg_vol > 0 else 1
        
        if mode == "SCALPING":
            # Scalping: lebih sensitif terhadap volume
            if vol_ratio >= 2.0:
                strength_score += 2.0
            elif vol_ratio >= 1.5:
                strength_score += 1.5
            elif vol_ratio >= 1.2:
                strength_score += 1.0
            else:
                strength_score += 0.5
        else:
            # Swing: volume lebih konservatif
            if vol_ratio >= 3.0:
                strength_score += 2.0
            elif vol_ratio >= 2.0:
                strength_score += 1.5
            elif vol_ratio >= 1.5:
                strength_score += 1.0
            else:
                strength_score += 0.3
        
        # RSI position (max 1.0)
        closes = [c.close for c in candles[-20:]]
        rsi = self.analyzer.calculate_rsi(closes)
        
        if mode_config['rsi_oversold'] <= rsi <= mode_config['rsi_overbought']:
            strength_score += 1.0
        else:
            strength_score += 0.3
        
        # Time bonus (max 0.5)
        if TimeUtils.is_good_trading_time():
            strength_score += 0.5
        else:
            strength_score += 0.1
        
        # Mode-specific base score
        if mode == "SCALPING":
            strength_score += 1.0  # Lower base for scalping
        else:
            strength_score += 1.5  # Higher base for swing
        
        return min(strength_score, 6.5)

    def calculate_risk_reward(self, entry_price: float, direction: str, candles: List[CandleData], mode: str = "SCALPING") -> Tuple[float, float, float]:
        """Calculate risk/reward ratio and levels for specific mode"""
        try:
            support_levels, resistance_levels = self.analyzer.find_support_resistance(candles)
            mode_config = ConfigManager.get_mode_config(mode)
            
            if direction == SignalType.BULLISH:
                # Find closest support below entry for stop loss
                stop_loss = min([s for s in support_levels if s < entry_price], default=entry_price * 0.98) if support_levels else entry_price * 0.98
                
                # Find closest resistance above entry for take profit
                take_profit = min([r for r in resistance_levels if r > entry_price], default=entry_price * 1.04) if resistance_levels else entry_price * 1.04
                
                # Mode-specific adjustments
                if mode == "SCALPING":
                    # Scalping: tighter stops and targets
                    stop_loss = entry_price * 0.99  # 1% stop loss
                    take_profit = entry_price * 1.02  # 2% take profit
                else:
                    # Swing: wider stops and targets
                    stop_loss = entry_price * 0.97  # 3% stop loss
                    take_profit = entry_price * 1.06  # 6% take profit
            else:
                # Bearish
                # Find closest resistance above entry for stop loss
                stop_loss = max([r for r in resistance_levels if r > entry_price], default=entry_price * 1.02) if resistance_levels else entry_price * 1.02
                
                # Find closest support below entry for take profit
                take_profit = max([s for s in support_levels if s < entry_price], default=entry_price * 0.96) if support_levels else entry_price * 0.96
                
                # Mode-specific adjustments
                if mode == "SCALPING":
                    # Scalping: tighter stops and targets
                    stop_loss = entry_price * 1.01  # 1% stop loss
                    take_profit = entry_price * 0.98  # 2% take profit
                else:
                    # Swing: wider stops and targets
                    stop_loss = entry_price * 1.03  # 3% stop loss
                    take_profit = entry_price * 0.94  # 6% take profit
            
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            return rr_ratio, stop_loss, take_profit
            
        except Exception as e:
            self.logger.log_error("SignalProcessor", "R:R calculation error: {}".format(e))
            # Return default values on error
            if mode == "SCALPING":
                return 1.2, entry_price * 0.99, entry_price * 1.02
            else:
                return 2.0, entry_price * 0.97, entry_price * 1.06

    def process_signal(self, candles: List[CandleData], pair: str, mode: str = "SCALPING") -> Optional[SignalData]:
        """Process signal with Trading Logger integration"""
        if not candles or len(candles) < 20:
            return None
        
        try:
            current = candles[-1]
            entry_price = current.close
            today = datetime.now().strftime("%Y%m%d")
            
            # Get mode-specific configuration
            mode_config = self.get_mode_config(mode)
            
            # Cooldown check with Trading Logger
            if not self.check_cooldown(pair, mode):
                self.trading_logger.log_trading_alert(
                    "COOLDOWN",
                    f"Cooldown active for {pair}",
                    pair=pair,
                    mode=mode
                )
                return None
            
            # Technical analysis with Trading Logger
            if mode == "SCALPING":
                ta_data = self.detector.analyze_scalping_15m(candles, pair)
            else:  # SWING mode
                ta_data = self.detector.analyze_swing_1h(candles, pair)
            
            # Log market analysis with Trading Logger
            self.trading_logger.log_market_analysis(pair, ta_data, mode)
            
            # Volume filter with Trading Logger
            if mode == "SCALPING":
                volume_ratio = ta_data.get('volume_ratio', 1)
                volume_passed = volume_ratio >= mode_config['volume_threshold']
                
                if not volume_passed:
                    self.trading_logger.log_trading_alert(
                        "FILTER_FAILED",
                        f"Volume ratio {volume_ratio:.2f} < {mode_config['volume_threshold']} threshold",
                        pair=pair,
                        mode=mode
                    )
                    return None
            else:  # SWING mode
                mfi = ta_data.get('volume_analysis', {}).get('mfi', 50)
                volume_passed = mfi >= 50  # MFI threshold for swing
                
                if not volume_passed:
                    self.trading_logger.log_trading_alert(
                        "FILTER_FAILED",
                        f"MFI {mfi:.2f} < 50 threshold",
                        pair=pair,
                        mode=mode
                    )
                    return None
            
            # Pattern detection with Trading Logger
            if mode == "SCALPING":
                sweep_detected, sweep_direction = self.detector.detect_sweep(candles, pair, "SCALPING")
            else:  # SWING mode
                sweep_detected, sweep_direction = self.detector.detect_sweep(candles, pair, "SWING")
            
            if sweep_detected:
                # Log pattern detection with Trading Logger
                self.trading_logger.log_pattern_detection(
                    pair, "Sweep", True, 
                    {"Direction": sweep_direction, "Mode": mode}, 
                    mode, confidence=0.85
                )
                
                # Calculate strength and risk/reward
                strength = self.calculate_strength(candles, pair, mode)
                rr_ratio, stop_loss, take_profit = self.calculate_risk_reward(entry_price, sweep_direction, candles, mode)
                
                # Mode-specific strength filter
                if strength >= mode_config['min_strength'] and rr_ratio >= mode_config['min_risk_reward']:
                    # Create signal
                    signal = SignalData(
                        pair=pair,
                        direction=SignalType.BUY if sweep_direction == SignalType.BULLISH else SignalType.SELL,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        strength=strength,
                        risk_reward=rr_ratio,
                        timestamp=datetime.utcnow()
                    )
                    
                    # Update tracking
                    if mode == "SCALPING":
                        self.daily_signal_count_scalping["{}_{}".format(pair, today)] += 1
                        self.last_signals_scalping[pair] = datetime.utcnow()
                    else:
                        self.daily_signal_count_swing["{}_{}".format(pair, today)] += 1
                        self.last_signals_swing[pair] = datetime.utcnow()
                    
                    # Log risk management with Trading Logger
                    self.trading_logger.log_risk_management(
                        pair, "ENTRY", {
                            "entry_price": entry_price,
                            "stop_loss": stop_loss,
                            "take_profit": take_profit,
                            "risk_reward": rr_ratio,
                            "strength": strength
                        }, mode
                    )
                    
                    return signal
                else:
                    self.trading_logger.log_trading_alert(
                        "FILTER_FAILED",
                        f"Strength/R:R insufficient - Strength: {strength:.2f}, R:R: {rr_ratio:.2f}",
                        pair=pair,
                        mode=mode
                    )
            
            # Check for engulfing patterns (only for scalping mode)
            if mode == "SCALPING":
                if sweep_direction == SignalType.BULLISH and self.detector.detect_engulfing(candles, SignalType.BULLISH):
                    # Log pattern detection with Trading Logger
                    self.trading_logger.log_pattern_detection(
                        pair, "Bullish Engulfing", True, 
                        {"Mode": mode}, 
                        mode, confidence=0.80
                    )
                    
                    # Calculate strength and risk/reward
                    strength = self.calculate_strength(candles, pair, mode)
                    rr_ratio, stop_loss, take_profit = self.calculate_risk_reward(entry_price, SignalType.BULLISH, candles, mode)
                    
                    # Mode-specific strength filter
                    if strength >= mode_config['min_strength'] and rr_ratio >= mode_config['min_risk_reward']:
                        # Create signal
                        signal = SignalData(
                            pair=pair,
                            direction=SignalType.BUY,
                            entry_price=entry_price,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            strength=strength,
                            risk_reward=rr_ratio,
                            timestamp=datetime.utcnow()
                        )
                        
                        # Update tracking
                        self.daily_signal_count_scalping["{}_{}".format(pair, today)] += 1
                        self.last_signals_scalping[pair] = datetime.utcnow()
                        
                        # Log risk management with Trading Logger
                        self.trading_logger.log_risk_management(
                            pair, "ENTRY", {
                                "entry_price": entry_price,
                                "stop_loss": stop_loss,
                                "take_profit": take_profit,
                                "risk_reward": rr_ratio,
                                "strength": strength
                            }, mode
                        )
                        
                        return signal
                    else:
                        self.trading_logger.log_trading_alert(
                            "FILTER_FAILED",
                            f"Strength/R:R insufficient - Strength: {strength:.2f}, R:R: {rr_ratio:.2f}",
                            pair=pair,
                            mode=mode
                        )
                
                elif sweep_direction == SignalType.BEARISH and self.detector.detect_engulfing(candles, SignalType.BEARISH):
                    # Log pattern detection with Trading Logger
                    self.trading_logger.log_pattern_detection(
                        pair, "Bearish Engulfing", True, 
                        {"Mode": mode}, 
                        mode, confidence=0.80
                    )
                    
                    # Calculate strength and risk/reward
                    strength = self.calculate_strength(candles, pair, mode)
                    rr_ratio, stop_loss, take_profit = self.calculate_risk_reward(entry_price, SignalType.BEARISH, candles, mode)
                    
                    # Mode-specific strength filter
                    if strength >= mode_config['min_strength'] and rr_ratio >= mode_config['min_risk_reward']:
                        # Create signal
                        signal = SignalData(
                            pair=pair,
                            direction=SignalType.SELL,
                            entry_price=entry_price,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            strength=strength,
                            risk_reward=rr_ratio,
                            timestamp=datetime.utcnow()
                        )
                        
                        # Update tracking
                        self.daily_signal_count_scalping["{}_{}".format(pair, today)] += 1
                        self.last_signals_scalping[pair] = datetime.utcnow()
                        
                        # Log risk management with Trading Logger
                        self.trading_logger.log_risk_management(
                            pair, "ENTRY", {
                                "entry_price": entry_price,
                                "stop_loss": stop_loss,
                                "take_profit": take_profit,
                                "risk_reward": rr_ratio,
                                "strength": strength
                            }, mode
                        )
                        
                        return signal
                    else:
                        self.trading_logger.log_trading_alert(
                            "FILTER_FAILED",
                            f"Strength/R:R insufficient - Strength: {strength:.2f}, R:R: {rr_ratio:.2f}",
                            pair=pair,
                            mode=mode
                        )
            
            # Swing Trading OTL Pattern Detection (for SWING mode only)
            if mode == "SWING":
                otl_breakout = self.detector.detect_otl_breakout(candles, pair)
                if otl_breakout:
                    # Log pattern detection with Trading Logger
                    self.trading_logger.log_pattern_detection(
                        pair, "OTL Breakout", True, 
                        {"Mode": mode}, 
                        mode, confidence=0.90
                    )
                    
                    # Calculate strength and risk/reward
                    strength = self.calculate_strength(candles, pair, mode)
                    rr_ratio, stop_loss, take_profit = self.calculate_risk_reward(entry_price, otl_breakout, candles, mode)
                    
                    # Mode-specific strength filter
                    if strength >= mode_config['min_strength'] and rr_ratio >= mode_config['min_risk_reward']:
                        # Create signal
                        signal = SignalData(
                            pair=pair,
                            direction=SignalType.BUY if otl_breakout == SignalType.BULLISH else SignalType.SELL,
                            entry_price=entry_price,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            strength=strength,
                            risk_reward=rr_ratio,
                            timestamp=datetime.utcnow()
                        )
                        
                        # Update tracking
                        self.daily_signal_count_swing["{}_{}".format(pair, today)] += 1
                        self.last_signals_swing[pair] = datetime.utcnow()
                        
                        # Log risk management with Trading Logger
                        self.trading_logger.log_risk_management(
                            pair, "ENTRY", {
                                "entry_price": entry_price,
                                "stop_loss": stop_loss,
                                "take_profit": take_profit,
                                "risk_reward": rr_ratio,
                                "strength": strength
                            }, mode
                        )
                        
                        return signal
                    else:
                        self.trading_logger.log_trading_alert(
                            "FILTER_FAILED",
                            f"Strength/R:R insufficient - Strength: {strength:.2f}, R:R: {rr_ratio:.2f}",
                            pair=pair,
                            mode=mode
                        )
            
            # No pattern detected
            self.trading_logger.log_trading_alert(
                "NO_PATTERN",
                f"No pattern detected for {pair}",
                pair=pair,
                mode=mode
            )
            
        except Exception as e:
            self.trading_logger.log_trading_alert(
                "ERROR",
                f"Error processing signal for {pair}: {str(e)}",
                pair=pair,
                mode=mode,
                priority="CRITICAL"
            )
        
        return None

    def calculate_otl_strength(self, candles: List[CandleData], pair: str, otl_data: Dict) -> float:
        """Calculate strength specifically for OTL signals"""
        if len(candles) < 50:
            return 3.0
        
        current = candles[-1]
        indicators = otl_data.get('indicators', {})
        
        strength_score = 0.0
        
        # Trend alignment (max 2.0)
        trend_context = otl_data.get('trend_context', 'SIDEWAYS')
        if trend_context == "BULLISH_TREND":
            strength_score += 2.0
        elif trend_context == "BEARISH_TREND":
            strength_score += 2.0
        else:
            strength_score += 1.0
        
        # Volume confirmation (max 1.5)
        if otl_data.get('volume_confirmation', False):
            strength_score += 1.5
        
        # Momentum confirmation (max 1.5)
        if otl_data.get('momentum_confirmation', False):
            strength_score += 1.5
        
        # Indicator confluence (max 1.0)
        confluence_count = 0
        if indicators.get('macd_line', 0) > indicators.get('macd_signal', 0):
            confluence_count += 1
        if 30 < indicators.get('weekly_rsi', 50) < 70:
            confluence_count += 1
        if indicators.get('stochastic_k', 50) > indicators.get('stochastic_d', 50):
            confluence_count += 1
        
        strength_score += (confluence_count / 3) * 1.0
        
        # Breakout quality (max 1.0)
        breakout_type = otl_data.get('breakout_type', '')
        if 'SWING_HIGH' in breakout_type or 'SWING_LOW' in breakout_type:
            strength_score += 1.0
        elif 'PIVOT' in breakout_type:
            strength_score += 0.8
        else:
            strength_score += 0.5
        
        return min(strength_score, 6.0)

    def calculate_otl_risk_reward(self, entry_price: float, direction: str, candles: List[CandleData], otl_data: Dict) -> Tuple[float, float, float]:
        """Calculate risk/reward specifically for OTL signals"""
        try:
            # Get swing levels
            swing_highs, swing_lows = self.analyzer.find_swing_levels(candles)
            pivot_points = self.analyzer.calculate_pivot_points(candles)
            
            if direction == SignalType.BULLISH:
                # For bullish OTL, find next resistance levels
                resistance_levels = swing_highs + [pivot_points.get('R1', 0), pivot_points.get('R2', 0)]
                resistance_levels = [r for r in resistance_levels if r > entry_price]
                
                if resistance_levels:
                    take_profit = min(resistance_levels)  # Closest resistance
                else:
                    take_profit = entry_price * 1.08  # 8% default target
                
                # Stop loss below recent swing low
                support_levels = swing_lows + [pivot_points.get('S1', 0)]
                support_levels = [s for s in support_levels if s < entry_price]
                
                if support_levels:
                    stop_loss = max(support_levels)  # Closest support
                else:
                    stop_loss = entry_price * 0.97  # 3% default stop
                    
            else:  # Bearish
                # For bearish OTL, find next support levels
                support_levels = swing_lows + [pivot_points.get('S1', 0), pivot_points.get('S2', 0)]
                support_levels = [s for s in support_levels if s < entry_price]
                
                if support_levels:
                    take_profit = max(support_levels)  # Closest support
                else:
                    take_profit = entry_price * 0.92  # 8% default target
                
                # Stop loss above recent swing high
                resistance_levels = swing_highs + [pivot_points.get('R1', 0)]
                resistance_levels = [r for r in resistance_levels if r > entry_price]
                
                if resistance_levels:
                    stop_loss = min(resistance_levels)  # Closest resistance
                else:
                    stop_loss = entry_price * 1.03  # 3% default stop
            
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            return rr_ratio, stop_loss, take_profit
            
        except Exception as e:
            self.logger.log_error("SignalProcessor", "OTL R:R calculation error: {}".format(e))
            # Return default values on error
            if direction == SignalType.BULLISH:
                return 2.5, entry_price * 0.97, entry_price * 1.08
            else:
                return 2.5, entry_price * 1.03, entry_price * 0.92