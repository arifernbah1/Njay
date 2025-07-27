# main.py

# --- Import classes from other files ---
from arif_signal.data_manager import DataManager
from arif_signal.processor import SignalProcessor
from arif_signal.config import ConfigManager
from arif_signal.trading_logger import TradingLogger, TradingSignal
from arif_signal.notifications import NotificationService
from arif_signal.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from arif_signal.models import SignalData, SignalType
from datetime import datetime
import time
import sys

class ArifSignalApp:
    """Main application class with comprehensive error handling"""
    
    def __init__(self):
        try:
            self.config = ConfigManager()
            self.pairs = self.config.get_pairs()
            self.current_mode = "SCALPING"  # Default mode
            
            # Initialize specialized Trading Logger
            self.trading_logger = TradingLogger("trading_logs")
            
            # Initialize Telegram notification service
            self.notification_service = NotificationService(
                bot_token=self.config.get_telegram_token(),
                chat_id=self.config.get_telegram_chat_id(),
                trading_logger=self.trading_logger
            )
            
            # Initialize Error Handler
            self.error_handler = ErrorHandler(self.trading_logger, self.notification_service)
            
            # Initialize components with error handling
            self.data_manager = DataManager(self.trading_logger)
            self.signal_processor = SignalProcessor(self.trading_logger)
            
            # Set notification service for swing setup manager
            self.signal_processor.swing_setup_manager.set_notification_service(self.notification_service)
            
            # Log system startup
            self.trading_logger.log_trading_alert(
                "SYSTEM_START", 
                "Arif Signal Trading System initialized with comprehensive error handling",
                priority="HIGH"
            )
            
            # Send startup notification to Telegram
            self.notification_service.send_system_alert(
                "SYSTEM_START",
                "Arif Signal Trading System started successfully with Error Handling & Swing Setup integration",
                "HIGH"
            )
            
        except Exception as e:
            print(f"Critical error during initialization: {str(e)}")
            sys.exit(1)
    
    def run(self):
        """Main application loop with comprehensive error handling"""
        try:
            self.trading_logger.log_trading_alert(
                "SYSTEM_RUNNING",
                "Trading system is now running",
                priority="HIGH"
            )
            
            while True:
                try:
                    # Check for mode switch
                    new_mode = self.check_mode_switch()
                    if new_mode != self.current_mode:
                        self.current_mode = new_mode
                        self.trading_logger.log_trading_alert(
                            "MODE_SWITCH",
                            f"Switched to {self.current_mode} mode",
                            mode=self.current_mode,
                            priority="HIGH"
                        )
                    
                    # Process signals for current mode
                    signals = self.process_signals_for_mode(self.current_mode)
                    
                    # Monitor swing setups if in SWING mode
                    if self.current_mode == "SWING":
                        self.monitor_swing_setups()
                    
                    # Log performance summary periodically
                    if len(signals) > 0:
                        self.trading_logger.log_performance_summary(self.current_mode)
                    
                    # Wait before next cycle
                    time.sleep(30)  # 30 seconds cycle
                    
                except KeyboardInterrupt:
                    self.trading_logger.log_trading_alert(
                        "SYSTEM_SHUTDOWN",
                        "System shutdown requested by user",
                        priority="HIGH"
                    )
                    break
                    
                except Exception as e:
                    # Handle any unexpected errors
                    self.error_handler.handle_error(
                        e, "MainLoop", ErrorCategory.SYSTEM_ERROR, 
                        ErrorSeverity.HIGH, context={"mode": self.current_mode}
                    )
                    time.sleep(10)  # Wait before retry
            
            # Cleanup on shutdown
            self.cleanup()
            
        except Exception as e:
            self.error_handler.handle_error(
                e, "MainApp", ErrorCategory.SYSTEM_ERROR, 
                ErrorSeverity.CRITICAL
            )
            sys.exit(1)
    
    def process_signals_for_mode(self, mode: str) -> list:
        """Process signals for specific mode with comprehensive error handling"""
        signals = []
        
        try:
            self.trading_logger.log_trading_alert(
                "PROCESSING",
                f"Processing signals for {mode} mode",
                mode=mode
            )
            
            for pair in self.pairs:
                try:
                    # Get candles with error handling
                    candles = self.error_handler.safe_execute(
                        self.data_manager.get_candles,
                        pair,
                        "15m" if mode == "SCALPING" else "1h",
                        100 if mode == "SCALPING" else 200,
                        component="DataManager",
                        category=ErrorCategory.DATA_ERROR,
                        severity=ErrorSeverity.MEDIUM,
                        pair=pair,
                        mode=mode,
                        context={"timeframe": "15m" if mode == "SCALPING" else "1h"}
                    )
                    
                    if not candles:
                        self.trading_logger.log_trading_alert(
                            "DATA_ERROR",
                            f"No candles for {pair}",
                            pair=pair,
                            mode=mode
                        )
                        continue
                    
                    # Process signal with error handling
                    signal = self.error_handler.safe_execute(
                        self.signal_processor.process_signal,
                        candles, pair, mode,
                        component="SignalProcessor",
                        category=ErrorCategory.PROCESSING_ERROR,
                        severity=ErrorSeverity.MEDIUM,
                        pair=pair,
                        mode=mode
                    )
                    
                    if signal:
                        # Convert to TradingSignal format
                        trading_signal = TradingSignal(
                            pair=signal.pair,
                            direction=signal.direction,
                            entry_price=signal.entry_price,
                            stop_loss=signal.stop_loss,
                            take_profit=signal.take_profit,
                            strength=signal.strength,
                            risk_reward=signal.risk_reward,
                            mode=mode,
                            timestamp=signal.timestamp,
                            pattern=self._get_signal_pattern(signal, mode),
                            volume_ratio=self._get_volume_ratio(candles),
                            rsi=self._get_rsi(candles),
                            trend=self._get_trend(candles)
                        )
                        
                        # Log with Trading Logger
                        self.trading_logger.log_trading_signal(trading_signal)
                        
                        # Send Telegram alert with error handling
                        try:
                            signal_data = {
                                'pair': signal.pair,
                                'direction': signal.direction,
                                'entry_price': signal.entry_price,
                                'stop_loss': signal.stop_loss,
                                'take_profit': signal.take_profit,
                                'strength': signal.strength,
                                'risk_reward': signal.risk_reward,
                                'pattern': self._get_signal_pattern(signal, mode),
                                'mode': mode
                            }
                            self.notification_service.send_signal_alert(signal_data, mode)
                        except Exception as e:
                            self.error_handler.handle_error(
                                e, "TelegramNotification", ErrorCategory.TELEGRAM_ERROR,
                                ErrorSeverity.LOW, pair=pair, mode=mode
                            )
                        
                        signals.append(signal)
                        
                        self.trading_logger.log_trading_alert(
                            "SIGNAL_GENERATED",
                            f"Signal generated for {pair}",
                            pair=pair,
                            mode=mode
                        )
                    
                except Exception as e:
                    self.error_handler.handle_error(
                        e, "PairProcessing", ErrorCategory.PROCESSING_ERROR,
                        ErrorSeverity.MEDIUM, pair=pair, mode=mode
                    )
                    continue
            
            # Log mode summary
            if signals:
                self.trading_logger.log_trading_alert(
                    "SUMMARY",
                    f"Generated {len(signals)} signals for {mode} mode",
                    mode=mode
                )
            else:
                self.trading_logger.log_trading_alert(
                    "SUMMARY",
                    f"No signals generated for {mode} mode",
                    mode=mode
                )
                
        except Exception as e:
            self.error_handler.handle_error(
                e, "SignalProcessing", ErrorCategory.PROCESSING_ERROR,
                ErrorSeverity.HIGH, mode=mode
            )
        
        return signals
    
    def monitor_swing_setups(self):
        """Monitor swing setups with error handling"""
        try:
            active_setups = self.signal_processor.swing_setup_manager.get_active_setups()
            
            if active_setups:
                setup_count = sum(len(setups) for setups in active_setups.values())
                self.trading_logger.log_trading_alert(
                    "SWING_SETUP_MONITOR",
                    f"Monitoring {setup_count} active swing setups",
                    mode="SWING"
                )
                
                # Log setup details
                for pair, setups in active_setups.items():
                    for setup in setups:
                        self.trading_logger.log_trading_alert(
                            "SETUP_STATUS",
                            f"Setup {setup.setup_type} for {pair} - Status: {setup.status}",
                            pair=pair,
                            mode="SWING"
                        )
            else:
                self.trading_logger.log_trading_alert(
                    "SWING_SETUP_MONITOR",
                    "No active swing setups to monitor",
                    mode="SWING"
                )
                
        except Exception as e:
            self.error_handler.handle_error(
                e, "SwingSetupMonitor", ErrorCategory.PROCESSING_ERROR,
                ErrorSeverity.MEDIUM, mode="SWING"
            )
    
    def check_mode_switch(self) -> str:
        """Check for mode switch with error handling"""
        try:
            # Simple time-based mode switching
            current_hour = datetime.now().hour
            
            if 9 <= current_hour < 17:  # 9 AM - 5 PM
                return "SCALPING"
            else:
                return "SWING"
                
        except Exception as e:
            self.error_handler.handle_error(
                e, "ModeSwitch", ErrorCategory.SYSTEM_ERROR,
                ErrorSeverity.LOW
            )
            return self.current_mode  # Keep current mode on error
    
    def cleanup(self):
        """Cleanup resources on shutdown"""
        try:
            self.trading_logger.log_trading_alert(
                "SYSTEM_CLEANUP",
                "Cleaning up system resources",
                priority="HIGH"
            )
            
            # Log final error statistics
            error_stats = self.error_handler.get_error_count()
            self.trading_logger.log_trading_alert(
                "FINAL_STATS",
                f"Final error statistics: {error_stats}",
                priority="MEDIUM"
            )
            
            # Send shutdown notification
            self.notification_service.send_system_alert(
                "SYSTEM_SHUTDOWN",
                "Arif Signal Trading System shutdown completed",
                "HIGH"
            )
            
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
    
    def _get_signal_pattern(self, signal: SignalData, mode: str) -> str:
        """Get signal pattern with error handling"""
        try:
            if mode == "SCALPING":
                return "Sweep/Engulfing"
            else:  # SWING mode
                # Check if it's from swing setup
                active_setups = self.signal_processor.swing_setup_manager.get_active_setups()
                for pair_setups in active_setups.values():
                    for setup in pair_setups:
                        if setup.status == "TRIGGERED":
                            return f"Swing_{setup.setup_type}"
                return "OTL_Breakout"
        except Exception as e:
            self.error_handler.handle_error(
                e, "PatternDetection", ErrorCategory.PROCESSING_ERROR,
                ErrorSeverity.LOW, pair=signal.pair, mode=mode
            )
            return "Unknown"
    
    def _get_volume_ratio(self, candles) -> float:
        """Get volume ratio with error handling"""
        try:
            if len(candles) >= 2:
                current_volume = candles[-1].volume
                avg_volume = sum(c.volume for c in candles[-20:]) / 20
                return current_volume / avg_volume if avg_volume > 0 else 1.0
            return 1.0
        except Exception as e:
            self.error_handler.handle_error(
                e, "VolumeCalculation", ErrorCategory.PROCESSING_ERROR,
                ErrorSeverity.LOW
            )
            return 1.0
    
    def _get_rsi(self, candles) -> float:
        """Get RSI with error handling"""
        try:
            # Simple RSI calculation
            if len(candles) >= 14:
                gains = []
                losses = []
                for i in range(1, len(candles)):
                    change = candles[i].close - candles[i-1].close
                    if change > 0:
                        gains.append(change)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(change))
                
                avg_gain = sum(gains[-14:]) / 14
                avg_loss = sum(losses[-14:]) / 14
                
                if avg_loss == 0:
                    return 100.0
                
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                return rsi
            return 50.0
        except Exception as e:
            self.error_handler.handle_error(
                e, "RSICalculation", ErrorCategory.PROCESSING_ERROR,
                ErrorSeverity.LOW
            )
            return 50.0
    
    def _get_trend(self, candles) -> str:
        """Get trend with error handling"""
        try:
            if len(candles) >= 20:
                sma_20 = sum(c.close for c in candles[-20:]) / 20
                current_price = candles[-1].close
                
                if current_price > sma_20 * 1.01:
                    return "BULLISH"
                elif current_price < sma_20 * 0.99:
                    return "BEARISH"
                else:
                    return "SIDEWAYS"
            return "UNKNOWN"
        except Exception as e:
            self.error_handler.handle_error(
                e, "TrendCalculation", ErrorCategory.PROCESSING_ERROR,
                ErrorSeverity.LOW
            )
            return "UNKNOWN"

if __name__ == "__main__":
    print("🚀 Starting Arif Signal Trading System with Error Handling...")
    app = ArifSignalApp()
    app.run()