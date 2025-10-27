import logging
import os
from datetime import datetime
from typing import Dict, Any
import json

class ArifSignalLogger:
    """Mode-specific logging system for Arif Signal"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging directories and handlers"""
        # Create log directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Create subdirectories for different log types
        subdirs = ['signals', 'patterns', 'filters', 'technical', 'performance', 'system', 'errors']
        for subdir in subdirs:
            os.makedirs(os.path.join(self.log_dir, subdir), exist_ok=True)
        
        # Setup loggers
        self.setup_signal_logger()
        self.setup_pattern_logger()
        self.setup_filter_logger()
        self.setup_technical_logger()
        self.setup_performance_logger()
        self.setup_system_logger()
        self.setup_error_logger()
    
    def setup_signal_logger(self):
        """Setup signal logger"""
        self.signal_logger = logging.getLogger('arif_signals')
        self.signal_logger.setLevel(logging.INFO)
        
        # File handler
        signal_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'signals', f'signals_{datetime.now().strftime("%Y%m%d")}.log')
        )
        signal_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        signal_handler.setFormatter(formatter)
        
        self.signal_logger.addHandler(signal_handler)
        self.signal_logger.propagate = False
    
    def setup_pattern_logger(self):
        """Setup pattern logger"""
        self.pattern_logger = logging.getLogger('arif_patterns')
        self.pattern_logger.setLevel(logging.DEBUG)
        
        # File handler
        pattern_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'patterns', f'patterns_{datetime.now().strftime("%Y%m%d")}.log')
        )
        pattern_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        pattern_handler.setFormatter(formatter)
        
        self.pattern_logger.addHandler(pattern_handler)
        self.pattern_logger.propagate = False
    
    def setup_filter_logger(self):
        """Setup filter logger"""
        self.filter_logger = logging.getLogger('arif_filters')
        self.filter_logger.setLevel(logging.DEBUG)
        
        # File handler
        filter_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'filters', f'filters_{datetime.now().strftime("%Y%m%d")}.log')
        )
        filter_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        filter_handler.setFormatter(formatter)
        
        self.filter_logger.addHandler(filter_handler)
        self.filter_logger.propagate = False
    
    def setup_technical_logger(self):
        """Setup technical analysis logger"""
        self.technical_logger = logging.getLogger('arif_technical')
        self.technical_logger.setLevel(logging.DEBUG)
        
        # File handler
        technical_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'technical', f'technical_{datetime.now().strftime("%Y%m%d")}.log')
        )
        technical_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        technical_handler.setFormatter(formatter)
        
        self.technical_logger.addHandler(technical_handler)
        self.technical_logger.propagate = False
    
    def setup_performance_logger(self):
        """Setup performance logger"""
        self.performance_logger = logging.getLogger('arif_performance')
        self.performance_logger.setLevel(logging.INFO)
        
        # File handler
        performance_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'performance', f'performance_{datetime.now().strftime("%Y%m%d")}.log')
        )
        performance_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        performance_handler.setFormatter(formatter)
        
        self.performance_logger.addHandler(performance_handler)
        self.performance_logger.propagate = False
    
    def setup_system_logger(self):
        """Setup system logger"""
        self.system_logger = logging.getLogger('arif_system')
        self.system_logger.setLevel(logging.INFO)
        
        # File handler
        system_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'system', f'system_{datetime.now().strftime("%Y%m%d")}.log')
        )
        system_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        system_handler.setFormatter(formatter)
        
        self.system_logger.addHandler(system_handler)
        self.system_logger.propagate = False
    
    def setup_error_logger(self):
        """Setup error logger"""
        self.error_logger = logging.getLogger('arif_errors')
        self.error_logger.setLevel(logging.ERROR)
        
        # File handler
        error_handler = logging.FileHandler(
            os.path.join(self.log_dir, 'errors', f'errors_{datetime.now().strftime("%Y%m%d")}.log')
        )
        error_handler.setLevel(logging.ERROR)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        error_handler.setFormatter(formatter)
        
        self.error_logger.addHandler(error_handler)
        self.error_logger.propagate = False

    # Mode-Specific Logging Methods
    def log_signal_generated(self, signal_data: Dict, mode: str = "SCALPING"):
        """Log signal generation with mode-specific formatting"""
        try:
            if mode == "SCALPING":
                self.signal_logger.info("🚀 SCALPING SIGNAL: {} | {} | Entry: {:.4f} | SL: {:.4f} | TP: {:.4f} | Strength: {:.2f} | R:R: {:.2f}".format(
                    signal_data.get('pair', 'N/A'),
                    signal_data.get('direction', 'N/A'),
                    signal_data.get('entry_price', 0),
                    signal_data.get('stop_loss', 0),
                    signal_data.get('take_profit', 0),
                    signal_data.get('strength', 0),
                    signal_data.get('risk_reward', 0)
                ))
            else:  # SWING mode
                self.signal_logger.info("📈 SWING SIGNAL: {} | {} | Entry: {:.4f} | SL: {:.4f} | TP: {:.4f} | Strength: {:.2f} | R:R: {:.2f}".format(
                    signal_data.get('pair', 'N/A'),
                    signal_data.get('direction', 'N/A'),
                    signal_data.get('entry_price', 0),
                    signal_data.get('stop_loss', 0),
                    signal_data.get('take_profit', 0),
                    signal_data.get('strength', 0),
                    signal_data.get('risk_reward', 0)
                ))
        except Exception as e:
            self.error_logger.error("Error logging signal generation: {}".format(str(e)))

    def log_pattern_detection(self, pair: str, pattern: str, detected: bool, details: Dict = None, mode: str = "SCALPING"):
        """Log pattern detection with mode-specific context"""
        try:
            if mode == "SCALPING":
                if detected:
                    self.pattern_logger.info("⚡ SCALPING PATTERN: {} | {} | {}".format(
                        pair, pattern, details or {}
                    ))
                else:
                    self.pattern_logger.debug("⚡ SCALPING CHECK: {} | {} | Not detected".format(
                        pair, pattern
                    ))
            else:  # SWING mode
                if detected:
                    self.pattern_logger.info("📊 SWING PATTERN: {} | {} | {}".format(
                        pair, pattern, details or {}
                    ))
                else:
                    self.pattern_logger.debug("📊 SWING CHECK: {} | {} | Not detected".format(
                        pair, pattern
                    ))
        except Exception as e:
            self.error_logger.error("Error logging pattern detection: {}".format(str(e)))

    def log_filter_result(self, pair: str, filter_name: str, passed: bool, reason: str, mode: str = "SCALPING"):
        """Log filter results with mode-specific context"""
        try:
            if mode == "SCALPING":
                if passed:
                    self.filter_logger.debug("⚡ SCALPING FILTER: {} | {} | ✅ PASSED | {}".format(
                        pair, filter_name, reason
                    ))
                else:
                    self.filter_logger.info("⚡ SCALPING FILTER: {} | {} | ❌ FAILED | {}".format(
                        pair, filter_name, reason
                    ))
            else:  # SWING mode
                if passed:
                    self.filter_logger.debug("📊 SWING FILTER: {} | {} | ✅ PASSED | {}".format(
                        pair, filter_name, reason
                    ))
                else:
                    self.filter_logger.info("📊 SWING FILTER: {} | {} | ❌ FAILED | {}".format(
                        pair, filter_name, reason
                    ))
        except Exception as e:
            self.error_logger.error("Error logging filter result: {}".format(str(e)))

    def log_signal_filtered(self, pair: str, reason: str, details: Dict = None, mode: str = "SCALPING"):
        """Log signal filtering with mode-specific context"""
        try:
            if mode == "SCALPING":
                self.signal_logger.info("⚡ SCALPING FILTERED: {} | {} | {}".format(
                    pair, reason, details or {}
                ))
            else:  # SWING mode
                self.signal_logger.info("📊 SWING FILTERED: {} | {} | {}".format(
                    pair, reason, details or {}
                ))
        except Exception as e:
            self.error_logger.error("Error logging signal filtered: {}".format(str(e)))

    def log_technical_analysis(self, pair: str, analysis_data: Dict, mode: str = "SCALPING"):
        """Log technical analysis results with mode-specific formatting"""
        try:
            if mode == "SCALPING":
                # Log key scalping indicators
                rsi = analysis_data.get('rsi', 0)
                volume_ratio = analysis_data.get('volume_ratio', 0)
                trend = analysis_data.get('trend', 'N/A')
                
                self.technical_logger.debug("⚡ SCALPING TA: {} | RSI: {:.2f} | Volume: {:.2f}x | Trend: {} | Support: {} | Resistance: {}".format(
                    pair, rsi, volume_ratio, trend,
                    len(analysis_data.get('support_levels', [])),
                    len(analysis_data.get('resistance_levels', []))
                ))
            else:  # SWING mode
                # Log key swing indicators
                ema_trend = analysis_data.get('ema_analysis', {}).get('trend_alignment', 'N/A')
                macd_bullish = analysis_data.get('macd_analysis', {}).get('macd_bullish', False)
                cloud_bullish = analysis_data.get('ichimoku_analysis', {}).get('cloud_bullish', False)
                trend_context = analysis_data.get('trend_context', 'N/A')
                
                self.technical_logger.debug("📊 SWING TA: {} | EMA: {} | MACD: {} | Cloud: {} | Trend: {} | MFI: {:.2f}".format(
                    pair, ema_trend, "BULL" if macd_bullish else "BEAR",
                    "BULL" if cloud_bullish else "BEAR", trend_context,
                    analysis_data.get('volume_analysis', {}).get('mfi', 0)
                ))
        except Exception as e:
            self.error_logger.error("Error logging technical analysis: {}".format(str(e)))

    def log_mode_switch(self, from_mode: str, to_mode: str, reason: str = None):
        """Log mode switching"""
        try:
            self.system_logger.info("🔄 MODE SWITCH: {} → {} | {}".format(
                from_mode, to_mode, reason or "Manual switch"
            ))
        except Exception as e:
            self.error_logger.error("Error logging mode switch: {}".format(str(e)))

    def log_mode_performance(self, mode: str, stats: Dict):
        """Log mode-specific performance statistics"""
        try:
            if mode == "SCALPING":
                self.performance_logger.info("⚡ SCALPING STATS: Signals: {} | Win Rate: {:.1f}% | Avg R:R: {:.2f} | Total PnL: {:.2f}".format(
                    stats.get('total_signals', 0),
                    stats.get('win_rate', 0) * 100,
                    stats.get('avg_risk_reward', 0),
                    stats.get('total_pnl', 0)
                ))
            else:  # SWING mode
                self.performance_logger.info("📊 SWING STATS: Signals: {} | Win Rate: {:.1f}% | Avg R:R: {:.2f} | Total PnL: {:.2f}".format(
                    stats.get('total_signals', 0),
                    stats.get('win_rate', 0) * 100,
                    stats.get('avg_risk_reward', 0),
                    stats.get('total_pnl', 0)
                ))
        except Exception as e:
            self.error_logger.error("Error logging mode performance: {}".format(str(e)))

    def log_error(self, component: str, message: str, pair: str = None, mode: str = None):
        """Log errors with context"""
        try:
            context = f" | Pair: {pair}" if pair else ""
            context += f" | Mode: {mode}" if mode else ""
            self.error_logger.error(f"ERROR [{component}]: {message}{context}")
        except Exception as e:
            print(f"Logger error: {str(e)}")

    def log_info(self, component: str, message: str, pair: str = None, mode: str = None):
        """Log info messages with context"""
        try:
            context = f" | Pair: {pair}" if pair else ""
            context += f" | Mode: {mode}" if mode else ""
            self.system_logger.info(f"INFO [{component}]: {message}{context}")
        except Exception as e:
            print(f"Logger error: {str(e)}")