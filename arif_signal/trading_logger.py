# trading_logger.py

import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class TradingSignal:
    """Trading signal data structure"""
    pair: str
    direction: str  # BUY/SELL
    entry_price: float
    stop_loss: float
    take_profit: float
    strength: float
    risk_reward: float
    mode: str  # SCALPING/SWING
    timestamp: datetime
    pattern: str  # Sweep/Engulfing/OTL
    volume_ratio: float
    rsi: float
    trend: str

@dataclass
class TradingPerformance:
    """Trading performance metrics"""
    mode: str
    total_signals: int
    winning_signals: int
    losing_signals: int
    win_rate: float
    avg_risk_reward: float
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float

class TradingLogger:
    """Specialized trading logger with trading-specific features"""
    
    def __init__(self, log_dir: str = "trading_logs"):
        self.log_dir = log_dir
        self.setup_trading_logging()
        self.performance_tracker = {}
    
    def setup_trading_logging(self):
        """Setup specialized trading logging structure"""
        # Create trading-specific directories
        trading_dirs = [
            'signals', 'patterns', 'performance', 'risk_management',
            'market_analysis', 'alerts', 'backtest', 'live_trading'
        ]
        
        for subdir in trading_dirs:
            os.makedirs(os.path.join(self.log_dir, subdir), exist_ok=True)
        
        # Setup specialized loggers
        self.setup_signal_logger()
        self.setup_pattern_logger()
        self.setup_performance_logger()
        self.setup_risk_logger()
        self.setup_market_logger()
        self.setup_alert_logger()
    
    def setup_signal_logger(self):
        """Setup signal-specific logger"""
        self.signal_logger = logging.getLogger('trading_signals')
        self.signal_logger.setLevel(logging.INFO)
        
        # Signal file handler
        signal_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'signals', f'signals_{datetime.now().strftime("%Y%m%d")}.json')
        )
        signal_handler.setLevel(logging.INFO)
        
        # Custom formatter for JSON
        formatter = logging.Formatter('%(message)s')
        signal_handler.setFormatter(formatter)
        
        self.signal_logger.addHandler(signal_handler)
        self.signal_logger.propagate = False
    
    def setup_pattern_logger(self):
        """Setup pattern-specific logger"""
        self.pattern_logger = logging.getLogger('trading_patterns')
        self.pattern_logger.setLevel(logging.INFO)
        
        pattern_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'patterns', f'patterns_{datetime.now().strftime("%Y%m%d")}.json')
        )
        pattern_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(message)s')
        pattern_handler.setFormatter(formatter)
        
        self.pattern_logger.addHandler(pattern_handler)
        self.pattern_logger.propagate = False
    
    def setup_performance_logger(self):
        """Setup performance-specific logger"""
        self.performance_logger = logging.getLogger('trading_performance')
        self.performance_logger.setLevel(logging.INFO)
        
        perf_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'performance', f'performance_{datetime.now().strftime("%Y%m%d")}.json')
        )
        perf_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(message)s')
        perf_handler.setFormatter(formatter)
        
        self.performance_logger.addHandler(perf_handler)
        self.performance_logger.propagate = False
    
    def setup_risk_logger(self):
        """Setup risk management logger"""
        self.risk_logger = logging.getLogger('trading_risk')
        self.risk_logger.setLevel(logging.INFO)
        
        risk_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'risk_management', f'risk_{datetime.now().strftime("%Y%m%d")}.json')
        )
        risk_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(message)s')
        risk_handler.setFormatter(formatter)
        
        self.risk_logger.addHandler(risk_handler)
        self.risk_logger.propagate = False
    
    def setup_market_logger(self):
        """Setup market analysis logger"""
        self.market_logger = logging.getLogger('trading_market')
        self.market_logger.setLevel(logging.INFO)
        
        market_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'market_analysis', f'market_{datetime.now().strftime("%Y%m%d")}.json')
        )
        market_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(message)s')
        market_handler.setFormatter(formatter)
        
        self.market_logger.addHandler(market_handler)
        self.market_logger.propagate = False
    
    def setup_alert_logger(self):
        """Setup trading alerts logger"""
        self.alert_logger = logging.getLogger('trading_alerts')
        self.alert_logger.setLevel(logging.INFO)
        
        alert_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'alerts', f'alerts_{datetime.now().strftime("%Y%m%d")}.json')
        )
        alert_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(message)s')
        alert_handler.setFormatter(formatter)
        
        self.alert_logger.addHandler(alert_handler)
        self.alert_logger.propagate = False

    # Trading-Specific Logging Methods
    def log_trading_signal(self, signal: TradingSignal):
        """Log trading signal with rich context"""
        try:
            signal_data = {
                'timestamp': signal.timestamp.isoformat(),
                'pair': signal.pair,
                'mode': signal.mode,
                'direction': signal.direction,
                'entry_price': signal.entry_price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'strength': signal.strength,
                'risk_reward': signal.risk_reward,
                'pattern': signal.pattern,
                'volume_ratio': signal.volume_ratio,
                'rsi': signal.rsi,
                'trend': signal.trend,
                'potential_profit': (signal.take_profit - signal.entry_price) if signal.direction == "BUY" else (signal.entry_price - signal.take_profit),
                'potential_loss': abs(signal.entry_price - signal.stop_loss)
            }
            
            self.signal_logger.info(json.dumps(signal_data))
            
            # Update performance tracker
            self._update_performance_tracker(signal)
            
        except Exception as e:
            print(f"Error logging trading signal: {str(e)}")
    
    def log_pattern_detection(self, pair: str, pattern: str, detected: bool, 
                            details: Dict, mode: str, confidence: float = 0.0):
        """Log pattern detection with trading context"""
        try:
            pattern_data = {
                'timestamp': datetime.now().isoformat(),
                'pair': pair,
                'pattern': pattern,
                'detected': detected,
                'mode': mode,
                'confidence': confidence,
                'details': details,
                'market_conditions': self._get_market_conditions(pair)
            }
            
            self.pattern_logger.info(json.dumps(pattern_data))
            
        except Exception as e:
            print(f"Error logging pattern detection: {str(e)}")
    
    def log_risk_management(self, pair: str, action: str, details: Dict, mode: str):
        """Log risk management actions"""
        try:
            risk_data = {
                'timestamp': datetime.now().isoformat(),
                'pair': pair,
                'action': action,  # ENTRY/EXIT/STOP_LOSS/TAKE_PROFIT
                'mode': mode,
                'details': details,
                'risk_level': self._calculate_risk_level(details)
            }
            
            self.risk_logger.info(json.dumps(risk_data))
            
        except Exception as e:
            print(f"Error logging risk management: {str(e)}")
    
    def log_market_analysis(self, pair: str, analysis: Dict, mode: str):
        """Log market analysis with trading context"""
        try:
            market_data = {
                'timestamp': datetime.now().isoformat(),
                'pair': pair,
                'mode': mode,
                'analysis': analysis,
                'market_sentiment': self._determine_sentiment(analysis),
                'volatility': self._calculate_volatility(analysis),
                'trend_strength': self._calculate_trend_strength(analysis)
            }
            
            self.market_logger.info(json.dumps(market_data))
            
        except Exception as e:
            print(f"Error logging market analysis: {str(e)}")
    
    def log_trading_alert(self, alert_type: str, message: str, pair: str = None, 
                         mode: str = None, priority: str = "MEDIUM"):
        """Log trading alerts"""
        try:
            alert_data = {
                'timestamp': datetime.now().isoformat(),
                'alert_type': alert_type,  # SIGNAL/STOP_LOSS/TAKE_PROFIT/ERROR/WARNING
                'message': message,
                'pair': pair,
                'mode': mode,
                'priority': priority,
                'requires_action': priority in ["HIGH", "CRITICAL"]
            }
            
            self.alert_logger.info(json.dumps(alert_data))
            
        except Exception as e:
            print(f"Error logging trading alert: {str(e)}")
    
    def log_performance_summary(self, mode: str, timeframe: str = "DAILY"):
        """Log performance summary with trading metrics"""
        try:
            if mode not in self.performance_tracker:
                return
            
            stats = self.performance_tracker[mode]
            performance = TradingPerformance(
                mode=mode,
                total_signals=stats.get('total_signals', 0),
                winning_signals=stats.get('winning_signals', 0),
                losing_signals=stats.get('losing_signals', 0),
                win_rate=stats.get('win_rate', 0.0),
                avg_risk_reward=stats.get('avg_risk_reward', 0.0),
                total_pnl=stats.get('total_pnl', 0.0),
                max_drawdown=stats.get('max_drawdown', 0.0),
                sharpe_ratio=stats.get('sharpe_ratio', 0.0),
                profit_factor=stats.get('profit_factor', 0.0)
            )
            
            self.performance_logger.info(json.dumps(asdict(performance)))
            
        except Exception as e:
            print(f"Error logging performance summary: {str(e)}")
    
    def log_error(self, component: str, message: str, pair: str = None, 
                  mode: str = None, error_data: Dict = None):
        """Log detailed error information"""
        try:
            error_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "component": component,
                "message": message,
                "pair": pair,
                "mode": mode,
                "error_data": error_data or {},
                "type": "ERROR"
            }
            
            self.errors_logger.error(json.dumps(error_log, indent=2))
            
        except Exception as e:
            print(f"Error logging error: {str(e)}")
    
    def log_recovery_attempt(self, component: str, recovery_type: str, 
                           success: bool, pair: str = None, mode: str = None):
        """Log recovery attempts"""
        try:
            recovery_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "component": component,
                "recovery_type": recovery_type,
                "success": success,
                "pair": pair,
                "mode": mode,
                "type": "RECOVERY"
            }
            
            self.alerts_logger.info(json.dumps(recovery_log, indent=2))
            
        except Exception as e:
            print(f"Error logging recovery: {str(e)}")
    
    def log_system_health(self, health_data: Dict):
        """Log system health metrics"""
        try:
            health_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "health_data": health_data,
                "type": "SYSTEM_HEALTH"
            }
            
            self.system_logger.info(json.dumps(health_log, indent=2))
            
        except Exception as e:
            print(f"Error logging system health: {str(e)}")
    
    # Helper methods
    def _update_performance_tracker(self, signal: TradingSignal):
        """Update performance tracking"""
        mode = signal.mode
        if mode not in self.performance_tracker:
            self.performance_tracker[mode] = {
                'total_signals': 0,
                'winning_signals': 0,
                'losing_signals': 0,
                'total_pnl': 0.0,
                'risk_rewards': []
            }
        
        self.performance_tracker[mode]['total_signals'] += 1
        self.performance_tracker[mode]['risk_rewards'].append(signal.risk_reward)
        
        # Calculate win rate (simplified)
        if signal.risk_reward > 1.0:
            self.performance_tracker[mode]['winning_signals'] += 1
        
        # Calculate average risk/reward
        self.performance_tracker[mode]['avg_risk_reward'] = sum(
            self.performance_tracker[mode]['risk_rewards']
        ) / len(self.performance_tracker[mode]['risk_rewards'])
        
        # Calculate win rate
        total = self.performance_tracker[mode]['total_signals']
        wins = self.performance_tracker[mode]['winning_signals']
        self.performance_tracker[mode]['win_rate'] = wins / total if total > 0 else 0.0
    
    def _get_market_conditions(self, pair: str, analysis: dict = None) -> Dict:
        """Get current market conditions based on analysis data"""
        if not analysis:
            return {
                'volatility': 'UNKNOWN',
                'trend': 'UNKNOWN',
                'volume': 'UNKNOWN',
                'spread': 'UNKNOWN'
            }
        closes = analysis.get('closes', [])
        volumes = analysis.get('volumes', [])
        if closes and len(closes) > 10:
            import numpy as np
            std = float(np.std(closes[-10:]))
            volatility = 'HIGH' if std > 0.01 * closes[-1] else 'LOW' if std < 0.002 * closes[-1] else 'MEDIUM'
        else:
            volatility = 'UNKNOWN'
        trend = analysis.get('trend', 'UNKNOWN')
        if volumes and len(volumes) > 10:
            avg_vol = sum(volumes[-10:]) / 10
            volume = 'HIGH' if volumes[-1] > 1.5 * avg_vol else 'LOW' if volumes[-1] < 0.7 * avg_vol else 'NORMAL'
        else:
            volume = 'UNKNOWN'
        spread = 'TIGHT'
        if closes and len(closes) > 1:
            spread_val = abs(closes[-1] - closes[-2]) / closes[-1]
            spread = 'WIDE' if spread_val > 0.005 else 'TIGHT'
        return {
            'volatility': volatility,
            'trend': trend,
            'volume': volume,
            'spread': spread
        }

    def _calculate_risk_level(self, details: Dict) -> str:
        """Calculate risk level based on risk/reward and stoploss size"""
        rr = details.get('risk_reward', 1.0)
        stop = details.get('stop_loss', 0.0)
        entry = details.get('entry_price', 0.0)
        if entry and stop:
            risk_pct = abs(entry - stop) / entry
            if rr >= 2.5 and risk_pct < 0.01:
                return 'LOW'
            elif rr >= 1.5 and risk_pct < 0.02:
                return 'MEDIUM'
            else:
                return 'HIGH'
        return 'UNKNOWN'

    def _determine_sentiment(self, analysis: Dict) -> str:
        """Determine market sentiment from trend and momentum indicators"""
        trend = analysis.get('trend', 'UNKNOWN')
        rsi = analysis.get('rsi', 50)
        macd = analysis.get('macd_line', 0)
        if trend == 'BULLISH' and rsi > 60 and macd > 0:
            return 'BULLISH'
        elif trend == 'BEARISH' and rsi < 40 and macd < 0:
            return 'BEARISH'
        else:
            return 'NEUTRAL'

    def _calculate_volatility(self, analysis: Dict) -> float:
        """Calculate volatility as std dev of close prices (normalized)"""
        closes = analysis.get('closes', [])
        if closes and len(closes) > 10:
            import numpy as np
            return float(np.std(closes[-10:]) / closes[-1])
        return 0.0

    def _calculate_trend_strength(self, analysis: Dict) -> float:
        """Calculate trend strength based on EMA slope and MACD"""
        ema_20 = analysis.get('ema_20', 0)
        ema_50 = analysis.get('ema_50', 0)
        ema_200 = analysis.get('ema_200', 0)
        closes = analysis.get('closes', [])
        macd = analysis.get('macd_line', 0)
        if closes and len(closes) > 20:
            slope = (closes[-1] - closes[-20]) / closes[-20]
            macd_strength = abs(macd) / (abs(closes[-1]) + 1e-6)
            return min(1.0, max(0.0, 0.5 * abs(slope) + 0.5 * macd_strength))
        return 0.0