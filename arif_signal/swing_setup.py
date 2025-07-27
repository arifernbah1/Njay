import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

@dataclass
class SwingSetup:
    """Swing trading setup data structure"""
    pair: str
    setup_type: str  # BREAKOUT/REVERSAL/CONTINUATION
    timeframe: str  # 1h/4h/Daily
    entry_zone: Tuple[float, float]  # (min_entry, max_entry)
    stop_loss: float
    take_profit: List[float]  # Multiple targets
    risk_reward: float
    confidence: float  # 0.0 - 1.0
    setup_strength: float  # 0.0 - 5.0
    market_structure: str  # BULLISH/BEARISH/SIDEWAYS
    key_levels: Dict[str, float]
    volume_profile: Dict[str, float]
    setup_date: datetime
    expiry_date: datetime
    status: str  # ACTIVE/EXPIRED/TRIGGERED
    notes: str

class SwingSetupManager:
    """Manages swing trading setups with comprehensive pre-analysis"""
    
    def __init__(self, trading_logger):
        self.logger = trading_logger
        self.active_setups = {}
        self.setup_history = []
        self.setup_config = {
            'min_confidence': 0.75,
            'min_strength': 4.0,
            'max_setups_per_pair': 2,
            'setup_expiry_hours': 48,
            'min_risk_reward': 2.5
        }
    
    def analyze_swing_setup(self, candles: List, pair: str) -> Optional[SwingSetup]:
        """Comprehensive swing setup analysis"""
        try:
            if len(candles) < 200:  # Need more data for swing analysis
                return None
            
            # 1. Market Structure Analysis
            market_structure = self._analyze_market_structure(candles)
            
            # 2. Key Levels Identification
            key_levels = self._identify_key_levels(candles)
            
            # 3. Volume Profile Analysis
            volume_profile = self._analyze_volume_profile(candles)
            
            # 4. Setup Pattern Detection
            setup_pattern = self._detect_setup_pattern(candles, market_structure)
            
            if not setup_pattern:
                return None
            
            # 5. Entry Zone Calculation
            entry_zone = self._calculate_entry_zone(candles, setup_pattern, key_levels)
            
            # 6. Risk Management Setup
            stop_loss, take_profits = self._calculate_risk_management(
                candles, setup_pattern, entry_zone, key_levels
            )
            
            # 7. Setup Strength & Confidence
            strength, confidence = self._calculate_setup_metrics(
                candles, setup_pattern, market_structure, volume_profile
            )
            
            # 8. Validate Setup
            if not self._validate_setup(strength, confidence, stop_loss, take_profits):
                return None
            
            # Create Swing Setup
            setup = SwingSetup(
                pair=pair,
                setup_type=setup_pattern['type'],
                timeframe="1h",
                entry_zone=entry_zone,
                stop_loss=stop_loss,
                take_profit=take_profits,
                risk_reward=setup_pattern['risk_reward'],
                confidence=confidence,
                setup_strength=strength,
                market_structure=market_structure,
                key_levels=key_levels,
                volume_profile=volume_profile,
                setup_date=datetime.now(),
                expiry_date=datetime.now() + timedelta(hours=self.setup_config['setup_expiry_hours']),
                status="ACTIVE",
                notes=setup_pattern['notes']
            )
            
            # Log setup creation
            self.logger.log_trading_alert(
                "SWING_SETUP_CREATED",
                f"Swing setup created for {pair}: {setup_pattern['type']}",
                pair=pair,
                mode="SWING",
                priority="HIGH"
            )
            
            return setup
            
        except Exception as e:
            self.logger.log_trading_alert(
                "ERROR",
                f"Error analyzing swing setup for {pair}: {str(e)}",
                pair=pair,
                mode="SWING",
                priority="CRITICAL"
            )
            return None
    
    def _analyze_market_structure(self, candles: List) -> str:
        """Analyze overall market structure"""
        try:
            # Get higher timeframe trend (4h)
            highs = [c.high for c in candles[-50:]]
            lows = [c.low for c in candles[-50:]]
            
            # Higher highs and higher lows = BULLISH
            # Lower highs and lower lows = BEARISH
            # Mixed = SIDEWAYS
            
            recent_highs = highs[-10:]
            recent_lows = lows[-10:]
            
            # Check for higher highs
            higher_highs = all(recent_highs[i] >= recent_highs[i-1] for i in range(1, len(recent_highs)))
            higher_lows = all(recent_lows[i] >= recent_lows[i-1] for i in range(1, len(recent_lows)))
            
            if higher_highs and higher_lows:
                return "BULLISH"
            elif not higher_highs and not higher_lows:
                return "BEARISH"
            else:
                return "SIDEWAYS"
                
        except Exception as e:
            return "SIDEWAYS"
    
    def _identify_key_levels(self, candles: List) -> Dict[str, float]:
        """Identify key support/resistance levels"""
        try:
            levels = {}
            
            # Pivot Points
            current = candles[-1]
            high = max(c.high for c in candles[-20:])
            low = min(c.low for c in candles[-20:])
            
            # Pivot Point
            pp = (high + low + current.close) / 3
            
            # Support and Resistance
            r1 = 2 * pp - low
            r2 = pp + (high - low)
            s1 = 2 * pp - high
            s2 = pp - (high - low)
            
            levels['pivot'] = pp
            levels['resistance_1'] = r1
            levels['resistance_2'] = r2
            levels['support_1'] = s1
            levels['support_2'] = s2
            
            # Recent swing highs and lows
            swing_highs = []
            swing_lows = []
            
            for i in range(2, len(candles) - 2):
                if (candles[i].high > candles[i-1].high and 
                    candles[i].high > candles[i-2].high and
                    candles[i].high > candles[i+1].high and
                    candles[i].high > candles[i+2].high):
                    swing_highs.append(candles[i].high)
                
                if (candles[i].low < candles[i-1].low and 
                    candles[i].low < candles[i-2].low and
                    candles[i].low < candles[i+1].low and
                    candles[i].low < candles[i+2].low):
                    swing_lows.append(candles[i].low)
            
            if swing_highs:
                levels['recent_swing_high'] = max(swing_highs[-3:])  # Last 3 swing highs
            if swing_lows:
                levels['recent_swing_low'] = min(swing_lows[-3:])  # Last 3 swing lows
            
            return levels
            
        except Exception as e:
            return {}
    
    def _analyze_volume_profile(self, candles: List) -> Dict[str, float]:
        """Analyze volume profile for swing trading"""
        try:
            profile = {}
            
            # Volume analysis
            recent_volumes = [c.volume for c in candles[-20:]]
            avg_volume = sum(recent_volumes) / len(recent_volumes)
            current_volume = candles[-1].volume
            
            profile['avg_volume'] = avg_volume
            profile['current_volume'] = current_volume
            profile['volume_ratio'] = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Volume trend
            volume_trend = sum(1 for i in range(1, len(recent_volumes)) 
                             if recent_volumes[i] > recent_volumes[i-1])
            profile['volume_trend'] = volume_trend / (len(recent_volumes) - 1)
            
            # High volume periods
            high_volume_candles = [c for c in candles[-20:] if c.volume > avg_volume * 1.5]
            profile['high_volume_periods'] = len(high_volume_candles)
            
            return profile
            
        except Exception as e:
            return {}
    
    def _detect_setup_pattern(self, candles: List, market_structure: str) -> Optional[Dict]:
        """Detect swing setup patterns"""
        try:
            current = candles[-1]
            key_levels = self._identify_key_levels(candles)
            
            # 1. Breakout Setup
            if self._detect_breakout_setup(candles, key_levels):
                return {
                    'type': 'BREAKOUT',
                    'risk_reward': 3.0,
                    'notes': 'Price breaking key resistance/support level'
                }
            
            # 2. Reversal Setup
            if self._detect_reversal_setup(candles, market_structure):
                return {
                    'type': 'REVERSAL',
                    'risk_reward': 2.5,
                    'notes': 'Potential trend reversal at key level'
                }
            
            # 3. Continuation Setup
            if self._detect_continuation_setup(candles, market_structure):
                return {
                    'type': 'CONTINUATION',
                    'risk_reward': 2.0,
                    'notes': 'Trend continuation after pullback'
                }
            
            return None
            
        except Exception as e:
            return None
    
    def _detect_breakout_setup(self, candles: List, key_levels: Dict) -> bool:
        """Detect breakout setup"""
        try:
            current = candles[-1]
            
            # Check for resistance breakout
            if 'resistance_1' in key_levels:
                resistance = key_levels['resistance_1']
                if (current.close > resistance and 
                    current.volume > sum(c.volume for c in candles[-5:]) / 5 * 1.2):
                    return True
            
            # Check for support breakdown
            if 'support_1' in key_levels:
                support = key_levels['support_1']
                if (current.close < support and 
                    current.volume > sum(c.volume for c in candles[-5:]) / 5 * 1.2):
                    return True
            
            return False
            
        except Exception as e:
            return False
    
    def _detect_reversal_setup(self, candles: List, market_structure: str) -> bool:
        """Detect reversal setup"""
        try:
            # Look for reversal patterns at key levels
            current = candles[-1]
            key_levels = self._identify_key_levels(candles)
            
            # Bullish reversal at support
            if market_structure == "BEARISH" and 'support_1' in key_levels:
                support = key_levels['support_1']
                if (abs(current.low - support) / support < 0.01 and  # Near support
                    current.close > current.open):  # Bullish candle
                    return True
            
            # Bearish reversal at resistance
            if market_structure == "BULLISH" and 'resistance_1' in key_levels:
                resistance = key_levels['resistance_1']
                if (abs(current.high - resistance) / resistance < 0.01 and  # Near resistance
                    current.close < current.open):  # Bearish candle
                    return True
            
            return False
            
        except Exception as e:
            return False
    
    def _detect_continuation_setup(self, candles: List, market_structure: str) -> bool:
        """Detect continuation setup"""
        try:
            # Look for continuation patterns
            if market_structure == "BULLISH":
                # Bullish continuation after pullback
                recent_lows = [c.low for c in candles[-10:]]
                if min(recent_lows) > min(recent_lows[:-5]):  # Higher lows
                    return True
            
            elif market_structure == "BEARISH":
                # Bearish continuation after bounce
                recent_highs = [c.high for c in candles[-10:]]
                if max(recent_highs) < max(recent_highs[:-5]):  # Lower highs
                    return True
            
            return False
            
        except Exception as e:
            return False
    
    def _calculate_entry_zone(self, candles: List, setup_pattern: Dict, key_levels: Dict) -> Tuple[float, float]:
        """Calculate entry zone for swing setup"""
        try:
            current = candles[-1]
            
            if setup_pattern['type'] == 'BREAKOUT':
                # Entry zone around breakout level
                if 'resistance_1' in key_levels:
                    resistance = key_levels['resistance_1']
                    return (resistance * 0.995, resistance * 1.005)
                elif 'support_1' in key_levels:
                    support = key_levels['support_1']
                    return (support * 0.995, support * 1.005)
            
            elif setup_pattern['type'] == 'REVERSAL':
                # Entry zone at reversal level
                if 'support_1' in key_levels:
                    support = key_levels['support_1']
                    return (support * 0.99, support * 1.01)
                elif 'resistance_1' in key_levels:
                    resistance = key_levels['resistance_1']
                    return (resistance * 0.99, resistance * 1.01)
            
            # Default entry zone
            return (current.close * 0.99, current.close * 1.01)
            
        except Exception as e:
            current = candles[-1]
            return (current.close * 0.99, current.close * 1.01)
    
    def _calculate_risk_management(self, candles: List, setup_pattern: Dict, 
                                 entry_zone: Tuple[float, float], key_levels: Dict) -> Tuple[float, List[float]]:
        """Calculate stop loss and take profit levels"""
        try:
            entry_price = (entry_zone[0] + entry_zone[1]) / 2
            
            # Calculate stop loss
            if setup_pattern['type'] == 'BREAKOUT':
                if 'resistance_1' in key_levels:
                    stop_loss = key_levels['resistance_1'] * 0.98  # Below breakout level
                else:
                    stop_loss = entry_price * 0.97
            else:
                stop_loss = entry_price * 0.97  # 3% stop loss
            
            # Calculate take profit levels
            risk = abs(entry_price - stop_loss)
            
            if setup_pattern['type'] == 'BREAKOUT':
                take_profits = [
                    entry_price + (risk * 2),  # 2R
                    entry_price + (risk * 3),  # 3R
                    entry_price + (risk * 5)   # 5R
                ]
            else:
                take_profits = [
                    entry_price + (risk * 1.5),  # 1.5R
                    entry_price + (risk * 2.5),  # 2.5R
                    entry_price + (risk * 4)     # 4R
                ]
            
            return stop_loss, take_profits
            
        except Exception as e:
            entry_price = (entry_zone[0] + entry_zone[1]) / 2
            stop_loss = entry_price * 0.97
            risk = abs(entry_price - stop_loss)
            take_profits = [entry_price + (risk * 2), entry_price + (risk * 3)]
            return stop_loss, take_profits
    
    def _calculate_setup_metrics(self, candles: List, setup_pattern: Dict, 
                               market_structure: str, volume_profile: Dict) -> Tuple[float, float]:
        """Calculate setup strength and confidence"""
        try:
            strength = 0.0
            confidence = 0.0
            
            # Base strength from setup type
            if setup_pattern['type'] == 'BREAKOUT':
                strength += 2.0
            elif setup_pattern['type'] == 'REVERSAL':
                strength += 1.5
            elif setup_pattern['type'] == 'CONTINUATION':
                strength += 1.0
            
            # Market structure alignment
            if market_structure in ['BULLISH', 'BEARISH']:
                strength += 1.0
                confidence += 0.2
            
            # Volume confirmation
            if volume_profile.get('volume_ratio', 1.0) > 1.2:
                strength += 0.5
                confidence += 0.1
            
            # Recent price action
            recent_candles = candles[-5:]
            bullish_candles = sum(1 for c in recent_candles if c.close > c.open)
            if bullish_candles >= 3:
                strength += 0.5
                confidence += 0.1
            
            # Normalize confidence to 0-1 range
            confidence = min(confidence + 0.5, 1.0)  # Base 0.5 + bonuses
            
            return strength, confidence
            
        except Exception as e:
            return 2.0, 0.6  # Default values
    
    def _validate_setup(self, strength: float, confidence: float, 
                       stop_loss: float, take_profits: List[float]) -> bool:
        """Validate if setup meets criteria"""
        try:
            # Check minimum requirements
            if strength < self.setup_config['min_strength']:
                return False
            
            if confidence < self.setup_config['min_confidence']:
                return False
            
            # Check risk/reward
            if take_profits and stop_loss:
                risk = abs(take_profits[0] - stop_loss)
                if risk > 0:
                    rr_ratio = abs(take_profits[0] - stop_loss) / risk
                    if rr_ratio < self.setup_config['min_risk_reward']:
                        return False
            
            return True
            
        except Exception as e:
            return False
    
    def add_setup(self, setup: SwingSetup):
        """Add new setup to active setups and send Telegram alert"""
        try:
            if setup.pair not in self.active_setups:
                self.active_setups[setup.pair] = []
            
            # Check maximum setups per pair
            if len(self.active_setups[setup.pair]) >= self.setup_config['max_setups_per_pair']:
                # Remove oldest setup
                self.active_setups[setup.pair].pop(0)
            
            self.active_setups[setup.pair].append(setup)
            
            # Log setup addition
            self.logger.log_trading_alert(
                "SWING_SETUP_ADDED",
                f"Added {setup.setup_type} setup for {setup.pair}",
                pair=setup.pair,
                mode="SWING"
            )
            
            # Send Telegram alert for new setup
            if hasattr(self, 'notification_service'):
                setup_data = {
                    'pair': setup.pair,
                    'setup_type': setup.setup_type,
                    'confidence': setup.confidence,
                    'setup_strength': setup.setup_strength,
                    'entry_zone': setup.entry_zone,
                    'stop_loss': setup.stop_loss,
                    'take_profit': setup.take_profit,
                    'risk_reward': setup.risk_reward,
                    'market_structure': setup.market_structure,
                    'notes': setup.notes
                }
                self.notification_service.send_swing_setup_alert(setup_data, "SWING")
            
        except Exception as e:
            self.logger.log_trading_alert(
                "ERROR",
                f"Error adding setup: {str(e)}",
                pair=setup.pair,
                mode="SWING",
                priority="HIGH"
            )
    
    def get_active_setups(self, pair: str = None) -> List[SwingSetup]:
        """Get active setups for pair or all pairs"""
        try:
            if pair:
                return self.active_setups.get(pair, [])
            else:
                all_setups = []
                for setups in self.active_setups.values():
                    all_setups.extend(setups)
                return all_setups
        except Exception as e:
            return []
    
    def cleanup_expired_setups(self):
        """Remove expired setups"""
        try:
            current_time = datetime.now()
            expired_count = 0
            
            for pair in list(self.active_setups.keys()):
                active_setups = self.active_setups[pair]
                valid_setups = []
                
                for setup in active_setups:
                    if setup.expiry_date > current_time:
                        valid_setups.append(setup)
                    else:
                        setup.status = "EXPIRED"
                        self.setup_history.append(setup)
                        expired_count += 1
                
                if valid_setups:
                    self.active_setups[pair] = valid_setups
                else:
                    del self.active_setups[pair]
            
            if expired_count > 0:
                self.logger.log_trading_alert(
                    "SWING_SETUP_CLEANUP",
                    f"Cleaned up {expired_count} expired setups",
                    mode="SWING"
                )
                
        except Exception as e:
            self.logger.log_trading_alert(
                "ERROR",
                f"Error cleaning up expired setups: {str(e)}",
                mode="SWING",
                priority="HIGH"
            )