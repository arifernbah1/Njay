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
from arif_signal.swing_setup import SwingSetupManager

# ========== SIGNAL PROCESSOR ==========
class SignalProcessor:
    """Enhanced signal processor with swing setup integration"""
    
    def __init__(self, trading_logger):
        self.trading_logger = trading_logger
        self.detector = PatternDetector(trading_logger)
        self.swing_setup_manager = SwingSetupManager(trading_logger)
        
        # Signal tracking
        self.daily_signal_count_scalping = {}
        self.daily_signal_count_swing = {}
        self.last_signals_scalping = {}
        self.last_signals_swing = {}
    
    def process_signal(self, candles: List[CandleData], pair: str, mode: str = "SCALPING") -> Optional[SignalData]:
        """Process signal with swing setup integration"""
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
            
            # Mode-specific processing
            if mode == "SCALPING":
                return self._process_scalping_signal(candles, pair, mode_config, today)
            else:  # SWING mode
                return self._process_swing_signal(candles, pair, mode_config, today)
            
        except Exception as e:
            self.trading_logger.log_trading_alert(
                "ERROR",
                f"Error processing signal for {pair}: {str(e)}",
                pair=pair,
                mode=mode,
                priority="CRITICAL"
            )
        
        return None
    
    def _process_scalping_signal(self, candles: List[CandleData], pair: str, mode_config: Dict, today: str) -> Optional[SignalData]:
        """Process scalping signal (existing logic)"""
        try:
            current = candles[-1]
            entry_price = current.close
            
            # Technical analysis
            ta_data = self.detector.analyze_scalping_15m(candles, pair)
            
            # Log market analysis
            self.trading_logger.log_market_analysis(pair, ta_data, "SCALPING")
            
            # Volume filter
            volume_ratio = ta_data.get('volume_ratio', 1)
            if volume_ratio < mode_config['volume_threshold']:
                self.trading_logger.log_trading_alert(
                    "FILTER_FAILED",
                    f"Volume ratio {volume_ratio:.2f} < {mode_config['volume_threshold']} threshold",
                    pair=pair,
                    mode="SCALPING"
                )
                return None
            
            # Pattern detection
            sweep_detected, sweep_direction = self.detector.detect_sweep(candles, pair, "SCALPING")
            
            if sweep_detected:
                # Log pattern detection
                self.trading_logger.log_pattern_detection(
                    pair, "Sweep", True, 
                    {"Direction": sweep_direction, "Mode": "SCALPING"}, 
                    "SCALPING", confidence=0.85
                )
                
                # Calculate metrics
                strength = self.calculate_strength(candles, pair, "SCALPING")
                rr_ratio, stop_loss, take_profit = self.calculate_risk_reward(entry_price, sweep_direction, candles, "SCALPING")
                
                # Validate signal
                if strength >= mode_config['min_strength'] and rr_ratio >= mode_config['min_risk_reward']:
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
                    self.daily_signal_count_scalping["{}_{}".format(pair, today)] += 1
                    self.last_signals_scalping[pair] = datetime.utcnow()
                    
                    # Log risk management
                    self.trading_logger.log_risk_management(
                        pair, "ENTRY", {
                            "entry_price": entry_price,
                            "stop_loss": stop_loss,
                            "take_profit": take_profit,
                            "risk_reward": rr_ratio,
                            "strength": strength
                        }, "SCALPING"
                    )
                    
                    return signal
                else:
                    self.trading_logger.log_trading_alert(
                        "FILTER_FAILED",
                        f"Strength/R:R insufficient - Strength: {strength:.2f}, R:R: {rr_ratio:.2f}",
                        pair=pair,
                        mode="SCALPING"
                    )
            
            # Check engulfing patterns
            if sweep_direction == SignalType.BULLISH and self.detector.detect_engulfing(candles, SignalType.BULLISH):
                return self._process_engulfing_signal(candles, pair, SignalType.BULLISH, "SCALPING", mode_config, today)
            elif sweep_direction == SignalType.BEARISH and self.detector.detect_engulfing(candles, SignalType.BEARISH):
                return self._process_engulfing_signal(candles, pair, SignalType.BEARISH, "SCALPING", mode_config, today)
            
            # No pattern detected
            self.trading_logger.log_trading_alert(
                "NO_PATTERN",
                f"No pattern detected for {pair}",
                pair=pair,
                mode="SCALPING"
            )
            
        except Exception as e:
            self.trading_logger.log_trading_alert(
                "ERROR",
                f"Error processing scalping signal: {str(e)}",
                pair=pair,
                mode="SCALPING",
                priority="HIGH"
            )
        
        return None
    
    def _process_swing_signal(self, candles: List[CandleData], pair: str, mode_config: Dict, today: str) -> Optional[SignalData]:
        """Process swing signal with setup integration"""
        try:
            current = candles[-1]
            entry_price = current.close
            
            # Cleanup expired setups first
            self.swing_setup_manager.cleanup_expired_setups()
            
            # Check for existing active setups
            active_setups = self.swing_setup_manager.get_active_setups(pair)
            
            # If no active setup, try to create new one
            if not active_setups:
                setup = self.swing_setup_manager.analyze_swing_setup(candles, pair)
                if setup:
                    self.swing_setup_manager.add_setup(setup)
                    active_setups = [setup]
            
            # Process active setups
            for setup in active_setups:
                if self._check_setup_trigger(setup, current):
                    return self._execute_swing_setup(setup, current, pair, mode_config, today)
            
            # If no setup triggered, check for OTL pattern
            otl_breakout = self.detector.detect_otl_breakout(candles, pair)
            if otl_breakout:
                return self._process_otl_signal(candles, pair, otl_breakout, mode_config, today)
            
            # No setup or pattern triggered
            self.trading_logger.log_trading_alert(
                "NO_SETUP",
                f"No swing setup triggered for {pair}",
                pair=pair,
                mode="SWING"
            )
            
        except Exception as e:
            self.trading_logger.log_trading_alert(
                "ERROR",
                f"Error processing swing signal: {str(e)}",
                pair=pair,
                mode="SWING",
                priority="HIGH"
            )
        
        return None
    
    def _check_setup_trigger(self, setup: 'SwingSetup', current: CandleData) -> bool:
        """Check if setup is triggered by current price action"""
        try:
            entry_min, entry_max = setup.entry_zone
            
            # Check if price is in entry zone
            if entry_min <= current.close <= entry_max:
                # Additional confirmation checks
                if setup.setup_type == "BREAKOUT":
                    # Volume confirmation for breakout
                    if current.volume > setup.volume_profile.get('avg_volume', 0) * 1.2:
                        return True
                elif setup.setup_type == "REVERSAL":
                    # Candle pattern confirmation for reversal
                    if (setup.market_structure == "BEARISH" and current.close > current.open) or \
                       (setup.market_structure == "BULLISH" and current.close < current.open):
                        return True
                elif setup.setup_type == "CONTINUATION":
                    # Trend continuation confirmation
                    return True
            
            return False
            
        except Exception as e:
            return False
    
    def _execute_swing_setup(self, setup: 'SwingSetup', current: CandleData, pair: str, 
                           mode_config: Dict, today: str) -> Optional[SignalData]:
        """Execute swing setup and create signal"""
        try:
            entry_price = current.close
            
            # Determine direction based on setup
            if setup.setup_type == "BREAKOUT":
                direction = SignalType.BUY if entry_price > setup.key_levels.get('resistance_1', 0) else SignalType.SELL
            elif setup.setup_type == "REVERSAL":
                direction = SignalType.BUY if setup.market_structure == "BEARISH" else SignalType.SELL
            else:  # CONTINUATION
                direction = SignalType.BUY if setup.market_structure == "BULLISH" else SignalType.SELL
            
            # Create signal
            signal = SignalData(
                pair=pair,
                direction=direction,
                entry_price=entry_price,
                stop_loss=setup.stop_loss,
                take_profit=setup.take_profit[0],  # Use first target
                strength=setup.setup_strength,
                risk_reward=setup.risk_reward,
                timestamp=datetime.utcnow()
            )
            
            # Update tracking
            self.daily_signal_count_swing["{}_{}".format(pair, today)] += 1
            self.last_signals_swing[pair] = datetime.utcnow()
            
            # Mark setup as triggered
            setup.status = "TRIGGERED"
            
            # Log setup execution
            self.trading_logger.log_trading_alert(
                "SWING_SETUP_TRIGGERED",
                f"Swing setup triggered: {setup.setup_type} for {pair}",
                pair=pair,
                mode="SWING",
                priority="HIGH"
            )
            
            # Log risk management
            self.trading_logger.log_risk_management(
                pair, "ENTRY", {
                    "entry_price": entry_price,
                    "stop_loss": setup.stop_loss,
                    "take_profit": setup.take_profit,
                    "risk_reward": setup.risk_reward,
                    "strength": setup.setup_strength,
                    "setup_type": setup.setup_type
                }, "SWING"
            )
            
            return signal
            
        except Exception as e:
            self.trading_logger.log_trading_alert(
                "ERROR",
                f"Error executing swing setup: {str(e)}",
                pair=pair,
                mode="SWING",
                priority="CRITICAL"
            )
            return None
    
    def _process_engulfing_signal(self, candles: List[CandleData], pair: str, direction: str, 
                                mode: str, mode_config: Dict, today: str) -> Optional[SignalData]:
        """Process engulfing pattern signal"""
        try:
            current = candles[-1]
            entry_price = current.close
            
            # Log pattern detection
            pattern_name = "Bullish Engulfing" if direction == SignalType.BULLISH else "Bearish Engulfing"
            self.trading_logger.log_pattern_detection(
                pair, pattern_name, True, 
                {"Mode": mode}, 
                mode, confidence=0.80
            )
            
            # Calculate metrics
            strength = self.calculate_strength(candles, pair, mode)
            rr_ratio, stop_loss, take_profit = self.calculate_risk_reward(entry_price, direction, candles, mode)
            
            # Validate signal
            if strength >= mode_config['min_strength'] and rr_ratio >= mode_config['min_risk_reward']:
                signal = SignalData(
                    pair=pair,
                    direction=SignalType.BUY if direction == SignalType.BULLISH else SignalType.SELL,
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
                
                # Log risk management
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
            
        except Exception as e:
            self.trading_logger.log_trading_alert(
                "ERROR",
                f"Error processing engulfing signal: {str(e)}",
                pair=pair,
                mode=mode,
                priority="HIGH"
            )
        
        return None
    
    def _process_otl_signal(self, candles: List[CandleData], pair: str, otl_direction: str, 
                           mode_config: Dict, today: str) -> Optional[SignalData]:
        """Process OTL breakout signal"""
        try:
            current = candles[-1]
            entry_price = current.close
            
            # Log pattern detection
            self.trading_logger.log_pattern_detection(
                pair, "OTL Breakout", True, 
                {"Mode": "SWING"}, 
                "SWING", confidence=0.90
            )
            
            # Calculate metrics
            strength = self.calculate_strength(candles, pair, "SWING")
            rr_ratio, stop_loss, take_profit = self.calculate_risk_reward(entry_price, otl_direction, candles, "SWING")
            
            # Validate signal
            if strength >= mode_config['min_strength'] and rr_ratio >= mode_config['min_risk_reward']:
                signal = SignalData(
                    pair=pair,
                    direction=SignalType.BUY if otl_direction == SignalType.BULLISH else SignalType.SELL,
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
                
                # Log risk management
                self.trading_logger.log_risk_management(
                    pair, "ENTRY", {
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "risk_reward": rr_ratio,
                        "strength": strength
                    }, "SWING"
                )
                
                return signal
            else:
                self.trading_logger.log_trading_alert(
                    "FILTER_FAILED",
                    f"Strength/R:R insufficient - Strength: {strength:.2f}, R:R: {rr_ratio:.2f}",
                    pair=pair,
                    mode="SWING"
                )
            
        except Exception as e:
            self.trading_logger.log_trading_alert(
                "ERROR",
                f"Error processing OTL signal: {str(e)}",
                pair=pair,
                mode="SWING",
                priority="HIGH"
            )
        
        return None

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