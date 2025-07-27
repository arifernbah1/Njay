# main.py

# --- Import classes from other files ---
from data_ws import DataManager
from processor import SignalProcessor
from config import ConfigManager
from trading_logger import TradingLogger, TradingSignal
from notifications import NotificationService
from error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from health_monitor import BotHealthMonitor, ComponentStatus
from models import SignalData, SignalType
from datetime import datetime
import time
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

class ArifSignalApp:
    """Main application class with parallel dual mode execution and health monitoring"""
    
    def __init__(self):
        try:
            self.config = ConfigManager()
            self.pairs = ConfigManager.TIER1_PAIRS
            
            # Both modes active simultaneously
            self.scalping_active = True
            self.swing_active = True
            
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
            
            # Initialize Health Monitor
            self.health_monitor = BotHealthMonitor(self.trading_logger, self.notification_service)
            
            # Initialize components with error handling
            self.data_manager = DataManager(self.trading_logger)
            self.signal_processor = SignalProcessor(self.trading_logger)
            
            # Set notification service for swing setup manager
            self.signal_processor.swing_setup_manager.set_notification_service(self.notification_service)
            
            # Threading control
            self.running = True
            self.scalping_thread = None
            self.swing_thread = None
            
            # Log system startup
            self.trading_logger.log_trading_alert(
                "SYSTEM_START", 
                "Arif Signal Trading System initialized with PARALLEL dual mode execution and health monitoring",
                priority="HIGH"
            )
            
            # Send startup notification to Telegram
            self.notification_service.send_system_alert(
                "SYSTEM_START",
                "Arif Signal Trading System started with PARALLEL SCALPING + SWING modes + Health Monitoring",
                "HIGH"
            )
            
        except Exception as e:
            print(f"Critical error during initialization: {str(e)}")
            sys.exit(1)
    
    def run(self):
        """Main application loop with parallel dual mode execution and health monitoring"""
        try:
            self.trading_logger.log_trading_alert(
                "SYSTEM_RUNNING",
                "Trading system is now running with PARALLEL dual modes and health monitoring",
                priority="HIGH"
            )
            
            # Start both modes in parallel
            self._start_parallel_modes()
            
            # Main monitoring loop
            while self.running:
                try:
                    # Monitor system health
                    self._monitor_system_health()
                    
                    # Check for shutdown signal
                    time.sleep(10)  # Check every 10 seconds
                    
                except KeyboardInterrupt:
                    self.trading_logger.log_trading_alert(
                        "SYSTEM_SHUTDOWN",
                        "System shutdown requested by user",
                        priority="HIGH"
                    )
                    break
                    
                except Exception as e:
                    self.error_handler.handle_error(
                        e, "MainLoop", ErrorCategory.SYSTEM_ERROR, 
                        ErrorSeverity.HIGH
                    )
                    time.sleep(10)
            
            # Cleanup on shutdown
            self.cleanup()
            
        except Exception as e:
            self.error_handler.handle_error(
                e, "MainApp", ErrorCategory.SYSTEM_ERROR, 
                ErrorSeverity.CRITICAL
            )
            sys.exit(1)
    
    def _start_parallel_modes(self):
        """Start both SCALPING and SWING modes in parallel"""
        try:
            self.trading_logger.log_trading_alert(
                "PARALLEL_START",
                "Starting parallel dual mode execution",
                priority="HIGH"
            )
            
            # Start SCALPING mode thread
            self.scalping_thread = threading.Thread(
                target=self._run_scalping_mode,
                name="ScalpingMode",
                daemon=True
            )
            self.scalping_thread.start()
            
            # Start SWING mode thread
            self.swing_thread = threading.Thread(
                target=self._run_swing_mode,
                name="SwingMode",
                daemon=True
            )
            self.swing_thread.start()
            
            self.trading_logger.log_trading_alert(
                "PARALLEL_ACTIVE",
                "Both SCALPING and SWING modes are now running in parallel",
                priority="HIGH"
            )
            
        except Exception as e:
            self.error_handler.handle_error(
                e, "ParallelStart", ErrorCategory.SYSTEM_ERROR,
                ErrorSeverity.CRITICAL
            )
    
    def _run_scalping_mode(self):
        """Run SCALPING mode continuously with health monitoring"""
        self.trading_logger.log_trading_alert(
            "SCALPING_START",
            "SCALPING mode thread started",
            mode="SCALPING",
            priority="HIGH"
        )
        
        # Update health monitor
        self.health_monitor.update_component_status("SCALPING_THREAD", ComponentStatus.RUNNING)
        
        while self.running and self.scalping_active:
            try:
                start_time = time.time()
                
                # Process scalping signals
                signals = self.process_signals_for_mode("SCALPING")
                
                # Update health metrics
                processing_time = (time.time() - start_time) * 1000  # Convert to ms
                self.health_monitor.add_processing_time(processing_time)
                
                # Update signal counters
                for signal in signals:
                    self.health_monitor.increment_signal("SCALPING")
                
                # Log scalping performance
                if signals:
                    self.trading_logger.log_performance_summary("SCALPING")
                
                # Scalping cycle: 15 seconds
                time.sleep(15)
                
            except Exception as e:
                self.health_monitor.increment_error()
                self.health_monitor.update_component_status("SCALPING_THREAD", ComponentStatus.ERROR)
                
                self.error_handler.handle_error(
                    e, "ScalpingMode", ErrorCategory.PROCESSING_ERROR,
                    ErrorSeverity.HIGH, mode="SCALPING"
                )
                time.sleep(10)  # Wait before retry
        
        self.health_monitor.update_component_status("SCALPING_THREAD", ComponentStatus.STOPPED)
        self.trading_logger.log_trading_alert(
            "SCALPING_STOP",
            "SCALPING mode thread stopped",
            mode="SCALPING",
            priority="HIGH"
        )
    
    def _run_swing_mode(self):
        """Run SWING mode continuously with health monitoring"""
        self.trading_logger.log_trading_alert(
            "SWING_START",
            "SWING mode thread started",
            mode="SWING",
            priority="HIGH"
        )
        
        # Update health monitor
        self.health_monitor.update_component_status("SWING_THREAD", ComponentStatus.RUNNING)
        
        while self.running and self.swing_active:
            try:
                start_time = time.time()
                
                # Process swing signals
                signals = self.process_signals_for_mode("SWING")
                
                # Monitor swing setups
                self.monitor_swing_setups()
                
                # Update health metrics
                processing_time = (time.time() - start_time) * 1000  # Convert to ms
                self.health_monitor.add_processing_time(processing_time)
                
                # Update signal counters
                for signal in signals:
                    self.health_monitor.increment_signal("SWING")
                
                # Log swing performance
                if signals:
                    self.trading_logger.log_performance_summary("SWING")
                
                # Swing cycle: 60 seconds
                time.sleep(60)
                
            except Exception as e:
                self.health_monitor.increment_error()
                self.health_monitor.update_component_status("SWING_THREAD", ComponentStatus.ERROR)
                
                self.error_handler.handle_error(
                    e, "SwingMode", ErrorCategory.PROCESSING_ERROR,
                    ErrorSeverity.HIGH, mode="SWING"
                )
                time.sleep(10)  # Wait before retry
        
        self.health_monitor.update_component_status("SWING_THREAD", ComponentStatus.STOPPED)
        self.trading_logger.log_trading_alert(
            "SWING_STOP",
            "SWING mode thread stopped",
            mode="SWING",
            priority="HIGH"
        )
    
    def _monitor_system_health(self):
        """Monitor system health and thread status"""
        try:
            # Check if threads are alive
            scalping_alive = self.scalping_thread and self.scalping_thread.is_alive()
            swing_alive = self.swing_thread and self.swing_thread.is_alive()
            
            # Update health monitor component status
            if scalping_alive:
                self.health_monitor.update_component_status("SCALPING_THREAD", ComponentStatus.RUNNING)
            else:
                self.health_monitor.update_component_status("SCALPING_THREAD", ComponentStatus.ERROR)
            
            if swing_alive:
                self.health_monitor.update_component_status("SWING_THREAD", ComponentStatus.RUNNING)
            else:
                self.health_monitor.update_component_status("SWING_THREAD", ComponentStatus.ERROR)
            
            # Log thread status
            if not scalping_alive and self.scalping_active:
                self.trading_logger.log_trading_alert(
                    "THREAD_DEAD",
                    "SCALPING thread died, attempting restart",
                    mode="SCALPING",
                    priority="HIGH"
                )
                self._restart_scalping_thread()
            
            if not swing_alive and self.swing_active:
                self.trading_logger.log_trading_alert(
                    "THREAD_DEAD",
                    "SWING thread died, attempting restart",
                    mode="SWING",
                    priority="HIGH"
                )
                self._restart_swing_thread()
            
            # Get health status
            health_status = self.health_monitor.get_system_status()
            
            # Log system health
            self.trading_logger.log_trading_alert(
                "SYSTEM_HEALTH",
                f"System health check: {health_status}",
                priority="MEDIUM"
            )
            
        except Exception as e:
            self.error_handler.handle_error(
                e, "SystemHealth", ErrorCategory.SYSTEM_ERROR,
                ErrorSeverity.MEDIUM
            )
    
    def _restart_scalping_thread(self):
        """Restart SCALPING thread"""
        try:
            if self.scalping_thread:
                self.scalping_thread.join(timeout=5)
            
            self.scalping_thread = threading.Thread(
                target=self._run_scalping_mode,
                name="ScalpingMode",
                daemon=True
            )
            self.scalping_thread.start()
            
            self.health_monitor.update_component_status("SCALPING_THREAD", ComponentStatus.RESTARTING)
            
            self.trading_logger.log_trading_alert(
                "THREAD_RESTART",
                "SCALPING thread restarted successfully",
                mode="SCALPING",
                priority="HIGH"
            )
            
        except Exception as e:
            self.error_handler.handle_error(
                e, "ScalpingRestart", ErrorCategory.SYSTEM_ERROR,
                ErrorSeverity.HIGH, mode="SCALPING"
            )
    
    def _restart_swing_thread(self):
        """Restart SWING thread"""
        try:
            if self.swing_thread:
                self.swing_thread.join(timeout=5)
            
            self.swing_thread = threading.Thread(
                target=self._run_swing_mode,
                name="SwingMode",
                daemon=True
            )
            self.swing_thread.start()
            
            self.health_monitor.update_component_status("SWING_THREAD", ComponentStatus.RESTARTING)
            
            self.trading_logger.log_trading_alert(
                "THREAD_RESTART",
                "SWING thread restarted successfully",
                mode="SWING",
                priority="HIGH"
            )
            
        except Exception as e:
            self.error_handler.handle_error(
                e, "SwingRestart", ErrorCategory.SYSTEM_ERROR,
                ErrorSeverity.HIGH, mode="SWING"
            )
    
    def process_signals_for_mode(self, mode: str) -> list:
        """Process signals for specific mode with comprehensive error handling and health monitoring"""
        signals = []
        
        try:
            self.trading_logger.log_trading_alert(
                "PROCESSING",
                f"Processing signals for {mode} mode",
                mode=mode
            )
            
            # Use ThreadPoolExecutor for parallel pair processing
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Submit all pairs for processing
                future_to_pair = {
                    executor.submit(self._process_single_pair, pair, mode): pair 
                    for pair in self.pairs
                }
                
                # Collect results
                for future in as_completed(future_to_pair):
                    pair = future_to_pair[future]
                    try:
                        signal = future.result()
                        if signal:
                            signals.append(signal)
                    except Exception as e:
                        self.health_monitor.increment_error()
                        self.error_handler.handle_error(
                            e, "PairProcessing", ErrorCategory.PROCESSING_ERROR,
                            ErrorSeverity.MEDIUM, pair=pair, mode=mode
                        )
            
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
            self.health_monitor.increment_error()
            self.error_handler.handle_error(
                e, "SignalProcessing", ErrorCategory.PROCESSING_ERROR,
                ErrorSeverity.HIGH, mode=mode
            )
        
        return signals
    
    def _process_single_pair(self, pair: str, mode: str) -> Optional[SignalData]:
        """Process single pair for specific mode with health monitoring"""
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
                return None
            
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
                    self.health_monitor.increment_telegram_sent()
                except Exception as e:
                    self.health_monitor.increment_telegram_failed()
                    self.error_handler.handle_error(
                        e, "TelegramNotification", ErrorCategory.TELEGRAM_ERROR,
                        ErrorSeverity.LOW, pair=pair, mode=mode
                    )
                
                self.trading_logger.log_trading_alert(
                    "SIGNAL_GENERATED",
                    f"Signal generated for {pair}",
                    pair=pair,
                    mode=mode
                )
                
                return signal
            
            return None
            
        except Exception as e:
            self.health_monitor.increment_error()
            self.error_handler.handle_error(
                e, "SinglePairProcessing", ErrorCategory.PROCESSING_ERROR,
                ErrorSeverity.MEDIUM, pair=pair, mode=mode
            )
            return None
    
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
            self.health_monitor.increment_error()
            self.error_handler.handle_error(
                e, "SwingSetupMonitor", ErrorCategory.PROCESSING_ERROR,
                ErrorSeverity.MEDIUM, mode="SWING"
            )
    
    def cleanup(self):
        """Cleanup resources on shutdown"""
        try:
            self.trading_logger.log_trading_alert(
                "SYSTEM_CLEANUP",
                "Cleaning up system resources",
                priority="HIGH"
            )
            
            # Stop both modes
            self.running = False
            self.scalping_active = False
            self.swing_active = False
            
            # Stop health monitoring
            self.health_monitor.stop_monitoring()
            
            # Wait for threads to finish
            if self.scalping_thread:
                self.scalping_thread.join(timeout=10)
            if self.swing_thread:
                self.swing_thread.join(timeout=10)
            
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
                "Arif Signal Trading System shutdown completed (Parallel Dual Mode + Health Monitoring)",
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
    print("🚀 Starting Arif Signal Trading System with PARALLEL Dual Mode + Health Monitoring...")
    print("⚡ SCALPING Mode: Active (15s cycle)")
    print("📈 SWING Mode: Active (60s cycle)")
    print("🔄 Both modes running simultaneously!")
    print("🏥 Health Monitoring: Active (5min cycle)")
    app = ArifSignalApp()
    app.run()